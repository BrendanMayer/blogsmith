from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from platformdirs import user_config_dir

APP_NAME = "Blogsmith"


@dataclass
class AppSettings:
    site_repo_path: str = ""
    posts_dir: str = "_posts"
    drafts_dir: str = "_drafts"
    assets_dir: str = "assets/images/blog"
    branch: str = "main"
    remote_name: str = "origin"
    auto_push: bool = True
    git_author_name: str = ""
    git_author_email: str = ""


def settings_dir() -> Path:
    path = Path(user_config_dir(APP_NAME))
    path.mkdir(parents=True, exist_ok=True)
    return path


def settings_path() -> Path:
    return settings_dir() / "config.json"


def load_settings() -> AppSettings:
    path = settings_path()

    if not path.exists():
        return AppSettings()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        defaults = asdict(AppSettings())
        return AppSettings(**{**defaults, **data})
    except Exception:
        return AppSettings()


def save_settings(settings: AppSettings) -> None:
    path = settings_path()
    path.write_text(
        json.dumps(asdict(settings), indent=2),
        encoding="utf-8",
    )


def is_configured(settings: AppSettings) -> bool:
    if not settings.site_repo_path:
        return False

    repo = Path(settings.site_repo_path).expanduser()

    return repo.exists() and (repo / ".git").exists()