from pathlib import Path

import frontmatter

from blogsmith.config import BlogsmithConfig
from blogsmith.utils import draft_filename, post_filename, slugify, today_iso


def create_draft(
    config: BlogsmithConfig,
    title: str,
    tags: list[str] | None = None,
    excerpt: str = "",
) -> Path:
    config.drafts_path.mkdir(parents=True, exist_ok=True)

    filename = draft_filename(title)
    path = config.drafts_path / filename

    if path.exists():
        raise FileExistsError(f"Draft already exists: {path}")

    post = frontmatter.Post(
        content=f"# {title}\n\nWrite your post here.\n",
        layout="post",
        title=title,
        date=today_iso(),
        tags=tags or [],
        excerpt=excerpt,
        published=False,
    )

    path.write_text(frontmatter.dumps(post), encoding="utf-8")

    return path


def list_markdown_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []

    return sorted(directory.glob("*.md"))


def list_drafts(config: BlogsmithConfig) -> list[Path]:
    return list_markdown_files(config.drafts_path)


def list_posts(config: BlogsmithConfig) -> list[Path]:
    return list_markdown_files(config.posts_path)


def find_draft(config: BlogsmithConfig, slug_or_filename: str) -> Path:
    slug = slug_or_filename.removesuffix(".md")
    path = config.drafts_path / f"{slug}.md"

    if not path.exists():
        raise FileNotFoundError(f"Draft not found: {path}")

    return path


def publish_draft(
    config: BlogsmithConfig,
    slug_or_filename: str,
    publish_date: str | None = None,
) -> tuple[Path, Path]:
    config.posts_path.mkdir(parents=True, exist_ok=True)

    draft_path = find_draft(config, slug_or_filename)
    post = frontmatter.loads(draft_path.read_text(encoding="utf-8"))

    title = post.metadata.get("title")
    if not title:
        raise ValueError(f"Draft is missing a title: {draft_path}")

    date_value = publish_date or today_iso()

    post.metadata["date"] = date_value
    post.metadata["published"] = True

    published_filename = post_filename(title, date_value)
    published_path = config.posts_path / published_filename

    if published_path.exists():
        raise FileExistsError(f"Published post already exists: {published_path}")

    published_path.write_text(frontmatter.dumps(post), encoding="utf-8")
    draft_path.unlink()

    return published_path, draft_path

def find_any_post_file(config: BlogsmithConfig, slug_or_filename: str) -> Path:
    slug = slug_or_filename.removesuffix(".md")

    draft_path = config.drafts_path / f"{slug}.md"
    if draft_path.exists():
        return draft_path

    for post in list_posts(config):
        if post.name.endswith(f"{slug}.md") or post.stem.endswith(slug):
            return post

    raise FileNotFoundError(f"No draft or post found matching: {slug_or_filename}")