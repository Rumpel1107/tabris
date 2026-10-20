import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import openai
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core import deadline, providers
from core.deadline import DeadlineTransport

ANSWER = (b'{"id": "x", "object": "chat.completion", "created": 0, "model": "m", "choices": '
          b'[{"index": 0, "message": {"role": "assistant", "content": "ok"}, "finish_reason": "stop"}]}')


@pytest.fixture
def local_server():
    """Start a local server whose every GET and POST runs `behaviour(handler)`, after the reply's head unless
    `head=False`; return its URL. Stopped after the test."""
    servers = []

    def start(behaviour, head=True):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.rfile.read(int(self.headers.get("Content-Length", 0)))
                if head:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.flush()
                behaviour(self)

            do_POST = do_GET

        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        servers.append(server)
        return f"http://127.0.0.1:{server.server_port}/"

    yield start
    for server in servers:
        server.shutdown()


def trickle(handler, closed_at=None, started=None):
    """A busy server keeping the line open: an empty line every 0.2 s for 5 s, then the answer."""
    try:
        for _ in range(25):
            handler.wfile.write(b"\n")
            handler.wfile.flush()
            time.sleep(0.2)
        handler.wfile.write(ANSWER)
    except (BrokenPipeError, ConnectionResetError):
        if closed_at is not None:
            closed_at.append(time.monotonic() - started)


def silent(handler):
    time.sleep(5)


def sparse_trickle(handler):
    """An empty line every 0.9 s: each arrives just before a 1 s silence would run out."""
    try:
        for _ in range(6):
            handler.wfile.write(b"\n")
            handler.wfile.flush()
            time.sleep(0.9)
    except (BrokenPipeError, ConnectionResetError):
        pass


def head_trickle(handler):
    """The status line, then one byte of a header every 0.2 s: the reply's head itself is held open."""
    try:
        handler.wfile.write(b"HTTP/1.1 200 OK\r\nX-Slow: ")
        for _ in range(25):
            handler.wfile.write(b"a")
            handler.wfile.flush()
            time.sleep(0.2)
    except (BrokenPipeError, ConnectionResetError):
        pass


@pytest.mark.parametrize("behaviour, head", [(trickle, True), (silent, True), (sparse_trickle, True), (head_trickle, False)])
def test_a_call_ends_at_its_timeout_however_the_server_holds_it(local_server, behaviour, head):
    url = local_server(behaviour, head)
    started = time.monotonic()
    with pytest.raises(httpx.TimeoutException):
        httpx.Client(transport=DeadlineTransport()).post(url, timeout=1)
    assert time.monotonic() - started < 1.5


@pytest.mark.parametrize("timeout", [1, None])
def test_a_reply_inside_the_timeout_arrives_whole(local_server, timeout):
    def two_empty_lines_then_the_answer(handler):
        handler.wfile.write(b"\n\n")
        handler.wfile.flush()
        time.sleep(0.2)
        handler.wfile.write(ANSWER)

    url = local_server(two_empty_lines_then_the_answer)
    response = httpx.Client(transport=DeadlineTransport()).post(url, timeout=timeout)
    assert response.json()["choices"][0]["message"]["content"] == "ok"


def test_a_reply_that_arrived_gives_its_connection_back(local_server):
    url = local_server(lambda handler: handler.wfile.write(ANSWER))
    client = httpx.Client(transport=DeadlineTransport(limits=httpx.Limits(max_connections=1)))
    for _ in range(3):
        assert client.post(url, timeout=1).json()["choices"][0]["message"]["content"] == "ok"


def test_a_call_cut_at_its_timeout_gives_its_connection_back(local_server):
    held, answering = local_server(trickle), local_server(lambda handler: handler.wfile.write(ANSWER))
    client = httpx.Client(transport=DeadlineTransport(limits=httpx.Limits(max_connections=1)))
    with pytest.raises(httpx.ReadTimeout):
        client.post(held, timeout=1)
    assert client.post(answering, timeout=1).json()["choices"][0]["message"]["content"] == "ok"


def test_the_connection_is_closed_at_the_timeout(local_server):
    closed_at, started = [], time.monotonic()
    url = local_server(lambda handler: trickle(handler, closed_at, started))
    with pytest.raises(httpx.ReadTimeout):
        httpx.Client(transport=DeadlineTransport()).post(url, timeout=1)
    time.sleep(0.5)   # the server learns of the close on its next write, at most 0.2 s later
    assert closed_at and closed_at[0] < 2


@pytest.mark.parametrize("call", [deadline.get, deadline.post])
def test_nothing_a_site_sets_reaches_the_next_call(local_server, call):
    cookies_received = []

    def set_a_cookie(handler):
        cookies_received.append(handler.headers.get("Cookie"))
        handler.wfile.write(ANSWER)

    def head_with_a_cookie(handler):
        handler.send_response(200)
        handler.send_header("Set-Cookie", "session=user-a; Path=/")
        handler.end_headers()
        set_a_cookie(handler)

    url = local_server(head_with_a_cookie, head=False)
    call(url, timeout=1)
    call(url, timeout=1)
    assert cookies_received == [None, None]


@pytest.mark.parametrize("call", [deadline.get, deadline.post])
def test_the_shared_calls_end_at_their_timeout(local_server, call):
    url = local_server(trickle)
    started = time.monotonic()
    with pytest.raises(httpx.ReadTimeout):
        call(url, timeout=1)
    assert time.monotonic() - started < 1.5


def test_a_tls_handshake_gets_only_what_is_left_and_its_stream_stays_bounded(monkeypatch):
    received = {}

    class PlainStream:
        def start_tls(self, ssl_context, server_hostname=None, timeout=None):
            received["timeout"] = timeout
            return PlainStream()

    monkeypatch.setattr(deadline._current, "deadline", time.monotonic() + 1, raising=False)
    tls = deadline._DeadlineNetworkStream(PlainStream()).start_tls("context", "example.com", timeout=15)
    assert received["timeout"] <= 1
    assert isinstance(tls, deadline._DeadlineNetworkStream)


def test_a_provider_call_held_open_fails_as_the_timeout_the_fallback_chain_handles(local_server, monkeypatch):
    url = local_server(trickle)
    monkeypatch.setitem(providers.PROVIDER_CONFIG["deepseek"], "base_url", url)
    monkeypatch.setitem(providers.PROVIDER_CONFIG["deepseek"], "api_key", "test-key")   # CI runs with no keys
    monkeypatch.setattr(providers, "_clients", {})
    providers._get_client("deepseek").chat.completions   # the SDK imports these on first use, once a process: not the call
    started = time.monotonic()
    with pytest.raises(openai.APITimeoutError):
        providers._call_provider("deepseek", "deepseek-chat", [{"role": "user", "content": "hola"}], timeout=1)
    assert time.monotonic() - started < 1.5
