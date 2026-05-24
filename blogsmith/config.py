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

    @property
    def posts_path(self) -> Path:
        return self.site_repo_path / self.posts_dir

    @property
    def drafts_path(self) -> Path:
        return self.site_repo_path / self.drafts_dir

    @property
    def assets_path(self) -> Path:
        return self.site_repo_path / self.assets_dir


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
    )


def write_default_config(path: Path = Path(CONFIG_FILE)) -> None:
    if path.exists():
        raise FileExistsError(f"{path} already exists.")

    example = {
        "site_repo_path": str(Path.home() / "Projects" / "BrendanMayer.github.io"),
        "posts_dir": "_posts",
        "drafts_dir": "_drafts",
        "assets_dir": "assets/images/blog",
        "branch": "main",
    }

    path.write_text(json.dumps(example, indent=2), encoding="utf-8")