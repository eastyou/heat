"""heat 的单元测试。"""

import contextlib
import io
import os
import tempfile
import unittest
from dataclasses import FrozenInstanceError
from html.parser import HTMLParser
from typing import List, Optional, Tuple

from heat import (
    Question,
    __version__,
    efficiency,
    fuel_heat,
    heat_absorbed,
    make_questions,
    mix_temperature,
    render_demo,
    render_sheet,
)
from heat.cli import main
from heat.physics import format_number


class _TagCollector(HTMLParser):
    """记录 HTML 中出现的所有标签名。"""

    def __init__(self) -> None:
        super().__init__()
        self.tags: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]) -> None:
        self.tags.append(tag)


def _parse_tags(text: str) -> List[str]:
    collector = _TagCollector()
    collector.feed(text)
    collector.close()
    return collector.tags


def _run_main(argv: List[str]) -> Tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(argv)
    return code, stdout.getvalue(), stderr.getvalue()


class TestFormatNumber(unittest.TestCase):
    def test_integer_value(self) -> None:
        self.assertEqual(format_number(84000.0), "84000")

    def test_decimal_value(self) -> None:
        self.assertEqual(format_number(0.5), "0.5")

    def test_trailing_zero_removed(self) -> None:
        self.assertEqual(format_number(2.50), "2.5")

    def test_zero_value(self) -> None:
        self.assertEqual(format_number(0.0), "0")

    def test_digits_argument(self) -> None:
        self.assertEqual(format_number(2.125, 3), "2.125")


class TestHeatAbsorbed(unittest.TestCase):
    def test_normal_value(self) -> None:
        self.assertAlmostEqual(heat_absorbed(2, 4200, 10), 84000.0)

    def test_float_inputs(self) -> None:
        self.assertAlmostEqual(heat_absorbed(0.5, 2100, 20), 21000.0)

    def test_string_inputs(self) -> None:
        self.assertAlmostEqual(heat_absorbed("2", "4200", "10"), 84000.0)

    def test_zero_mass_rejected(self) -> None:
        with self.assertRaises(ValueError):
            heat_absorbed(0, 4200, 10)

    def test_negative_mass_rejected(self) -> None:
        with self.assertRaises(ValueError):
            heat_absorbed(-1, 4200, 10)

    def test_zero_specific_rejected(self) -> None:
        with self.assertRaises(ValueError):
            heat_absorbed(2, 0, 10)

    def test_negative_delta_rejected(self) -> None:
        with self.assertRaises(ValueError):
            heat_absorbed(2, 4200, -5)

    def test_zero_delta_rejected(self) -> None:
        with self.assertRaises(ValueError):
            heat_absorbed(2, 4200, 0)

    def test_bool_rejected(self) -> None:
        with self.assertRaises(TypeError):
            heat_absorbed(True, 4200, 10)

    def test_none_rejected(self) -> None:
        with self.assertRaises(TypeError):
            heat_absorbed(None, 4200, 10)

    def test_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            heat_absorbed(float("nan"), 4200, 10)

    def test_inf_rejected(self) -> None:
        with self.assertRaises(ValueError):
            heat_absorbed(float("inf"), 4200, 10)

    def test_invalid_string_rejected(self) -> None:
        with self.assertRaises(ValueError):
            heat_absorbed("两千克", 4200, 10)

    def test_overflow_rejected(self) -> None:
        with self.assertRaises(ValueError):
            heat_absorbed(1e8, 1e8, 1e2)


class TestFuelHeat(unittest.TestCase):
    def test_normal_value(self) -> None:
        self.assertAlmostEqual(fuel_heat(0.5, 46000000), 23000000.0)

    def test_float_value(self) -> None:
        self.assertAlmostEqual(fuel_heat(0.1, 30000000), 3000000.0)

    def test_zero_mass_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fuel_heat(0, 46000000)

    def test_negative_mass_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fuel_heat(-0.5, 46000000)

    def test_zero_heat_value_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fuel_heat(0.5, 0)

    def test_negative_heat_value_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fuel_heat(0.5, -46000000)

    def test_bool_rejected(self) -> None:
        with self.assertRaises(TypeError):
            fuel_heat(False, 46000000)

    def test_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fuel_heat(0.5, float("nan"))

    def test_overflow_rejected(self) -> None:
        with self.assertRaises(ValueError):
            fuel_heat(1e8, 1e8)


