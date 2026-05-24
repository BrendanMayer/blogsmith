import argparse
from pathlib import Path

from blogsmith.config import load_config, write_default_config
from blogsmith.posts import create_draft


def parse_tags(tags: str | None) -> list[str]:
    if not tags:
        return []

    return [tag.strip() for tag in tags.split(",") if tag.strip()]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="blogsmith",
        description="Create and publish Jekyll blog posts."
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("init", help="Create a local Blogsmith config file.")

    new_parser = subparsers.add_parser("new", help="Create a new blog draft.")
    new_parser.add_argument("title", help="The title of the blog post.")
    new_parser.add_argument("--tags", help="Comma-separated tags.")
    new_parser.add_argument("--excerpt", default="", help="Short post summary.")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "init":
        write_default_config(Path("config.local.json"))
        print("Created config.local.json")
        return

    config = load_config()

    if args.command == "new":
        path = create_draft(
            config=config,
            title=args.title,
            tags=parse_tags(args.tags),
            excerpt=args.excerpt,
        )
        print(f"Created draft: {path}")