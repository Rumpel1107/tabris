import argparse
import config
import logging

from core.account import export_user


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.admin",
        description="Operator tools. These act on the real database and are never reachable from a chat.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    export_command = commands.add_parser("export", help="Write everything stored about one user to a JSON file.")
    export_command.add_argument("user_id", type=int, help="Numeric id of the user")

    return parser


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "export":
        print(f"Written: {export_user(config.DB_PATH, args.user_id)}")


if __name__ == "__main__":
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    main()