class TestEfficiency(unittest.TestCase):
    def test_normal_value(self) -> None:
        self.assertAlmostEqual(efficiency(84000, 100000), 84.0)

    def test_one_decimal_rounding(self) -> None:
        self.assertAlmostEqual(efficiency(1, 3), 33.3)

    def test_full_efficiency(self) -> None:
        self.assertAlmostEqual(efficiency(500, 500), 100.0)

    def test_zero_useful_rejected(self) -> None:
        with self.assertRaises(ValueError):
            efficiency(0, 100000)

    def test_useful_larger_than_total_rejected(self) -> None:
        with self.assertRaises(ValueError):
            efficiency(100001, 100000)

    def test_zero_total_rejected(self) -> None:
        with self.assertRaises(ValueError):
            efficiency(100, 0)

    def test_negative_total_rejected(self) -> None:
        with self.assertRaises(ValueError):
            efficiency(100, -100)

    def test_bool_rejected(self) -> None:
        with self.assertRaises(TypeError):
            efficiency(True, 100)

    def test_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            efficiency(float("nan"), 100)


class TestMixTemperature(unittest.TestCase):
    def test_normal_value(self) -> None:
        self.assertAlmostEqual(mix_temperature(1, 80, 2, 20), 40.0)

    def test_equal_mass(self) -> None:
        self.assertAlmostEqual(mix_temperature(2, 60, 2, 20), 40.0)

    def test_second_heavier(self) -> None:
        self.assertAlmostEqual(mix_temperature(1, 90, 3, 10), 30.0)

    def test_zero_mass_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mix_temperature(0, 80, 2, 20)

    def test_negative_mass_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mix_temperature(1, 80, -2, 20)

    def test_temperature_below_absolute_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mix_temperature(1, -273.15, 2, 20)

    def test_temperature_upper_bound_accepted(self) -> None:
        self.assertAlmostEqual(mix_temperature(1, 1000, 1, 1000), 1000.0)

    def test_temperature_above_upper_bound_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mix_temperature(1, 1000.1, 2, 20)

    def test_bool_rejected(self) -> None:
        with self.assertRaises(TypeError):
            mix_temperature(True, 80, 2, 20)

    def test_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            mix_temperature(1, float("nan"), 2, 20)


class TestMakeQuestions(unittest.TestCase):
    def test_count_one(self) -> None:
        self.assertEqual(len(make_questions(1, 1)), 1)

    def test_count_eight(self) -> None:
        self.assertEqual(len(make_questions(8, 1)), 8)

    def test_count_fifty(self) -> None:
        self.assertEqual(len(make_questions(50, 2026)), 50)

    def test_count_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(0, 1)

    def test_count_too_large_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(51, 1)

    def test_count_bool_rejected(self) -> None:
        with self.assertRaises(TypeError):
            make_questions(True, 1)

    def test_count_float_rejected(self) -> None:
        with self.assertRaises(TypeError):
            make_questions(8.0, 1)

    def test_seed_reproducible(self) -> None:
        self.assertEqual(make_questions(8, 1), make_questions(8, 1))

    def test_different_seed_differs(self) -> None:
        self.assertNotEqual(make_questions(8, 1), make_questions(8, 2))

    def test_negative_seed_accepted(self) -> None:
        self.assertEqual(len(make_questions(4, -5)), 4)

    def test_seed_too_large_rejected(self) -> None:
        with self.assertRaises(ValueError):
            make_questions(4, 2 ** 31)

    def test_seed_bool_rejected(self) -> None:
        with self.assertRaises(TypeError):
            make_questions(4, True)

    def test_kinds_cover_all_four(self) -> None:
        kinds = set(question.kind for question in make_questions(8, 3))
        self.assertEqual(kinds, {"吸热", "热值", "热效率", "混合温度"})

    def test_index_is_sequential(self) -> None:
        indexes = [question.index for question in make_questions(8, 1)]
        self.assertEqual(indexes, list(range(1, 9)))

    def test_prompt_ends_with_question_mark(self) -> None:
        for question in make_questions(20, 9):
            self.assertTrue(question.prompt.endswith("？"))

    def test_answer_not_empty(self) -> None:
        for question in make_questions(20, 9):
            self.assertGreater(len(question.answer), 0)

    def test_absorbed_answer_contains_joule(self) -> None:
        question = make_questions(4, 1)[0]
        self.assertEqual(question.kind, "吸热")
        self.assertIn("J", question.answer)
        self.assertIn("Q = cmΔt", question.answer)

    def test_efficiency_answer_contains_percent(self) -> None:
        question = make_questions(4, 1)[2]
        self.assertEqual(question.kind, "热效率")
        self.assertIn("%", question.answer)


