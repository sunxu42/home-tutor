"""Declarative answer sheets calibrated to target exam scores."""

from __future__ import annotations

# Wrong-answer variants used across profiles.
_WRONG: dict[str, str] = {
    "q01": "210",
    "q03": "45；67.5",
    "q06": "21",
    "q08": "√",
    "q11": "√",
    "q12": "C",
    "q14": "B",
    "q15": "A",
    "q17": "A",
    "q18": "C",
    "q20": "① 3.3  ② 1/48  ③ 55  ④ 1/4",
    "q21": "3:4；5:9；1:2；2:3",
    "q22": "10cm²",
    "q24": "9.42cm²",
    "q26": "秦7500；汉7500",
    "q28": "① 6500m²  ② 400m  ③ 3.14m",
    "q30": "总人数300；B20% D30%",
}

_CORRECT: dict[str, str] = {
    "q01": "180",
    "q02": "30；24",
    "q03": "36；72",
    "q04": "6；18.84；28.26",
    "q05": "425；400",
    "q06": "25",
    "q07": "×",
    "q08": "×",
    "q09": "√",
    "q10": "×",
    "q11": "×",
    "q12": "B",
    "q13": "B",
    "q14": "D",
    "q15": "B",
    "q16": "A",
    "q17": "C",
    "q18": "A",
    "q19": "25.5；8；0.04；1/16；0.75；28.26；3；6:5",
    "q20": "① 4  ② -13/24  ③ 63  ④ 1/8",
    "q21": "3:4；5:9；5:12；3:2",
    "q22": "12.5cm²",
    "q23": "（路线图完成）",
    "q24": "12.56cm²",
    "q25": "2/5吨；5/36吨",
    "q26": "秦朝5000km；汉朝10000km",
    "q27": "24件",
    "q28": "① 6962.5m²  ② 357m  ③ 7.536m",
    "q29": "60%",
    "q30": "B15% D35% 共400人",
}

# Questions marked wrong in each base tier (must sum to 100 - target_score points).
_WEAK_WRONG = frozenset(
    {
        "q01",
        "q03",
        "q06",
        "q08",
        "q11",
        "q12",
        "q14",
        "q15",
        "q17",
        "q20",
        "q21",
        "q22",
        "q24",
        "q26",
        "q28",
        "q30",
    }
)

_MEDIUM_WRONG = frozenset({"q06", "q11", "q14", "q18", "q20", "q21", "q28"})

_STRONG_WRONG = frozenset({"q17", "q20", "q28", "q30"})


def _sheet_from_wrong_set(wrong_ids: frozenset[str]) -> dict[str, str]:
    sheet: dict[str, str] = {}
    for question_id, answer in _CORRECT.items():
        sheet[question_id] = _WRONG.get(question_id, answer) if question_id in wrong_ids else answer
    return sheet


def build_sheet(base: str, delta: dict[str, str]) -> dict[str, str]:
    """Build a full answer sheet from base tier and per-profile overrides."""
    if base == "weak":
        sheet = _sheet_from_wrong_set(_WEAK_WRONG)
    elif base == "medium":
        sheet = _sheet_from_wrong_set(_MEDIUM_WRONG)
    else:
        sheet = _sheet_from_wrong_set(_STRONG_WRONG)

    for question_id, answer in delta.items():
        sheet[question_id] = answer
    return sheet


# Medium-tier wrong answers that differ from the generic _WRONG set.
_MEDIUM_SHEET = _sheet_from_wrong_set(_MEDIUM_WRONG)
_MEDIUM_SHEET.update(
    {
        "q06": "19",
        "q11": "√",
        "q14": "C",
        "q18": "B",
        "q20": "① 4  ② -13/24  ③ 58  ④ 1/8",
        "q21": "3:4；5:9；5:12；4:3",
        "q23": "（路线图已画，比例略不准）",
        "q28": "① 6962.5m²  ② 357m  ③ 7.5m",
    }
)

_STRONG_SHEET = _sheet_from_wrong_set(_STRONG_WRONG)
_STRONG_SHEET.update(
    {
        "q17": "A",
        "q20": "① 4  ② -13/24  ③ 63  ④ 3/16",
        "q28": "① 6962.5m²  ② 357m  ③ 7.54m",
        "q30": "B15% D34% 共400人",
    }
)

_WEAK_SHEET = _sheet_from_wrong_set(_WEAK_WRONG)
_WEAK_SHEET.update(
    {
        "q02": "30；36",
        "q05": "425；500",
        "q19": "25.5；8；0.4；1；0.75；28.26；3；3:5",
        "q23": "（西向线段已画，偏角未标）",
        "q25": "2/5吨；1/4吨",
    }
)

_BASE_SHEETS = {
    "weak": _WEAK_SHEET,
    "medium": _MEDIUM_SHEET,
    "strong": _STRONG_SHEET,
}
