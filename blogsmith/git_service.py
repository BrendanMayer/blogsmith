import subprocess
from pathlib import Path


def run_git(args: list[str], cwd: Path) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
    )

    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(message)

    return result.stdout.strip()


def current_branch(repo_path: Path) -> str:
    return run_git(["branch", "--show-current"], repo_path)


def working_tree_status(repo_path: Path) -> str:
    return run_git(["status", "--porcelain"], repo_path)


def validate_git_repo(repo_path: Path, expected_branch: str) -> None:
    if not (repo_path / ".git").exists():
        raise ValueError(f"Not a Git repository: {repo_path}")

    branch = current_branch(repo_path)

    if branch != expected_branch:
        raise ValueError(
            f"Expected branch '{expected_branch}', but current branch is '{branch}'."
        )


def commit_and_push(repo_path: Path, files: list[Path], message: str) -> None:
    relative_files = [
        str(file.resolve().relative_to(repo_path.resolve()))
        for file in files
    ]

    run_git(["add", *relative_files], repo_path)
    run_git(["commit", "-m", message], repo_path)
    run_git(["push"], repo_path)