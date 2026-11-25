"""热量练习题的生成逻辑。"""

import random
from dataclasses import dataclass
from typing import Callable, List, Tuple

from .physics import (
    efficiency,
    format_number,
    fuel_heat,
    heat_absorbed,
    mix_temperature,
)

# 题库使用的数据范围，数值经过挑选以保证结果远小于上限。
_SPECIFIC_HEATS: Tuple[float, ...] = (4200.0, 2100.0, 460.0, 880.0, 2400.0)
_DELTAS: Tuple[float, ...] = (10.0, 20.0, 25.0, 30.0, 40.0, 50.0, 60.0, 80.0)
_MASSES: Tuple[float, ...] = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0)
_FUEL_VALUES: Tuple[float, ...] = (30000000.0, 40000000.0, 44000000.0, 46000000.0)
_FUEL_MASSES: Tuple[float, ...] = (0.1, 0.2, 0.5, 1.0, 2.0)
_TOTALS: Tuple[int, ...] = (1000, 2000, 5000, 10000, 20000, 50000, 100000)
_PERCENTS: Tuple[int, ...] = (40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95)
_MIX_MASSES: Tuple[float, ...] = (0.5, 1.0, 1.5, 2.0, 3.0, 4.0)
_HOT_TEMPERATURES: Tuple[float, ...] = (50.0, 60.0, 70.0, 80.0, 90.0, 95.0)
_COLD_TEMPERATURES: Tuple[float, ...] = (0.0, 10.0, 15.0, 20.0, 25.0, 30.0)

_MIN_SEED = -(2 ** 31)
_MAX_SEED = 2 ** 31 - 1


@dataclass(frozen=True)
class Question:
    """一道热量练习题。"""

    index: int
    kind: str
    prompt: str
    answer: str


def _check_int(value: int, name: str, minimum: int, maximum: int) -> int:
    """校验整数型外部输入。"""

    if isinstance(value, bool):
        raise TypeError("%s不能是布尔值" % name)
    if not isinstance(value, int):
        raise TypeError("%s必须是整数" % name)
    if value < minimum or value > maximum:
        raise ValueError("%s必须在 %d 到 %d 之间" % (name, minimum, maximum))
    return value


def _format_energy(joules: float) -> str:
    """把能量格式化为「J（kJ）」的形式。"""

    return "%s J（%.1f kJ）" % (format_number(joules), joules / 1000.0)


def _absorbed_question(rng: random.Random, index: int) -> Question:
    mass = rng.choice(_MASSES)
    specific = rng.choice(_SPECIFIC_HEATS)
    delta = rng.choice(_DELTAS)
    value = heat_absorbed(mass, specific, delta)
    prompt = (
        "质量为 %s kg 的物质，比热容为 %s J/(kg·℃)，温度升高 %s ℃，"
        "需要吸收多少热量？"
        % (format_number(mass), format_number(specific), format_number(delta))
    )
    answer = "Q = cmΔt = %s × %s × %s = %s" % (
        format_number(specific),
        format_number(mass),
        format_number(delta),
        _format_energy(value),
    )
    return Question(index=index, kind="吸热", prompt=prompt, answer=answer)


def _fuel_question(rng: random.Random, index: int) -> Question:
    mass = rng.choice(_FUEL_MASSES)
    value = rng.choice(_FUEL_VALUES)
    joules = fuel_heat(mass, value)
    prompt = "完全燃烧 %s kg 热值为 %s J/kg 的燃料，能放出多少热量？" % (
        format_number(mass),
        format_number(value),
    )
    answer = "Q = mq = %s × %s = %s" % (
        format_number(mass),
        format_number(value),
        _format_energy(joules),
    )
    return Question(index=index, kind="热值", prompt=prompt, answer=answer)


def _efficiency_question(rng: random.Random, index: int) -> Question:
    total = rng.choice(_TOTALS)
    percent = rng.choice(_PERCENTS)
    useful = total * percent // 100
    value = efficiency(useful, total)
    prompt = "某装置消耗总能量 %s J，其中有效利用 %s J，求它的热效率是多少？" % (
        format_number(total),
        format_number(useful),
    )
    answer = "η = %s ÷ %s × 100%% = %.1f%%" % (
        format_number(useful),
        format_number(total),
        value,
    )
    return Question(index=index, kind="热效率", prompt=prompt, answer=answer)


def _mix_question(rng: random.Random, index: int) -> Question:
    mass_one = rng.choice(_MIX_MASSES)
    mass_two = rng.choice(_MIX_MASSES)
    temp_one = rng.choice(_HOT_TEMPERATURES)
    temp_two = rng.choice(_COLD_TEMPERATURES)
    value = mix_temperature(mass_one, temp_one, mass_two, temp_two)
    prompt = (
        "把 %s kg、%s ℃ 的液体与 %s kg、%s ℃ 的同种液体混合，"
        "不计热量损失，求混合后的温度是多少？"
        % (
            format_number(mass_one),
            format_number(temp_one),
            format_number(mass_two),
            format_number(temp_two),
        )
    )
    answer = "t = (m1t1 + m2t2) ÷ (m1 + m2) = (%s × %s + %s × %s) ÷ (%s + %s) = %.1f ℃" % (
        format_number(mass_one),
        format_number(temp_one),
        format_number(mass_two),
        format_number(temp_two),
        format_number(mass_one),
        format_number(mass_two),
        value,
    )
    return Question(index=index, kind="混合温度", prompt=prompt, answer=answer)


_BUILDERS: Tuple[Callable[[random.Random, int], Question], ...] = (
    _absorbed_question,
    _fuel_question,
    _efficiency_question,
    _mix_question,
)


def make_questions(count: int, seed: int) -> List[Question]:
    """按种子生成指定数量的练习题，数量范围为 1 到 50。"""

    total = _check_int(count, "题目数量", 1, 50)
    seed_value = _check_int(seed, "随机种子", _MIN_SEED, _MAX_SEED)
    rng = random.Random(seed_value)
    questions: List[Question] = []
    for position in range(total):
        index = position + 1
        builder = _BUILDERS[position % len(_BUILDERS)]
        questions.append(builder(rng, index))
    return questions
