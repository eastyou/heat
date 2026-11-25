"""heat 命令行入口。"""

import argparse
import sys
from typing import Optional, Sequence

from .physics import efficiency, format_number, fuel_heat, heat_absorbed, mix_temperature
from .questions import make_questions
from .render import render_demo, render_sheet


def _ensure_utf8_console() -> None:
    """尽量把标准输出与标准错误切换为 UTF-8，失败时忽略。"""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(encoding="utf-8")
        except (ValueError, OSError):
            continue


def _format_joules(value: float) -> str:
    """把焦耳值格式化：整数不带小数点，其余保留两位小数。"""

    if abs(value - round(value)) < 1e-9:
        return "%d" % int(round(value))
    return "%.2f" % value


def _build_parser() -> argparse.ArgumentParser:
    """构建命令行参数解析器。"""

    parser = argparse.ArgumentParser(
        prog="heat",
        description="初中物理热量工具：吸热、燃料放热、热效率、混合温度与练习纸。",
    )
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="命令")

    q_parser = subparsers.add_parser("q", help="计算吸收热量 Q = cmΔt")
    q_parser.add_argument("--mass", type=float, required=True, help="质量，单位 kg（大于 0）")
    q_parser.add_argument(
        "--specific",
        type=float,
        required=True,
        help="比热容，单位 J/(kg·℃)（大于 0）",
    )
    q_parser.add_argument("--delta", type=float, required=True, help="温度变化量，单位 ℃（大于 0）")

    fuel_parser = subparsers.add_parser("fuel", help="计算燃料放热 Q = mq")
    fuel_parser.add_argument("--mass", type=float, required=True, help="燃料质量，单位 kg（大于 0）")
    fuel_parser.add_argument("--value", type=float, required=True, help="热值，单位 J/kg（大于 0）")

    efficiency_parser = subparsers.add_parser("efficiency", help="计算热效率百分比")
    efficiency_parser.add_argument("--useful", type=float, required=True, help="有用能量，单位 J")
    efficiency_parser.add_argument("--total", type=float, required=True, help="总能量，单位 J")

    mix_parser = subparsers.add_parser("mix", help="计算同种物质混合后的终温")
    mix_parser.add_argument("--m1", type=float, required=True, help="第一份质量，单位 kg（大于 0）")
    mix_parser.add_argument("--t1", type=float, required=True, help="第一份温度，单位 ℃")
    mix_parser.add_argument("--m2", type=float, required=True, help="第二份质量，单位 kg（大于 0）")
    mix_parser.add_argument("--t2", type=float, required=True, help="第二份温度，单位 ℃")

    sheet_parser = subparsers.add_parser("sheet", help="生成 A4 热量练习纸")
    sheet_parser.add_argument("--count", type=int, default=8, help="题目数量，范围 1~50（默认 8）")
    sheet_parser.add_argument("--seed", type=int, default=1, help="随机种子（默认 1）")
    sheet_parser.add_argument("-o", "--output", required=True, help="输出 HTML 文件路径")
    sheet_parser.add_argument("--answers", action="store_true", help="附加参考答案页")

    demo_parser = subparsers.add_parser("demo", help="生成公式与例题卡片页")
    demo_parser.add_argument("-o", "--output", required=True, help="输出 HTML 文件路径")

    return parser


def _write_html(path: str, content: str) -> None:
    """把 HTML 内容写入本地文件，失败时抛出中文 ValueError。"""

    if not isinstance(path, str) or not path.strip():
        raise ValueError("输出路径不能为空")
    try:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
    except OSError as exc:
        raise ValueError("无法写入文件 %s：%s" % (path, exc))


def _run(args: argparse.Namespace) -> int:
    """执行具体子命令并返回退出码。"""

    command = args.command
    if command == "q":
        value = heat_absorbed(args.mass, args.specific, args.delta)
        print("吸收热量（Q = cmΔt）")
        print("  质量 m = %s kg" % format_number(args.mass))
        print("  比热容 c = %s J/(kg·℃)" % format_number(args.specific))
        print("  温度变化 Δt = %s ℃" % format_number(args.delta))
        print("  Q = %s J" % _format_joules(value))
        print("  Q = %.1f kJ" % (value / 1000.0))
        return 0

    if command == "fuel":
        value = fuel_heat(args.mass, args.value)
        print("燃料放热（Q = mq）")
        print("  燃料质量 m = %s kg" % format_number(args.mass))
        print("  热值 q = %s J/kg" % format_number(args.value))
        print("  Q = %s J" % _format_joules(value))
        print("  Q = %.1f kJ" % (value / 1000.0))
        return 0

    if command == "efficiency":
        percent = efficiency(args.useful, args.total)
        print("热效率（η = 有用能量 ÷ 总能量 × 100%）")
        print("  有用能量 = %s J" % format_number(args.useful))
        print("  总能量 = %s J" % format_number(args.total))
        print("  η = %.1f%%" % percent)
        return 0

    if command == "mix":
        value = mix_temperature(args.m1, args.t1, args.m2, args.t2)
        print("混合终温（t = (m1t1 + m2t2) ÷ (m1 + m2)）")
        print(
            "  m1 = %s kg，t1 = %s ℃"
            % (format_number(args.m1), format_number(args.t1))
        )
        print(
            "  m2 = %s kg，t2 = %s ℃"
            % (format_number(args.m2), format_number(args.t2))
        )
        print("  t = %.1f ℃" % value)
        return 0

    if command == "sheet":
        questions = make_questions(args.count, args.seed)
        content = render_sheet(questions, bool(args.answers))
        _write_html(args.output, content)
        print("已生成练习纸：%s" % args.output)
        print("  题目数量：%d" % len(questions))
        print("  答案页：%s" % ("包含" if args.answers else "不包含"))
        return 0

    if command == "demo":
        content = render_demo()
        _write_html(args.output, content)
        print("已生成公式卡片页：%s" % args.output)
        return 0

    raise ValueError("未知命令：%s" % command)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """命令行主函数，成功返回 0，输入非法或写文件失败返回 2。"""

    _ensure_utf8_console()
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return _run(args)
    except (TypeError, ValueError) as exc:
        print("错误：%s" % exc, file=sys.stderr)
        return 2