class TestRenderSheet(unittest.TestCase):
    def setUp(self) -> None:
        self.questions = make_questions(8, 1)

    def test_returns_html_document(self) -> None:
        output = render_sheet(self.questions, False)
        self.assertIsInstance(output, str)
        self.assertTrue(output.startswith("<!DOCTYPE html>"))

    def test_parseable_by_html_parser(self) -> None:
        tags = _parse_tags(render_sheet(self.questions, False))
        for required in ("html", "head", "body", "main", "ol", "li"):
            self.assertIn(required, tags)

    def test_contains_all_questions(self) -> None:
        output = render_sheet(self.questions, False)
        self.assertEqual(output.count('<li class="question">'), 8)

    def test_no_answer_page_by_default(self) -> None:
        output = render_sheet(self.questions, False)
        self.assertNotIn("参考答案", output)
        self.assertNotIn('class="sheet answer-page"', output)

    def test_answer_page_when_requested(self) -> None:
        output = render_sheet(self.questions, True)
        self.assertIn("参考答案", output)
        self.assertIn("answer-page", output)
        self.assertEqual(output.count('<li class="question">'), 8)

    def test_answer_text_present(self) -> None:
        output = render_sheet(self.questions, True)
        self.assertIn(self.questions[0].answer, output)

    def test_escaping_of_dynamic_text(self) -> None:
        question = Question(
            index=1,
            kind="<吸热>",
            prompt="含 <script>alert(1)</script> 的题目",
            answer="答案 <b>Q</b>",
        )
        output = render_sheet([question], True)
        self.assertNotIn("<script>", output)
        self.assertIn("&lt;script&gt;", output)
        self.assertNotIn("<b>Q</b>", output)
        self.assertIn("&lt;b&gt;Q&lt;/b&gt;", output)

    def test_empty_questions_placeholder(self) -> None:
        output = render_sheet([], False)
        self.assertIn("本页暂无题目", output)
        self.assertEqual(output.count('<li class="question">'), 0)

    def test_empty_questions_with_answers(self) -> None:
        output = render_sheet([], True)
        self.assertIn("本页暂无答案", output)

    def test_accepts_tuple(self) -> None:
        output = render_sheet((self.questions[0], self.questions[1]), False)
        self.assertEqual(output.count('<li class="question">'), 2)

    def test_answers_must_be_bool(self) -> None:
        with self.assertRaises(TypeError):
            render_sheet(self.questions, 1)

    def test_none_questions_rejected(self) -> None:
        with self.assertRaises(TypeError):
            render_sheet(None, False)

    def test_string_questions_rejected(self) -> None:
        with self.assertRaises(TypeError):
            render_sheet("题目", False)

    def test_non_question_item_rejected(self) -> None:
        with self.assertRaises(TypeError):
            render_sheet([object()], False)


class TestRenderDemo(unittest.TestCase):
    def test_returns_html_document(self) -> None:
        output = render_demo()
        self.assertTrue(output.startswith("<!DOCTYPE html>"))

    def test_parseable_by_html_parser(self) -> None:
        tags = _parse_tags(render_demo())
        for required in ("html", "body", "main", "article"):
            self.assertIn(required, tags)

    def test_contains_four_formulas(self) -> None:
        output = render_demo()
        for formula in ("Q = cmΔt", "Q = mq", "热效率", "混合温度"):
            self.assertIn(formula, output)

    def test_contains_example_answers(self) -> None:
        output = render_demo()
        self.assertIn("84000", output)
        self.assertIn("84.0%", output)
        self.assertIn("40.0 ℃", output)


