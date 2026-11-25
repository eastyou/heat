"""初中物理热量公式的实现与输入校验。"""

import math
from typing import Union

Number = Union[int, float, str]

# 计算结果允许的上限，超出视为输入不合理。
MAX_RESULT = 1e15
# 温度的物理下限（绝对零度）与练习场景的合理上限。
MIN_TEMPERATURE = -273.15
MAX_TEMPERATURE = 1000.0


def format_number(value: float, digits: int = 2) -> str:
    """把数值格式化为去掉多余零的字符串。"""

    text = ("%." + str(digits) + "f") % value
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    if text in ("", "-0"):
        return "0"
    return text


def _to_float(value: Number, name: str) -> float:
    """把外部输入转换为有限浮点数，失败时抛出中文异常。"""

    if isinstance(value, bool):
        raise TypeError("%s不能是布尔值" % name)
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str):
        try:
            number = float(value.strip())
        except ValueError:
            raise ValueError("%s必须是数值：%s" % (name, value.strip()))
    else:
        raise TypeError("%s必须是数值" % name)
    if not math.isfinite(number):
        raise ValueError("%s必须是有限的数值" % name)
    return number


def _require_positive(value: float, name: str) -> float:
    """要求数值大于 0。"""

    if value <= 0:
        raise ValueError("%s必须大于 0" % name)
    return value


def _check_temperature(value: Number, name: str) -> float:
    """校验温度是否落在练习允许的范围内。"""

    temperature = _to_float(value, name)
    if temperature <= MIN_TEMPERATURE:
        raise ValueError("%s必须大于 %.2f ℃" % (name, MIN_TEMPERATURE))
    if temperature > MAX_TEMPERATURE:
        raise ValueError("%s不能超过 %.0f ℃" % (name, MAX_TEMPERATURE))
    return temperature


def _check_result(value: float, name: str) -> float:
    """校验计算结果是否有限且没有超出上限。"""

    if not math.isfinite(value):
        raise ValueError("%s的计算结果不是有限数值" % name)
    if abs(value) >= MAX_RESULT:
        raise ValueError("%s的计算结果过大，请检查输入" % name)
    return value


def heat_absorbed(mass: Number, specific: Number, delta: Number) -> float:
    """计算吸收热量 Q = c·m·Δt，单位为焦耳。"""

    mass_value = _require_positive(_to_float(mass, "质量"), "质量")
    specific_value = _require_positive(_to_float(specific, "比热容"), "比热容")
    delta_value = _require_positive(_to_float(delta, "温度变化"), "温度变化")
    return _check_result(mass_value * specific_value * delta_value, "吸收热量")


def fuel_heat(mass: Number, value: Number) -> float:
    """计算燃料完全燃烧放出的热量 Q = m·q，单位为焦耳。"""

    mass_value = _require_positive(_to_float(mass, "燃料质量"), "燃料质量")
    heat_value = _require_positive(_to_float(value, "热值"), "热值")
    return _check_result(mass_value * heat_value, "燃料放热")


def efficiency(useful: Number, total: Number) -> float:
    """计算热效率百分比，保留 1 位小数。"""

    useful_value = _require_positive(_to_float(useful, "有用能量"), "有用能量")
    total_value = _require_positive(_to_float(total, "总能量"), "总能量")
    if useful_value > total_value:
        raise ValueError("有用能量不能大于总能量")
    return round(useful_value / total_value * 100.0, 1)


def mix_temperature(m1: Number, t1: Number, m2: Number, t2: Number) -> float:
    """同种物质混合后的终温 t = (m1·t1 + m2·t2) / (m1 + m2)。"""

    mass_one = _require_positive(_to_float(m1, "第一份质量"), "第一份质量")
    mass_two = _require_positive(_to_float(m2, "第二份质量"), "第二份质量")
    temp_one = _check_temperature(t1, "第一份温度")
    temp_two = _check_temperature(t2, "第二份温度")
    total_mass = mass_one + mass_two
    result = (mass_one * temp_one + mass_two * temp_two) / total_mass
    if not (MIN_TEMPERATURE < result <= MAX_TEMPERATURE):
        raise ValueError("混合后的温度超出允许范围")
    return _check_result(result, "混合温度")
