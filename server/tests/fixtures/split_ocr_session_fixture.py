"""Split monolithic ocr-session JSON into session directory layout."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path
from typing import Any

_FIXTURES_DIR = Path(__file__).resolve().parent
if str(_FIXTURES_DIR) not in sys.path:
    sys.path.insert(0, str(_FIXTURES_DIR))

from generate_tutor_mock import write_tutor_files
from profile_factory import ALL_PROFILES, PROFILE_BY_ID

from home_tutor.services.analysis.materializer import (
    build_question_package,
    build_timeline_index,
)


def _question_number_map(questions: list[dict[str, Any]]) -> dict[str, int]:
    return {q["question_id"]: idx + 1 for idx, q in enumerate(questions)}


def split_session(monolith: dict[str, Any], out_dir: Path, *, profile_id: str) -> None:
    """Write meta, events.jsonl, frames, packages; tutor written in second pass."""
    profile = PROFILE_BY_ID[profile_id]
    session_id = monolith["session_id"]
    questions_raw = monolith["questions"]
    number_map = _question_number_map(questions_raw)
    events = monolith["events"]

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    packages_dir = out_dir / "packages"
    packages_dir.mkdir(parents=True, exist_ok=True)

    meta_questions = [
        {
            "question_id": q["question_id"],
            "page_id": q["page_id"],
            "index_on_page": q["index_on_page"],
            "number": number_map[q["question_id"]],
        }
        for q in questions_raw
    ]

    meta = {
        "schema_version": "home-tutor.session-meta.v1",
        "session_id": session_id,
        "grade_level": monolith.get("grade_level", "primary"),
        "subject": monolith.get("subject", "math"),
        "started_at": monolith["started_at"],
        "ended_at": monolith["ended_at"],
        "accuracy_percent": profile.accuracy_percent,
        "pages": monolith.get("pages", []),
        "questions": meta_questions,
        "status": "complete",
        "metadata": {
            "data_source": "mock",
            "exam_title": "六年级数学上册期末测试卷",
            "student_label": profile.label,
            "student_profile": profile.profile_id,
            "target_score": profile.target_score,
            "earned_score": profile.earned_score,
            "duration_minutes": round(profile.duration_ms / 60_000, 1),
        },
    }
    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    with (out_dir / "events.jsonl").open("w", encoding="utf-8") as f:
        for evt in sorted(events, key=lambda e: e["t_offset_ms"]):
            f.write(json.dumps(evt, ensure_ascii=False) + "\n")

    frames_doc = {"frames": monolith.get("frames", [])}
    (out_dir / "frames.json").write_text(
        json.dumps(frames_doc, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    regions = monolith.get("regions", [])
    for q in questions_raw:
        qid = q["question_id"]
        enriched = {
            **q,
            "number": number_map[qid],
        }
        pkg = build_question_package(
            session_id=session_id,
            question=enriched,
            regions=regions,
            events=events,
            grade_level=monolith.get("grade_level", "primary"),
            subject=monolith.get("subject", "math"),
        )
        (packages_dir / f"{qid}.json").write_text(
            json.dumps(pkg, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    verdicts = write_tutor_files(
        session_dir=out_dir,
        session_id=session_id,
        packages_dir=packages_dir,
    )

    timeline = build_timeline_index(
        session_id=session_id,
        events=events,
        question_numbers=number_map,
        verdicts=verdicts,
    )
    (out_dir / "timeline-index.json").write_text(
        json.dumps(timeline, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Split monolithic OCR session fixtures")
    parser.add_argument("--profile", help="Profile id, e.g. score53")
    parser.add_argument("--all", action="store_true")
    args = parser.parse_args()

    if args.all:
        profiles = [profile.profile_id for profile in ALL_PROFILES]
    elif args.profile:
        profiles = [args.profile]
    else:
        parser.error("Specify --profile or --all")

    ocr_dir = _FIXTURES_DIR / "ocr-sessions"
    sessions_dir = _FIXTURES_DIR / "sessions"

    for profile_id in profiles:
        src = ocr_dir / f"g6-math-final-{profile_id}.json"
        dest = sessions_dir / profile_id
        monolith = json.loads(src.read_text(encoding="utf-8"))
        split_session(monolith, dest, profile_id=profile_id)
        print(f"Wrote {dest}")


if __name__ == "__main__":
    main()
