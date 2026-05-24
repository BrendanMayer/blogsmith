from pathlib import Path

import frontmatter

from blogsmith.config import BlogsmithConfig
from blogsmith.utils import draft_filename, today_iso


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