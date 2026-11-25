"""练习纸与公式卡片页的 HTML 渲染。"""

import html
from typing import List, Sequence

from .physics import (
    efficiency,
    format_number,
    fuel_heat,
    heat_absorbed,
    mix_temperature,
)
from .questions import Question

_CSS = """
@page { size: A4; margin: 16mm; }
* { box-sizing: border-box; }
body {
  margin: 0;
  padding: 12mm 0;
  background: #eceff3;
  color: #1f2933;
  font-family: "Songti SC", "SimSun", "Noto Serif CJK SC", serif;
  font-size: 15px;
  line-height: 1.7;
}
.sheet {
  width: 210mm;
  min-height: 297mm;
  margin: 0 auto 12mm;
  padding: 16mm 18mm;
  background: #ffffff;
  box-shadow: 0 2px 10px rgba(31, 41, 51, 0.12);
}
.sheet-head { border-bottom: 2px solid #1f2933; margin-bottom: 6mm; padding-bottom: 4mm; }
.sheet-head h1 { margin: 0 0 4mm; font-size: 24px; letter-spacing: 2px; text-align: center; }
.meta { margin: 0; font-size: 13px; color: #3e4c59; display: flex; justify-content: space-between; }
.note { margin: 0 0 8mm; font-size: 12px; color: #616e7c; }
.questions {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8mm 10mm;
}
.question { padding-bottom: 4mm; border-bottom: 1px dashed #cbd2d9; break-inside: avoid; }
.kind { margin: 0 0 2mm; font-size: 12px; letter-spacing: 1px; color: #52606d; }
.prompt { margin: 0 0 3mm; font-size: 15px; text-align: justify; }
.space { height: 22mm; border-bottom: 1px solid #e4e7eb; }
.empty { margin: 20mm 0; text-align: center; color: #616e7c; }
.subhead { margin: 0 0 6mm; font-size: 20px; letter-spacing: 2px; text-align: center; }
.answers {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4mm 10mm;
  font-size: 14px;
}
.answers li { break-inside: avoid; }
.answers .no { margin-right: 2mm; color: #52606d; }
.cards { display: grid; grid-template-columns: 1fr 1fr; gap: 8mm; margin-top: 8mm; }
.card { border: 1px solid #cbd2d9; border-radius: 6px; padding: 6mm; break-inside: avoid; }
.card h2 { margin: 0 0 3mm; font-size: 16px; letter-spacing: 1px; }
.formula {
  margin: 0 0 3mm;
  font-family: "Times New Roman", "Songti SC", serif;
  font-size: 20px;
  color: #0b3d91;
}
.card p { margin: 0 0 2mm; font-size: 13px; text-align: justify; }
.card .result { color: #1f6f43; }
.lead { margin: 0; font-size: 13px; color: #3e4c59; text-align: center; }
@media print {
  body { background: #ffffff; padding: 0; }
  .sheet {
    width: auto;
    min-height: 0;
    margin: 0;
    padding: 0;
    box-shadow: none;
  }
  .answer-page { page-break-before: always; }
}
"""


def _document(title: str, body: str) -> str:
    """拼装完整的 HTML 文档，body 为页面主体的 HTML 片段。"""

    parts: List[str] = [
        "<!DOCTYPE html>\n",
        '<html lang="zh-CN">\n',
        "<head>\n",
        '<meta charset="utf-8">\n',
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n',
        "<title>%s</title>\n" % html.escape(title),
        "<style>%s</style>\n" % _CSS,
        "</head>\n",
        "<body>\n",
        body,
        "</body>\n",
        "</html>\n",
    ]
    return "".join(parts)


def _validate_questions(questions: Sequence[Question]) -> List[Question]:
    """把外部传入的题目序列转换为列表并逐项校验。"""

    if isinstance(questions, (str, bytes)):
        raise TypeError("题目列表必须是 Question 对象的序列")
    try:
        items = list(questions)
    except TypeError:
        raise TypeError("题目列表必须是 Question 对象的序列")
    for item in items:
        if not isinstance(item, Question):
            raise TypeError("题目列表只能包含 Question 对象")
    return items


