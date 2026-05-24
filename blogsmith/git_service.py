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


def ensure_clean_working_tree(repo_path: Path) -> None:
    status = working_tree_status(repo_path)

    if status:
        raise ValueError(
            "Portfolio repo has uncommitted changes. "
            "Commit, stash, or discard them before publishing."
        )


def commit_and_push(repo_path: Path, files: list[Path], message: str) -> None:
    repo_root = repo_path.resolve()

    relative_files = [
        str(file.resolve().relative_to(repo_root))
        for file in files
    ]

    run_git(["add", *relative_files], repo_path)
    run_git(["commit", "-m", message], repo_path)
    run_git(["push"], repo_path)
    
def remote_url(repo_path: Path) -> str:
    return run_git(["remote", "get-url", "origin"], repo_path)


def latest_commit(repo_path: Path) -> str:
    return run_git(["log", "-1", "--oneline"], repo_path)