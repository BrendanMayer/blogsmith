import os
import subprocess
from pathlib import Path


def open_in_editor(path: Path) -> None:
    editor = os.environ.get("EDITOR")

    if editor:
        subprocess.run([editor, str(path)], check=True)
        return

    if os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
        return

    if os.uname().sysname == "Darwin":
        subprocess.run(["open", str(path)], check=True)
        return

    subprocess.run(["xdg-open", str(path)], check=True)