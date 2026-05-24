import re
from datetime import date


def slugify(title: str) -> str:
    slug = title.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")

    if not slug:
        raise ValueError("Title must contain at least one letter or number.")

    return slug


def today_iso() -> str:
    return date.today().isoformat()


def post_filename(title: str, publish_date: str | None = None) -> str:
    date_part = publish_date or today_iso()
    return f"{date_part}-{slugify(title)}.md"


def draft_filename(title: str) -> str:
    return f"{slugify(title)}.md"