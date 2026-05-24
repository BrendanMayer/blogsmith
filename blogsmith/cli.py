import argparse
from pathlib import Path

from blogsmith.config import write_default_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blogsmith",
        description="Create and publish Jekyll blog posts."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create a local Blogsmith config file.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init":
        write_default_config(Path("config.local.json"))
        print("Created config.local.json")