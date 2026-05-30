from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

CONFIG_FILE = "config.local.json"


@dataclass
class BlogsmithConfig:
    site_repo_path: Path
    posts_dir: str = "_posts"
    drafts_dir: str = "_drafts"
    assets_dir: str = "assets/images/blog"
    branch: str = "main"
    remote_name: str = "origin"

    @property
    def posts_path(self) -> Path:
        return self.site_repo_path / self.posts_dir

    @property
    def drafts_path(self) -> Path:
        return self.site_repo_path / self.drafts_dir

    @property
    def assets_path(self) -> Path:
        return self.site_repo_path / self.assets_dir

    @classmethod
    def from_settings(cls, settings: object) -> "BlogsmithConfig":
        return cls(
            site_repo_path=Path(settings.site_repo_path).expanduser().resolve(),
            posts_dir=settings.posts_dir,
            drafts_dir=settings.drafts_dir,
            assets_dir=settings.assets_dir,
            branch=settings.branch,
            remote_name=settings.remote_name,
        )


def load_config(config_path: Path | None = None) -> BlogsmithConfig:
    path = config_path or Path(CONFIG_FILE)

    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Create it from config.example.json."
        )

    data = json.loads(path.read_text(encoding="utf-8"))

    return BlogsmithConfig(
        site_repo_path=Path(data["site_repo_path"]).expanduser().resolve(),
        posts_dir=data.get("posts_dir", "_posts"),
        drafts_dir=data.get("drafts_dir", "_drafts"),
        assets_dir=data.get("assets_dir", "assets/images/blog"),
        branch=data.get("branch", "main"),
        remote_name=data.get("remote_name", "origin"),
    )


def write_default_config(path: Path = Path(CONFIG_FILE)) -> None:
    if path.exists():
        raise FileExistsError(f"{path} already exists.")

    example = {
        "site_repo_path": str(Path.home() / "Projects" / "your-portfolio"),
        "posts_dir": "_posts",
        "drafts_dir": "_drafts",
        "assets_dir": "assets/images/blog",
        "branch": "main",
        "remote_name": "origin",
    }

    path.write_text(json.dumps(example, indent=2), encoding="utf-8")