import argparse
from pathlib import Path

from blogsmith.config import load_config, write_default_config
from blogsmith.git_service import (
    commit_and_push,
    ensure_clean_working_tree,
    latest_commit,
    remote_url,
    validate_git_repo,
    working_tree_status,
    current_branch,
)
from blogsmith.editor import open_in_editor
from blogsmith.posts import (
    create_draft,
    find_any_post_file,
    list_drafts,
    list_posts,
    publish_draft,
)
from blogsmith.preview import open_preview
from blogsmith.validation import validate_post_file
from blogsmith.images import import_image


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
    
    subparsers.add_parser("status", help="Show linked site repository status.")

    new_parser = subparsers.add_parser("new", help="Create a new blog draft.")
    new_parser.add_argument("title", help="The title of the blog post.")
    new_parser.add_argument("--tags", help="Comma-separated tags.")
    new_parser.add_argument("--excerpt", default="", help="Short post summary.")

    subparsers.add_parser("list", help="List drafts and published posts.")

    publish_parser = subparsers.add_parser("publish", help="Publish a draft.")
    publish_parser.add_argument("slug", help="Draft slug or filename.")
    publish_parser.add_argument("--date", help="Publish date in YYYY-MM-DD format.")
    publish_parser.add_argument(
        "--push",
        action="store_true",
        help="Commit and push the published post."
    )
    publish_parser.add_argument(
        "--message",
        help="Custom Git commit message when using --push."
    )
    
    edit_parser = subparsers.add_parser("edit", help="Open a draft or post in your editor.")
    edit_parser.add_argument("slug", help="Draft/post slug or filename.")
    
    preview_parser = subparsers.add_parser("preview", help="Preview a draft or post in the browser.")
    preview_parser.add_argument("slug", help="Draft/post slug or filename.")
    
    validate_parser = subparsers.add_parser("validate", help="Validate a draft or post.")
    validate_parser.add_argument("slug", help="Draft/post slug or filename.")
    
    image_parser = subparsers.add_parser("image", help="Import an image for a post.")
    image_parser.add_argument("slug", help="Post slug.")
    image_parser.add_argument("image_path", help="Path to the image.")
    image_parser.add_argument("--alt", default="", help="Image alt text.")
    
    

    return parser


def print_files(label: str, files: list[Path]) -> None:
    print(f"\n{label}")

    if not files:
        print("  None")
        return

    for file in files:
        print(f"  - {file.name}")


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

    elif args.command == "list":
        print_files("Drafts", list_drafts(config))
        print_files("Published Posts", list_posts(config))

    elif args.command == "publish":
        validate_git_repo(config.site_repo_path, config.branch)

        if args.push:
            ensure_clean_working_tree(config.site_repo_path)

        path = publish_draft(
            config=config,
            slug_or_filename=args.slug,
            publish_date=args.date,
        )
        
        errors = validate_post_file(path)
        if errors:
            print(f"Published file failed validation: {path}")
            for error in errors:
                print(f"  - {error}")
            raise SystemExit(1)

        print(f"Published post: {path}")

        if args.push:
            commit_message = args.message or f"Add blog post: {path.stem}"

            commit_and_push(
                repo_path=config.site_repo_path,
                files=[path],
                message=commit_message,
            )
            print("Committed and pushed post.")
    
    elif args.command == "edit":
        path = find_any_post_file(config, args.slug)
        open_in_editor(path)
        print(f"Opened: {path}")
        
    elif args.command == "preview":
        path = find_any_post_file(config, args.slug)
        preview_path = open_preview(path)
        print(f"Opened preview: {preview_path}")
        
    elif args.command == "validate":
        path = find_any_post_file(config, args.slug)
        errors = validate_post_file(path)

        if errors:
            print(f"Validation failed: {path}")
            for error in errors:
                print(f"  - {error}")
            raise SystemExit(1)

        print(f"Validation passed: {path}")
        
    elif args.command == "status":
        validate_git_repo(config.site_repo_path, config.branch)

        print(f"Site repo: {config.site_repo_path}")
        print(f"Branch: {current_branch(config.site_repo_path)}")
        print(f"Remote: {remote_url(config.site_repo_path)}")
        print(f"Latest commit: {latest_commit(config.site_repo_path)}")

        status = working_tree_status(config.site_repo_path)
        if status:
            print("\nUncommitted changes:")
            print(status)
        else:
            print("\nWorking tree clean.")
    
    elif args.command == "image":
        image_path, markdown = import_image(
            config=config,
            post_slug=args.slug,
            source_image=Path(args.image_path),
            alt_text=args.alt,
        )

        print(f"Imported image: {image_path}")
        print("\nMarkdown:")
        print(markdown)