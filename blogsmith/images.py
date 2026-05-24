import shutil
from pathlib import Path

from blogsmith.config import BlogsmithConfig


ALLOWED_IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
}


def import_image(
    config: BlogsmithConfig,
    post_slug: str,
    source_image: Path,
    alt_text: str,
) -> tuple[Path, str]:
    if not source_image.exists():
        raise FileNotFoundError(f"Image not found: {source_image}")

    extension = source_image.suffix.lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError(f"Unsupported image type: {extension}")

    safe_slug = post_slug.removesuffix(".md")
    target_dir = config.assets_path / safe_slug
    target_dir.mkdir(parents=True, exist_ok=True)

    target_path = target_dir / source_image.name

    if target_path.exists():
        raise FileExistsError(f"Image already exists: {target_path}")

    shutil.copy2(source_image, target_path)

    relative_path = target_path.relative_to(config.site_repo_path).as_posix()
    markdown = f"![{alt_text}](/{relative_path})"

    return target_path, markdown