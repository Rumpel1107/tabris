import argparse
import config
import logging

from core.account import deactivate_account, export_user
from core.db import get_user_records


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.admin",
        description="Operator tools. These act on the real database and are never reachable from a chat.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    export_command = commands.add_parser("export", help="Write everything stored about one user to a JSON file.")
    export_command.add_argument("user_id", type=int, help="Numeric id of the user")

    deactivate_command = commands.add_parser("deactivate", help="Export a user's data, then stop their account from conversing.")
    deactivate_command.add_argument("user_id", type=int, help="Numeric id of the user")

    return parser


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)
    if args.command == "export":
        print(f"Written: {export_user(config.DB_PATH, args.user_id)}")
    elif args.command == "deactivate":
        records = get_user_records(config.DB_PATH, args.user_id)
        user = records["user"]
        print(f"About to deactivate user {args.user_id}: {user['name']}")
        print(f"  Location: {user['location'] or '(none)'}")
        print(f"  Channels: {', '.join(records['channels']) or '(none)'}")
        print(f"  Facts: {len(records['facts'])}")
        print(f"  Messages: {len(records['messages'])}")
        confirmation = input(f"Type the name exactly ({user['name']}) to confirm: ")
        if confirmation != user["name"]:
            print("Confirmation did not match. Nothing was changed.")
            return
        path = deactivate_account(config.DB_PATH, args.user_id)
        print(f"Deactivated. Export written to {path}")


if __name__ == "__main__":
    logging.basicConfig(
        level=config.LOG_LEVEL,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    )
    main()
