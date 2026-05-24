from pathlib import Path

import frontmatter


REQUIRED_FIELDS = [
    "layout",
    "title",
    "date",
    "tags",
    "excerpt",
]


def validate_post_file(path: Path) -> list[str]:
    errors: list[str] = []

    if not path.exists():
        return [f"File does not exist: {path}"]

    try:
        post = frontmatter.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return [f"Could not parse front matter: {exc}"]

    for field in REQUIRED_FIELDS:
        if field not in post.metadata:
            errors.append(f"Missing required field: {field}")

    if post.metadata.get("layout") != "post":
        errors.append("layout should be 'post'.")

    title = post.metadata.get("title")
    if not isinstance(title, str) or not title.strip():
        errors.append("title must be a non-empty string.")

    tags = post.metadata.get("tags")
    if not isinstance(tags, list):
        errors.append("tags must be a list.")

    excerpt = post.metadata.get("excerpt")
    if not isinstance(excerpt, str):
        errors.append("excerpt must be a string.")

    if not post.content.strip():
        errors.append("Post content is empty.")

    return errors