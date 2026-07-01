"""Regenerate OCR monoliths and split session fixture directories."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

_SERVER_DIR = Path(__file__).resolve().parents[2]
_FIXTURES_DIR = Path(__file__).resolve().parent


def main() -> None:
    commands = [
        [sys.executable, str(_FIXTURES_DIR / "mock_ocr_session_builder.py")],
        [sys.executable, str(_FIXTURES_DIR / "split_ocr_session_fixture.py"), "--all"],
    ]
    for cmd in commands:
        print("Running", " ".join(cmd))
        subprocess.run(cmd, check=True, cwd=_SERVER_DIR)

    sessions_dir = _FIXTURES_DIR / "sessions"
    for legacy in ("score50", "score70", "score90"):
        legacy_path = sessions_dir / legacy
        if legacy_path.exists():
            shutil.rmtree(legacy_path)
            print(f"Removed legacy {legacy_path}")


if __name__ == "__main__":
    main()
