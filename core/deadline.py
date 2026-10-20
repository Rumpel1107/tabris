import threading
import time

import httpcore
import httpx

_current = threading.local()


def _remaining(timeout: float | None, expired: type[Exception]) -> float | None:
    """The smaller of a step's own timeout and what is left of its call's; once the call's has run out, the step fails."""
    deadline = getattr(_current, "deadline", None)
    if deadline is None:
        return timeout
    left = deadline - time.monotonic()
    if left <= 0:
        raise expired("the call ran past its timeout")
    return left if timeout is None else min(timeout, left)


class _DeadlineNetworkStream(httpcore.NetworkStream):
    def __init__(self, stream: httpcore.NetworkStream):
        self._stream = stream

    def read(self, max_bytes: int, timeout: float | None = None) -> bytes:
        return self._stream.read(max_bytes, _remaining(timeout, httpcore.ReadTimeout))

    def write(self, buffer: bytes, timeout: float | None = None) -> None:
        self._stream.write(buffer, _remaining(timeout, httpcore.WriteTimeout))

    def close(self) -> None:
        self._stream.close()

    def start_tls(self, ssl_context, server_hostname=None, timeout=None) -> httpcore.NetworkStream:
        timeout = _remaining(timeout, httpcore.ConnectTimeout)
        return _DeadlineNetworkStream(self._stream.start_tls(ssl_context, server_hostname, timeout))

    def get_extra_info(self, info: str):
        return self._stream.get_extra_info(info)


class _DeadlineBackend(httpcore.NetworkBackend):
    def __init__(self, backend: httpcore.NetworkBackend):
        self._backend = backend

    def connect_tcp(self, host, port, timeout=None, local_address=None, socket_options=None) -> httpcore.NetworkStream:
        timeout = _remaining(timeout, httpcore.ConnectTimeout)
        return _DeadlineNetworkStream(self._backend.connect_tcp(host, port, timeout, local_address, socket_options))

    def connect_unix_socket(self, path, timeout=None, socket_options=None) -> httpcore.NetworkStream:
        timeout = _remaining(timeout, httpcore.ConnectTimeout)
        return _DeadlineNetworkStream(self._backend.connect_unix_socket(path, timeout, socket_options))

    def sleep(self, seconds: float) -> None:
        self._backend.sleep(seconds)


class DeadlineTransport(httpx.HTTPTransport):
    """Bound a whole call by its read timeout. httpx bounds each silence, and a busy server's empty line every few seconds resets it."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # every connect, read and write of a call gets only what is left of it; a private hook of the pinned httpcore
        self._pool._network_backend = _DeadlineBackend(self._pool._network_backend)

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        read = (request.extensions.get("timeout") or {}).get("read")
        _current.deadline = None if read is None else time.monotonic() + read
        return super().handle_request(request)


def get(url: str, **kwargs) -> httpx.Response:
    """`httpx.get`, with its timeout bounding the whole call (DEF-19): a client of its own, so no cookie outlives the call."""
    with httpx.Client(transport=DeadlineTransport()) as client:
        return client.get(url, **kwargs)


def post(url: str, **kwargs) -> httpx.Response:
    """`httpx.post`, with its timeout bounding the whole call (DEF-19): a client of its own, so no cookie outlives the call."""
    with httpx.Client(transport=DeadlineTransport()) as client:
        return client.post(url, **kwargs)
