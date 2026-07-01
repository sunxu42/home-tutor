"""Generate mock TutorContent files from materialized packages."""

from __future__ import annotations

import json
from pathlib import Path

from tutor_templates import build_tutor_content


def write_tutor_files(
    *,
    session_dir: Path,
    session_id: str,
    packages_dir: Path,
) -> dict[str, str]:
    """Write tutor/qNN.json for each package; return question_id -> verdict."""
    tutor_dir = session_dir / "tutor"
    tutor_dir.mkdir(parents=True, exist_ok=True)
    verdicts: dict[str, str] = {}

    for pkg_path in sorted(packages_dir.glob("q*.json")):
        package = json.loads(pkg_path.read_text(encoding="utf-8"))
        question_id = package["question_id"]
        tutor = build_tutor_content(
            session_id=session_id,
            question_id=question_id,
            package=package,
        )
        verdicts[question_id] = tutor["verdict"]
        out = tutor_dir / pkg_path.name
        out.write_text(json.dumps(tutor, ensure_ascii=False, indent=2), encoding="utf-8")

    return verdicts
