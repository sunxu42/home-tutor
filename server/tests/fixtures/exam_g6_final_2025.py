"""六年级数学期末试卷题目定义与三档学生作答画像。

试卷来源：server/tests/assets/人教版2025-2026学年小学六年级数学上册期末测试卷.docx
满分 100 分，考试时长 60 分钟。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Difficulty = Literal["easy", "medium", "hard"]
QuestionType = Literal[
    "fill_blank", "multiple_choice", "calculation", "word_problem", "unknown"
]


@dataclass(frozen=True)
class AnswerStep:
    """单步手写演化：相对本题 focus 开始的偏移毫秒与区域文本。"""

    offset_ms: int
    text: str
    region: Literal["answer", "scratch"] = "answer"
    confidence: float = 0.92


@dataclass(frozen=True)
class IdlePeriod:
    """本题 focus 段内的停笔/卡壳。"""

    offset_ms: int
    duration_ms: int


@dataclass(frozen=True)
class QuestionBehavior:
    """单题作答行为（用于生成 OCR 事件流）。"""

    time_ms: int
    steps: tuple[AnswerStep, ...]
    idle_periods: tuple[IdlePeriod, ...] = ()
    revisit: bool = False  # 是否中途跳走后再次回来


@dataclass(frozen=True)
class ChoiceOption:
    """选择题单个选项。"""

    key: str
    text: str


@dataclass(frozen=True)
class ExamQuestion:
    question_id: str
    number: int
    page_id: str
    index_on_page: int
    prompt_text: str
    question_type: QuestionType
    difficulty: Difficulty
    max_score: int
    correct_answer: str
    choices: tuple[ChoiceOption, ...] = ()


@dataclass(frozen=True)
class StudentProfile:
    profile_id: str
    label: str
    target_score: int
    duration_ms: int
    session_id: str
    behaviors: dict[str, QuestionBehavior]
    started_at: str = "2026-06-22T14:00:00.000Z"
    accuracy_percent: float = 0.0
    earned_score: float = 0.0


# ---------------------------------------------------------------------------
# 试卷题目（30 题）
# ---------------------------------------------------------------------------

EXAM_QUESTIONS: tuple[ExamQuestion, ...] = (
    ExamQuestion(
        "q01", 1, "page_1", 1,
        "新苗幼儿园大班有男孩126人，女孩84人。中班人数是大班人数的6/7。新苗幼儿园中班有　人。",
        "fill_blank", "easy", 1, "180",
    ),
    ExamQuestion(
        "q02", 2, "page_1", 2,
        "（　）米的2/5是12米，36kg比（　）kg多1/2。",
        "fill_blank", "medium", 2, "30；24",
    ),
    ExamQuestion(
        "q03", 3, "page_1", 3,
        "淘淘要画一个等腰三角形，顶角和一个底角的度数比是1：2，顶角　°，每个底角　°。",
        "fill_blank", "medium", 2, "36；72",
    ),
    ExamQuestion(
        "q04", 4, "page_1", 4,
        "圆规两脚张开3cm，所画圆的直径　cm，周长　cm，面积　cm²。",
        "fill_blank", "easy", 3, "6；18.84；28.26",
    ),
    ExamQuestion(
        "q05", 5, "page_1", 5,
        "小麦出粉率85%，500千克小麦可磨出　千克面粉，磨340千克面粉需小麦　千克。",
        "fill_blank", "easy", 2, "425；400",
    ),
    ExamQuestion(
        "q06", 6, "page_1", 6,
        "按规律继续画下去，第（6）个图形共有　个。",
        "fill_blank", "hard", 1, "25",
    ),
    ExamQuestion(
        "q07", 7, "page_1", 7,
        "16千克铁的1/4和8千克棉花的3/4一样重。（　）",
        "fill_blank", "easy", 1, "×",
    ),
    ExamQuestion(
        "q08", 8, "page_1", 8,
        "0和1的倒数都是它本身。（　）",
        "fill_blank", "easy", 1, "×",
    ),
    ExamQuestion(
        "q09", 9, "page_1", 9,
        "比的前项乘5，后项除以1/5，比值不变。（　）",
        "fill_blank", "easy", 1, "√",
    ),
    ExamQuestion(
        "q10", 10, "page_1", 10,
        "半径是2厘米的圆的面积跟它的周长相等。（　）",
        "fill_blank", "easy", 1, "×",
    ),
    ExamQuestion(
        "q11", 11, "page_1", 11,
        "学校种了98棵树苗，全部成活，成活率是98%。（　）",
        "fill_blank", "easy", 1, "×",
    ),
    ExamQuestion(
        "q12", 12, "page_1", 12,
        "K5路公交：有1/5的人下车，又上来此时车上人数的1/5，上车与下车人数相比（　）。",
        "multiple_choice", "medium", 2, "B",
    ),
    ExamQuestion(
        "q13", 13, "page_1", 13,
        "学校在公园的东偏北40°方向，公园在学校的（　）方向。",
        "multiple_choice", "easy", 2, "B",
    ),
    ExamQuestion(
        "q14", 14, "page_1", 14,
        "240米圆形跑道，爸爸4分钟一圈，小东6分钟一圈，同地相背而行，相遇时间算式（　）。",
        "multiple_choice", "medium", 2, "D",
    ),
    ExamQuestion(
        "q15", 15, "page_1", 15,
        "比是4：5，前项加12，要使比值不变，后项应（　）。",
        "multiple_choice", "medium", 2, "B",
    ),
    ExamQuestion(
        "q16", 16, "page_1", 16,
        "周长31.4cm的圆，圆规两脚间距离（　）cm。",
        "multiple_choice", "easy", 2, "A",
    ),
    ExamQuestion(
        "q17", 17, "page_1", 17,
        "上衣先提价20%再降价20%，现价与原价相比（　）。",
        "multiple_choice", "medium", 2, "C",
    ),
    ExamQuestion(
        "q18", 18, "page_1", 18,
        "根据扇形统计图，参加乒乓球课程大约有（　）人。",
        "multiple_choice", "medium", 2, "A",
    ),
    ExamQuestion(
        "q19", 19, "page_2", 1,
        "直接写得数：15÷10/17=　，14×4/7=　，2/5×10%=　，4/5×1/4÷4/5×1/4=　，"
        "0.5+25%=　，3.14×9=　，2/3×0+3=　，300千克:1/4吨=　",
        "calculation", "easy", 4,
        "25.5；8；0.04；1/16；0.75；28.26；3；6:5",
    ),
    ExamQuestion(
        "q20", 20, "page_2", 2,
        "递等式计算：①1又1/5×2.75+1/4÷5/6  ②5/8×1/6−6×62.5%  "
        "③60×(1−5/12+7/15)  ④3/4−7/16−0.125×8/7",
        "calculation", "hard", 12,
        "①4  ②-13/24  ③63  ④1/8",
    ),
    ExamQuestion(
        "q21", 21, "page_2", 3,
        "化简比：5/8：5/6；0.25：0.45；500千克：1.2吨；1.2平方米：80平方分米",
        "calculation", "medium", 12, "3:4；5:9；5:12；3:2",
    ),
    ExamQuestion(
        "q22", 22, "page_2", 4,
        "求下图中阴影部分的面积。",
        "calculation", "medium", 4, "12.5cm²",
    ),
    ExamQuestion(
        "q23", 23, "page_3", 1,
        "根据台风移动路径（正西300km→西偏北40° 150km→北偏西20° 200km）画移动路线图。",
        "unknown", "hard", 4, "（作图题，路线比例与角度正确）",
    ),
    ExamQuestion(
        "q24", 24, "page_3", 2,
        "长6cm宽4cm的长方形内画最大圆，求面积（保留找圆心痕迹）。",
        "calculation", "medium", 4, "12.56cm²",
    ),
    ExamQuestion(
        "q25", 25, "page_3", 3,
        "粉碎机每小时粉碎3/5吨，2/3小时可粉碎多少吨？25分钟可粉碎多少吨？",
        "word_problem", "medium", 5, "2/5吨；5/36吨",
    ),
    ExamQuestion(
        "q26", 26, "page_3", 4,
        "长城全长21200km，明朝6200km，秦朝是汉朝的1/2，求秦、汉长度。",
        "word_problem", "medium", 5, "秦朝5000km；汉朝10000km",
    ),
    ExamQuestion(
        "q27", 27, "page_3", 5,
        "四五六年级共80件获奖，比2:3:5，六年级比四年级多多少件？",
        "word_problem", "easy", 5, "24件",
    ),
    ExamQuestion(
        "q28", 28, "page_4", 1,
        "田径场：①阴影活动场地面积 ②最内圈跑1圈米数 ③400米赛第二道起跑线前移距离",
        "word_problem", "hard", 5,
        "①6962.5m²  ②357m  ③7.536m",
    ),
    ExamQuestion(
        "q29", 29, "page_4", 2,
        "幸福村去年路灯65盏，今年104盏，今年比去年增加百分之几？",
        "word_problem", "easy", 5, "60%",
    ),
    ExamQuestion(
        "q30", 30, "page_4", 3,
        "环保知识调查：补全统计表、求总人数、补全统计图。",
        "word_problem", "hard", 5,
        "B15% D35% 共400人",
    ),
)

EXAM_PAGES: tuple[dict[str, str | int], ...] = (
    {"page_id": "page_1", "index": 1},
    {"page_id": "page_2", "index": 2},
    {"page_id": "page_3", "index": 3},
    {"page_id": "page_4", "index": 4},
)

# Student profiles live in profile_factory.py (10 sessions for homepage demo).

from exam_mcq_choices import MCQ_CHOICES  # noqa: E402


def _with_mcq_choices(questions: tuple[ExamQuestion, ...]) -> tuple[ExamQuestion, ...]:
    """为选择题注入 options（来自 exam_mcq_choices）。"""
    enriched: list[ExamQuestion] = []
    for q in questions:
        raw = MCQ_CHOICES.get(q.question_id, ())
        if raw and not q.choices:
            choices = tuple(ChoiceOption(key, text) for key, text in raw)
            enriched.append(
                ExamQuestion(
                    q.question_id,
                    q.number,
                    q.page_id,
                    q.index_on_page,
                    q.prompt_text,
                    q.question_type,
                    q.difficulty,
                    q.max_score,
                    q.correct_answer,
                    choices,
                )
            )
        else:
            enriched.append(q)
    return tuple(enriched)


EXAM_QUESTIONS = _with_mcq_choices(EXAM_QUESTIONS)