class TestCli(unittest.TestCase):
    def setUp(self) -> None:
        self._temp = tempfile.TemporaryDirectory()
        self.tempdir = self._temp.name

    def tearDown(self) -> None:
        self._temp.cleanup()

    def _path(self, name: str) -> str:
        return os.path.join(self.tempdir, name)

    def test_q_success(self) -> None:
        code, stdout, stderr = _run_main(
            ["q", "--mass", "2", "--specific", "4200", "--delta", "10"]
        )
        self.assertEqual(code, 0)
        self.assertIn("Q = 84000 J", stdout)
        self.assertIn("84.0 kJ", stdout)
        self.assertEqual(stderr, "")

    def test_fuel_success(self) -> None:
        code, stdout, _ = _run_main(["fuel", "--mass", "0.5", "--value", "46000000"])
        self.assertEqual(code, 0)
        self.assertIn("Q = 23000000 J", stdout)
        self.assertIn("23000.0 kJ", stdout)

    def test_efficiency_success(self) -> None:
        code, stdout, _ = _run_main(["efficiency", "--useful", "84000", "--total", "100000"])
        self.assertEqual(code, 0)
        self.assertIn("84.0%", stdout)

    def test_mix_success(self) -> None:
        code, stdout, _ = _run_main(["mix", "--m1", "1", "--t1", "80", "--m2", "2", "--t2", "20"])
        self.assertEqual(code, 0)
        self.assertIn("40.0 ℃", stdout)

    def test_q_zero_mass_returns_two(self) -> None:
        code, _, stderr = _run_main(
            ["q", "--mass", "0", "--specific", "4200", "--delta", "10"]
        )
        self.assertEqual(code, 2)
        self.assertIn("错误：", stderr)

    def test_q_nan_returns_two(self) -> None:
        code, _, stderr = _run_main(
            ["q", "--mass", "nan", "--specific", "4200", "--delta", "10"]
        )
        self.assertEqual(code, 2)
        self.assertIn("错误：", stderr)

    def test_q_inf_returns_two(self) -> None:
        code, _, stderr = _run_main(
            ["q", "--mass", "inf", "--specific", "4200", "--delta", "10"]
        )
        self.assertEqual(code, 2)
        self.assertIn("错误：", stderr)

    def test_efficiency_invalid_returns_two(self) -> None:
        code, _, stderr = _run_main(
            ["efficiency", "--useful", "120", "--total", "100"]
        )
        self.assertEqual(code, 2)
        self.assertIn("错误：", stderr)

    def test_mix_out_of_range_returns_two(self) -> None:
        code, _, stderr = _run_main(
            ["mix", "--m1", "1", "--t1", "1200", "--m2", "2", "--t2", "20"]
        )
        self.assertEqual(code, 2)
        self.assertIn("错误：", stderr)

    def test_sheet_writes_file(self) -> None:
        path = self._path("sheet.html")
        code, stdout, _ = _run_main(["sheet", "--count", "8", "--seed", "1", "-o", path])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(path))
        self.assertIn("已生成练习纸", stdout)
        with open(path, encoding="utf-8") as handle:
            content = handle.read()
        self.assertEqual(content.count('<li class="question">'), 8)
        self.assertIn("html", _parse_tags(content))

    def test_sheet_answers_flag(self) -> None:
        path = self._path("sheet_answers.html")
        code, _, _ = _run_main(
            ["sheet", "--count", "4", "--seed", "2", "-o", path, "--answers"]
        )
        self.assertEqual(code, 0)
        with open(path, encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("参考答案", content)

    def test_sheet_seed_reproducible(self) -> None:
        first = self._path("first.html")
        second = self._path("second.html")
        _run_main(["sheet", "--count", "8", "--seed", "7", "-o", first])
        _run_main(["sheet", "--count", "8", "--seed", "7", "-o", second])
        with open(first, encoding="utf-8") as handle:
            first_text = handle.read()
        with open(second, encoding="utf-8") as handle:
            second_text = handle.read()
        self.assertEqual(first_text, second_text)

    def test_sheet_invalid_count_returns_two(self) -> None:
        path = self._path("bad.html")
        code, _, stderr = _run_main(["sheet", "--count", "0", "-o", path])
        self.assertEqual(code, 2)
        self.assertIn("错误：", stderr)
        self.assertFalse(os.path.exists(path))

    def test_sheet_empty_output_returns_two(self) -> None:
        code, _, stderr = _run_main(["sheet", "--count", "1", "-o", ""])
        self.assertEqual(code, 2)
        self.assertIn("错误：", stderr)

    def test_sheet_bad_directory_returns_two(self) -> None:
        path = os.path.join(self.tempdir, "missing", "sheet.html")
        code, _, stderr = _run_main(["sheet", "--count", "1", "-o", path])
        self.assertEqual(code, 2)
        self.assertIn("错误：", stderr)

    def test_sheet_output_is_directory_returns_two(self) -> None:
        code, _, stderr = _run_main(["sheet", "--count", "1", "-o", self.tempdir])
        self.assertEqual(code, 2)
        self.assertIn("错误：", stderr)

    def test_demo_writes_file(self) -> None:
        path = self._path("demo.html")
        code, stdout, _ = _run_main(["demo", "-o", path])
        self.assertEqual(code, 0)
        self.assertTrue(os.path.exists(path))
        self.assertIn("已生成公式卡片页", stdout)
        with open(path, encoding="utf-8") as handle:
            content = handle.read()
        self.assertIn("Q = cmΔt", content)

    def test_demo_bad_path_returns_two(self) -> None:
        path = os.path.join(self.tempdir, "missing", "demo.html")
        code, _, stderr = _run_main(["demo", "-o", path])
        self.assertEqual(code, 2)
        self.assertIn("错误：", stderr)

    def test_missing_command_exits(self) -> None:
        with self.assertRaises(SystemExit) as context:
            with contextlib.redirect_stderr(io.StringIO()):
                main([])
        self.assertEqual(context.exception.code, 2)

    def test_unknown_command_exits(self) -> None:
        with self.assertRaises(SystemExit) as context:
            with contextlib.redirect_stderr(io.StringIO()):
                main(["unknown"])
        self.assertEqual(context.exception.code, 2)

    def test_non_numeric_argument_exits(self) -> None:
        with self.assertRaises(SystemExit) as context:
            with contextlib.redirect_stderr(io.StringIO()):
                main(["q", "--mass", "abc", "--specific", "4200", "--delta", "10"])
        self.assertEqual(context.exception.code, 2)

    def test_missing_required_option_exits(self) -> None:
        with self.assertRaises(SystemExit) as context:
            with contextlib.redirect_stderr(io.StringIO()):
                main(["q", "--mass", "2"])
        self.assertEqual(context.exception.code, 2)

    def test_top_level_help_exits_zero(self) -> None:
        with self.assertRaises(SystemExit) as context:
            with contextlib.redirect_stdout(io.StringIO()):
                main(["--help"])
        self.assertEqual(context.exception.code, 0)

    def test_subcommand_help_exits_zero(self) -> None:
        for command in ("q", "fuel", "efficiency", "mix", "sheet", "demo"):
            with self.subTest(command=command):
                with self.assertRaises(SystemExit) as context:
                    with contextlib.redirect_stdout(io.StringIO()):
                        main([command, "--help"])
                self.assertEqual(context.exception.code, 0)


class TestPackage(unittest.TestCase):
    def test_version(self) -> None:
        self.assertEqual(__version__, "0.1.0")

    def test_api_callables(self) -> None:
        for function in (
            heat_absorbed,
            fuel_heat,
            efficiency,
            mix_temperature,
            make_questions,
            render_sheet,
            render_demo,
        ):
            self.assertTrue(callable(function))

    def test_question_is_frozen(self) -> None:
        question = Question(index=1, kind="吸热", prompt="题目", answer="答案")
        with self.assertRaises(FrozenInstanceError):
            question.kind = "其他"


if __name__ == "__main__":
    unittest.main()