def render_sheet(questions: Sequence[Question], answers: bool) -> str:
    """渲染 A4 练习纸；answers 为真时在末尾附一页参考答案。"""

    items = _validate_questions(questions)
    if not isinstance(answers, bool):
        raise TypeError("answers 必须是布尔值")

    blocks: List[str] = []
    for question in items:
        blocks.append(
            '<li class="question">\n'
            '<p class="kind">%s</p>\n'
            '<p class="prompt">%d. %s</p>\n'
            '<div class="space"></div>\n'
            "</li>\n"
            % (html.escape(question.kind), question.index, html.escape(question.prompt))
        )
    if blocks:
        body = '<ol class="questions">\n%s</ol>\n' % "".join(blocks)
    else:
        body = '<p class="empty">本页暂无题目。</p>\n'

    head = (
        '<header class="sheet-head">\n'
        "<h1>初中物理 · 热量练习纸</h1>\n"
        '<p class="meta">'
        "<span>姓名：__________</span>"
        "<span>班级：__________</span>"
        "<span>日期：__________</span>"
        "</p>\n"
        "</header>\n"
        '<p class="note">要求：先写公式，再代入数据，最后注明单位。</p>\n'
    )
    body = '<main class="sheet">\n' + head + body + "</main>\n"

    if answers:
        rows: List[str] = []
        for question in items:
            rows.append(
                '<li><span class="no">%d.</span>%s</li>\n'
                % (question.index, html.escape(question.answer))
            )
        if rows:
            answer_body = (
                '<h2 class="subhead">参考答案</h2>\n<ol class="answers">\n%s</ol>\n'
                % "".join(rows)
            )
        else:
            answer_body = '<p class="empty">本页暂无答案。</p>\n'
        body += '<main class="sheet answer-page">\n' + answer_body + "</main>\n"

    return _document("初中物理 · 热量练习纸", body)


def _card(title: str, formula: str, lines: Sequence[str], result: str) -> str:
    """拼装一张公式卡片。"""

    paragraphs = "".join("<p>%s</p>\n" % html.escape(line) for line in lines)
    return (
        '<article class="card">\n'
        "<h2>%s</h2>\n"
        '<p class="formula">%s</p>\n'
        "%s"
        '<p class="result">%s</p>\n'
        "</article>\n"
        % (
            html.escape(title),
            html.escape(formula),
            paragraphs,
            html.escape(result),
        )
    )


def render_demo() -> str:
    """渲染公式与例题卡片页。"""

    absorbed = heat_absorbed(2, 4200, 10)
    fuel = fuel_heat(0.5, 46000000)
    percent = efficiency(84000, 100000)
    mixed = mix_temperature(1, 80, 2, 20)

    cards = [
        _card(
            "吸收热量",
            "Q = cmΔt",
            ["c 为比热容，m 为质量，Δt 为温度变化量。", "例：2 kg 水升温 10 ℃，c = 4200 J/(kg·℃)。"],
            "Q = 4200 × 2 × 10 = %s J" % format_number(absorbed),
        ),
        _card(
            "燃料放热",
            "Q = mq",
            ["m 为燃料质量，q 为燃料的热值。", "例：完全燃烧 0.5 kg 热值为 46000000 J/kg 的燃料。"],
            "Q = 0.5 × 46000000 = %s J" % format_number(fuel),
        ),
        _card(
            "热效率",
            "η = Q有用 ÷ Q总 × 100%",
            ["有用能量与总能量的比值，结果常用百分数表示。", "例：消耗 100000 J，有效利用 84000 J。"],
            "η = 84000 ÷ 100000 × 100%% = %.1f%%" % percent,
        ),
        _card(
            "混合温度",
            "t = (m1t1 + m2t2) ÷ (m1 + m2)",
            ["同种物质混合且不计热量损失时成立。", "例：1 kg、80 ℃ 与 2 kg、20 ℃ 混合。"],
            "t = (1 × 80 + 2 × 20) ÷ 3 = %.1f ℃" % mixed,
        ),
    ]

    body = (
        '<main class="sheet">\n'
        '<header class="sheet-head">\n'
        "<h1>初中物理 · 热量公式与例题</h1>\n"
        '<p class="lead">四个核心公式与对应例题，可直接用于课堂展示或打印。</p>\n'
        "</header>\n"
        '<section class="cards">\n%s</section>\n'
        "</main>\n" % "".join(cards)
    )
    return _document("初中物理 · 热量公式与例题", body)
