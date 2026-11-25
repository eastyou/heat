# heat

[![CI](https://github.com/eastyou/heat/actions/workflows/ci.yml/badge.svg)](https://github.com/eastyou/heat/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](pyproject.toml)

heat 是一个面向初中物理教学的命令行工具，用于计算吸收热量、燃料放热、热效率与同种物质的混合终温，并能生成可打印的 A4 练习纸和公式卡片页。项目只使用 Python 标准库，不依赖任何第三方包。

## 特性

- 提供 `q`、`fuel`、`efficiency`、`mix`、`sheet`、`demo` 六个子命令，覆盖初中热学的主要计算题型。
- 计算结果同时以焦耳（J）和千焦（kJ）输出，便于课堂讲解与作业对照。
- 练习纸按 A4 纸张排版，可直接打印；`--answers` 会在末尾附加一页参考答案。
- `--seed` 固定随机种子后，每次生成的题目完全一致，方便教师复现同一套练习。
- 所有数值输入都会校验：布尔值、NaN、无穷大、非数字文本、越界值、空路径都会被拒绝并给出中文提示。
- 计算结果显示为有限值，且限制在 1e15 以内，避免因输入过大产生无意义的结果。
- 代码兼容 Python 3.9，可在 Windows、Linux 与 macOS 上运行。

## 安装

要求 Python 3.9 或更高版本，无需安装第三方依赖。

```bash
# 在仓库根目录安装为可编辑包，随后可直接使用 heat 命令
pip install -e .
```

也可以不安装，直接在仓库根目录以模块方式运行：

```bash
python3 -m heat --help
```

## 使用

计算 2 kg 水温度升高 10 ℃ 吸收的热量（水的比热容取 4200 J/(kg·℃)）：

```bash
heat q --mass 2 --specific 4200 --delta 10
```

```text
吸收热量（Q = cmΔt）
  质量 m = 2 kg
  比热容 c = 4200 J/(kg·℃)
  温度变化 Δt = 10 ℃
  Q = 84000 J
  Q = 84.0 kJ
```

计算 0.5 kg 热值为 46000000 J/kg 的燃料完全燃烧放出的热量：

```bash
heat fuel --mass 0.5 --value 46000000
```

```text
燃料放热（Q = mq）
  燃料质量 m = 0.5 kg
  热值 q = 46000000 J/kg
  Q = 23000000 J
  Q = 23000.0 kJ
```

计算热效率：

```bash
heat efficiency --useful 84000 --total 100000
```

```text
热效率（η = 有用能量 ÷ 总能量 × 100%）
  有用能量 = 84000 J
  总能量 = 100000 J
  η = 84.0%
```

计算 1 kg、80 ℃ 的液体与 2 kg、20 ℃ 的同种液体混合后的温度：

```bash
heat mix --m1 1 --t1 80 --m2 2 --t2 20
```

```text
混合终温（t = (m1t1 + m2t2) ÷ (m1 + m2)）
  m1 = 1 kg，t1 = 80 ℃
  m2 = 2 kg，t2 = 20 ℃
  t = 40.0 ℃
```

生成 8 道题并附带答案页：

```bash
heat sheet --count 8 --seed 1 -o sheet.html --answers
```

```text
已生成练习纸：sheet.html
  题目数量：8
  答案页：包含
```

生成公式与例题卡片页：

```bash
heat demo -o demo.html
```

```text
已生成公式卡片页：demo.html
```

输入不合法时，错误信息写入标准错误，退出码为 2：

```bash
heat q --mass 0 --specific 4200 --delta 10
```

```text
错误：质量必须大于 0
```

### 参数

| 子命令 | 参数 | 说明 |
| --- | --- | --- |
| `q` | `--mass` | 质量，单位 kg，必须大于 0 |
| `q` | `--specific` | 比热容，单位 J/(kg·℃)，必须大于 0 |
| `q` | `--delta` | 温度变化量，单位 ℃，必须大于 0 |
| `fuel` | `--mass` | 燃料质量，单位 kg，必须大于 0 |
| `fuel` | `--value` | 燃料热值，单位 J/kg，必须大于 0 |
| `efficiency` | `--useful` | 有用能量，单位 J，必须大于 0 且不超过总能量 |
| `efficiency` | `--total` | 总能量，单位 J，必须大于 0 |
| `mix` | `--m1` / `--m2` | 两份同种液体的质量，单位 kg，必须大于 0 |
| `mix` | `--t1` / `--t2` | 两份液体的温度，单位 ℃，取值须大于 -273.15 且不超过 1000 |
| `sheet` | `--count` | 题目数量，范围 1~50，默认 8 |
| `sheet` | `--seed` | 随机种子，默认 1 |
| `sheet` | `-o` / `--output` | 输出 HTML 文件路径，必填 |
| `sheet` | `--answers` | 附加参考答案页 |
| `demo` | `-o` / `--output` | 输出 HTML 文件路径，必填 |

### 退出码

| 退出码 | 含义 |
| --- | --- |
| 0 | 计算成功或文件写入成功 |
| 2 | 参数缺失、数值非法、输入越界或文件写入失败，错误信息输出到 stderr |

## 作为库使用

```python
from heat import (
    efficiency,
    fuel_heat,
    heat_absorbed,
    make_questions,
    mix_temperature,
    render_sheet,
)

print(heat_absorbed(2, 4200, 10))        # 84000.0
print(fuel_heat(0.5, 46000000))          # 23000000.0
print(efficiency(84000, 100000))         # 84.0
print(mix_temperature(1, 80, 2, 20))     # 40.0

questions = make_questions(8, seed=1)
html = render_sheet(questions, answers=True)
```

## 开发与测试

项目使用 unittest，测试文件为 `tests/test_heat.py`，共 110 个测试用例，覆盖正常值、边界值、非法输入、HTML 解析、随机种子复现以及全部子命令。

```bash
python3 -m unittest discover -s tests -v
```

测试在 Python 3.9.6 与 3.15.2 下运行，均为 110 个用例全部通过。

## License

[MIT](LICENSE) © 2026 eastyou
