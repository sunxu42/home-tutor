"""Integration tests for split session fixtures."""

import json
from pathlib import Path


def test_score53_fixture_layout() -> None:
    root = Path(__file__).resolve().parent / "fixtures" / "sessions" / "score53"
    assert (root / "meta.json").exists()
    assert (root / "events.jsonl").exists()
    assert (root / "timeline-index.json").exists()
    assert len(list((root / "packages").glob("q*.json"))) == 30
    meta = json.loads((root / "meta.json").read_text(encoding="utf-8"))
    assert meta["schema_version"] == "home-tutor.session-meta.v1"
    assert len(meta["questions"]) == 30
