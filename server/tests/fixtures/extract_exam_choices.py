"""从原卷 docx 校验 / 打印选择题选项（开发用）。

用法:
    cd server
    python tests/fixtures/extract_exam_choices.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

_FIXTURES_DIR = Path(__file__).resolve().parent
_ASSETS_DIR = _FIXTURES_DIR.parent / "assets"
_DOCX_NAME = "人教版2025-2026学年小学六年级数学上册期末测试卷.docx"

if str(_FIXTURES_DIR) not in sys.path:
    sys.path.insert(0, str(_FIXTURES_DIR))

from exam_g6_final_2025 import ChoiceOption  # noqa: E402
from exam_mcq_choices import MCQ_CHOICES  # noqa: E402


def _docx_path() -> Path:
    path = _ASSETS_DIR / _DOCX_NAME
    if not path.is_file():
        msg = f"原卷未找到: {path}\n请将 docx 放入 server/tests/assets/"
        raise FileNotFoundError(msg)
    return path


def _parse_option_line(line: str) -> list[tuple[str, str]]:
    """解析 'A．… B．…' 合并行或单行选项。"""
    pattern = re.compile(r"([A-D])[．.]\s*([^A-D．.]+?)(?=\s+[A-D][．.]|$)")
    return [(m.group(1), m.group(2).strip()) for m in pattern.finditer(line)]


def extract_from_docx() -> dict[str, list[tuple[str, str]]]:
    from docx import Document

    doc = Document(_docx_path())
    paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    result: dict[str, list[tuple[str, str]]] = {}
    current_qid: str | None = None

    for text in paras:
        stem_match = re.match(r"^(\d{1,2})[．.]", text)
        if stem_match:
            num = int(stem_match.group(1))
            if 12 <= num <= 18:
                current_qid = f"q{num:02d}"
                result[current_qid] = []
            elif num > 18:
                current_qid = None
            continue

        if current_qid and re.match(r"^[A-D][．.]", text):
            result[current_qid].extend(_parse_option_line(text))

    return result


def main() -> None:
    docx_choices = extract_from_docx()
    mismatches: list[str] = []

    for qid, expected_raw in MCQ_CHOICES.items():
        expected = [ChoiceOption(key, text) for key, text in expected_raw]
        parsed = docx_choices.get(qid, [])
        exp_keys = [c.key for c in expected]
        par_keys = [k for k, _ in parsed]
        if par_keys != exp_keys:
            mismatches.append(f"{qid}: docx keys {par_keys} vs fixture {exp_keys}")
            continue
        for (pkey, ptext), choice in zip(parsed, expected, strict=True):
            if pkey != choice.key:
                mismatches.append(f"{qid} key mismatch {pkey} vs {choice.key}")
            elif ptext != choice.text and "÷" not in choice.text:
                mismatches.append(f"{qid}{pkey}: docx={ptext!r} fixture={choice.text!r}")

    if mismatches:
        print("校验差异（含 docx 公式丢失导致的预期差异）:")
        for line in mismatches:
            print(" ", line)
    else:
        print("全部 7 道选择题选项与 fixture 一致。")

    print("\n当前 fixture 选项:")
    for qid, choices_raw in MCQ_CHOICES.items():
        print(f"  {qid}:")
        for key, text in choices_raw:
            print(f"    {key}. {text}")


if __name__ == "__main__":
    main()
