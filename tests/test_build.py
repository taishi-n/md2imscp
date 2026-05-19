from __future__ import annotations

import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path

from md2imscp.core import InputValidationError, build_package, validate_package


PROJECT_ROOT = Path(__file__).resolve().parent.parent


class BuildPackageTests(unittest.TestCase):
    def test_builds_and_validates_sample_package(self) -> None:
        sample = PROJECT_ROOT / "examples" / "sample_assessment.md"
        with tempfile.TemporaryDirectory() as temp_dir_name:
            output = Path(temp_dir_name) / "sample.zip"
            build_package(sample, output, run_validation=True)

            self.assertTrue(output.exists())
            validate_package(output)

            with zipfile.ZipFile(output) as archive:
                names = set(archive.namelist())
                self.assertIn("imsmanifest.xml", names)
                self.assertIn("sample.xml", names)

                xml_text = archive.read("sample.xml").decode("utf-8")
                self.assertIn("<code>cout</code>", xml_text)
                self.assertIn("<strong>どれ</strong>", xml_text)
                self.assertIn("<strong>正解</strong>です。<code>int</code> は C++ の基本的な整数型である。", xml_text)
                self.assertIn("2026-04-20T09:00:00+09:00", xml_text)
                self.assertIn("PT30M", xml_text)
                self.assertIn('<mattext charset="ascii-us" texttype="text/plain" xml:space="default"><![CDATA[True]]></mattext>', xml_text)

    def test_true_false_answer_attribute_still_works(self) -> None:
        markdown = textwrap.dedent(
            """\
            ---
            title: Legacy True False
            ---

            ### 問題 1 {type="true-false" answer="false"}
            C++ は大文字小文字を区別しない。
            """
        )
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            source = temp_dir / "legacy.md"
            output = temp_dir / "legacy.zip"
            source.write_text(markdown, encoding="utf-8")

            build_package(source, output, run_validation=True)

            with zipfile.ZipFile(output) as archive:
                xml_text = archive.read("legacy.xml").decode("utf-8")
                self.assertIn("True", xml_text)
                self.assertIn("False", xml_text)
                self.assertIn(
                    '<decvar defaultval="0.0" maxvalue="1.0" minvalue="0.0" varname="SCORE" vartype="Decimal" />',
                    xml_text,
                )
                self.assertIn('<setvar action="Add" varname="SCORE">1.0</setvar>', xml_text)

    def test_item_limit_keeps_only_first_n_items(self) -> None:
        markdown = textwrap.dedent(
            """\
            ---
            title: Limited Assessment
            ---

            ## Section A

            ### 問題 1 {type="true-false" answer="true"}
            A

            ### 問題 2 {type="true-false" answer="false"}
            B

            ## Section B

            ### 問題 3 {type="true-false" answer="true"}
            C
            """
        )
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            source = temp_dir / "limited.md"
            output = temp_dir / "limited.zip"
            source.write_text(markdown, encoding="utf-8")

            build_package(source, output, item_limit=2, run_validation=True)

            with zipfile.ZipFile(output) as archive:
                xml_text = archive.read("limited.xml").decode("utf-8")
                self.assertIn('<section ident=', xml_text)
                self.assertIn('title="Section A"', xml_text)
                self.assertIn('title="問題 1"', xml_text)
                self.assertIn('title="問題 2"', xml_text)
                self.assertNotIn('title="問題 3"', xml_text)
                self.assertNotIn('title="Section B"', xml_text)

    def test_shuffle_items_with_seed_reorders_and_limits_across_sections(self) -> None:
        markdown = textwrap.dedent(
            """\
            ---
            title: Shuffled Assessment
            ---

            ## First

            ### Alpha {type="true-false" answer="true"}
            A

            ### Beta {type="true-false" answer="false"}
            B

            ## Second

            ### Gamma {type="true-false" answer="true"}
            C

            ### Delta {type="true-false" answer="false"}
            D
            """
        )
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            source = temp_dir / "shuffled.md"
            output = temp_dir / "shuffled.zip"
            source.write_text(markdown, encoding="utf-8")

            build_package(source, output, shuffle_items=True, shuffle_seed=7, item_limit=2, run_validation=True)

            with zipfile.ZipFile(output) as archive:
                xml_text = archive.read("shuffled.xml").decode("utf-8")
                alpha_pos = xml_text.find('title="Alpha"')
                beta_pos = xml_text.find('title="Beta"')
                gamma_pos = xml_text.find('title="Gamma"')
                delta_pos = xml_text.find('title="Delta"')
                self.assertEqual(-1, alpha_pos)
                self.assertNotEqual(-1, beta_pos)
                self.assertEqual(-1, gamma_pos)
                self.assertNotEqual(-1, delta_pos)
                self.assertLess(delta_pos, beta_pos)

    def test_horizontal_rule_mode_generates_markdown_and_builds_package(self) -> None:
        sample = PROJECT_ROOT / "examples" / "horizontal_rule_single_choice_bank.md"
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            output = temp_dir / "bank.zip"
            generated = temp_dir / "generated.md"

            build_package(
                sample,
                output,
                horizontal_rule_item_type="single-choice",
                shuffle_items=True,
                shuffle_seed=1,
                item_limit=2,
                generated_markdown_out=generated,
                run_validation=True,
            )

            generated_text = generated.read_text(encoding="utf-8")
            self.assertIn('### 問題 1 {type="single-choice"}', generated_text)
            self.assertIn('### 問題 2 {type="single-choice"}', generated_text)
            self.assertIn("**整数型** をひとつ選べ。", generated_text)
            self.assertIn("`#include <iostream>` の説明として正しいものを選べ。", generated_text)
            self.assertNotIn("`cout` で改行するものを選べ。", generated_text)

            with zipfile.ZipFile(output) as archive:
                xml_text = archive.read("cpp-bank.xml").decode("utf-8")
                self.assertIn("整数型", xml_text)
                self.assertIn("#include &lt;iostream&gt;", xml_text)
                self.assertNotIn("cout</code> で改行するものを選べ", xml_text)

    def test_horizontal_rule_bank_examples_build_for_each_supported_type(self) -> None:
        cases = [
            ("horizontal_rule_single_choice_bank.md", "single-choice", "cpp-bank.xml"),
            ("horizontal_rule_multiple_choice_bank.md", "multiple-choice", "cpp-multiple-choice-bank.xml"),
            ("horizontal_rule_true_false_bank.md", "true-false", "cpp-true-false-bank.xml"),
            ("horizontal_rule_cloze_bank.md", "cloze", "cpp-cloze-bank.xml"),
            ("horizontal_rule_matching_bank.md", "matching", "cpp-matching-bank.xml"),
        ]
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            for filename, item_type, xml_name in cases:
                source = PROJECT_ROOT / "examples" / filename
                output = temp_dir / f"{source.stem}.zip"
                build_package(
                    source,
                    output,
                    horizontal_rule_item_type=item_type,
                    shuffle_items=True,
                    shuffle_seed=3,
                    item_limit=2,
                    run_validation=True,
                )
                with zipfile.ZipFile(output) as archive:
                    self.assertIn("imsmanifest.xml", archive.namelist())
                    self.assertIn(xml_name, archive.namelist())

    def test_shuffle_multiple_choice_options_reorders_choice_output(self) -> None:
        markdown = textwrap.dedent(
            """\
            ---
            title: Choice Shuffle
            ---

            ### 問題 1 {type="multiple-choice"}
            正しいものをすべて選べ。

            - [x] Alpha
            - [ ] Beta
            - [x] Gamma
            """
        )
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            source = temp_dir / "choice-shuffle.md"
            output = temp_dir / "choice-shuffle.zip"
            source.write_text(markdown, encoding="utf-8")

            build_package(
                source,
                output,
                shuffle_multiple_choice_options=True,
                shuffle_seed=11,
                run_validation=True,
            )

            with zipfile.ZipFile(output) as archive:
                xml_text = archive.read("choice-shuffle.xml").decode("utf-8")
                alpha_pos = xml_text.find("<![CDATA[Alpha]]>")
                beta_pos = xml_text.find("<![CDATA[Beta]]>")
                gamma_pos = xml_text.find("<![CDATA[Gamma]]>")
                self.assertNotEqual(-1, alpha_pos)
                self.assertNotEqual(-1, beta_pos)
                self.assertNotEqual(-1, gamma_pos)
                self.assertLess(alpha_pos, gamma_pos)
                self.assertLess(gamma_pos, beta_pos)
                self.assertIn(
                    '<decvar defaultval="0.0" maxvalue="0.0" minvalue="0.0" varname="SCORE" vartype="Decimal" />',
                    xml_text,
                )
                self.assertIn('<setvar action="Add" varname="SCORE">0.0</setvar>', xml_text)

    def test_default_scores_are_one_point_except_multiple_choice(self) -> None:
        markdown = textwrap.dedent(
            """\
            ---
            title: Score Defaults
            ---

            ### Single {type="single-choice"}
            選べ。

            - [x] A
            - [ ] B

            ### Numeric {type="numeric" answer="1"}
            入力せよ。

            ### Cloze {type="cloze"}
            `[[A]]` と `[[B]]`

            ### Matching {type="matching"}
            対応づけよ。

            | 項目 | 対応 |
            | --- | --- |
            | A | 1 |
            | B | 2 |
            """
        )
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            source = temp_dir / "score-defaults.md"
            output = temp_dir / "score-defaults.zip"
            source.write_text(markdown, encoding="utf-8")

            build_package(source, output, run_validation=True)

            with zipfile.ZipFile(output) as archive:
                xml_text = archive.read("score-defaults.xml").decode("utf-8")
                self.assertIn(
                    '<decvar defaultval="0.0" maxvalue="1.0" minvalue="0.0" varname="SCORE" vartype="Decimal" />',
                    xml_text,
                )
                self.assertIn('<setvar action="Add" varname="SCORE">1.0</setvar>', xml_text)
                self.assertIn('<setvar action="Add" varname="SCORE">1</setvar>', xml_text)
                self.assertIn('<setvar action="Add" varname="SCORE">0.5</setvar>', xml_text)

    def test_preamble_blocks_after_front_matter_are_not_emitted(self) -> None:
        markdown = textwrap.dedent(
            """\
            ---
            title: Preamble Omitted
            ---

            この段落は section の説明に出てはいけない。

            ### 問題 1 {type="true-false" answer="true"}
            設問本文。
            """
        )
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            source = temp_dir / "preamble.md"
            output = temp_dir / "preamble.zip"
            source.write_text(markdown, encoding="utf-8")

            build_package(source, output, run_validation=True)

            with zipfile.ZipFile(output) as archive:
                xml_text = archive.read("preamble.xml").decode("utf-8")
                self.assertIn("設問本文。", xml_text)
                self.assertNotIn("この段落は section の説明に出てはいけない。", xml_text)

    def test_question_layout_metadata_accepts_documented_values(self) -> None:
        cases = [
            ("I", "question-layout-i.xml"),
            ("S", "question-layout-s.xml"),
            ("A", "question-layout-a.xml"),
        ]
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            for question_layout, xml_name in cases:
                source = temp_dir / f"{question_layout}.md"
                output = temp_dir / f"{question_layout}.zip"
                markdown = textwrap.dedent(
                    f"""\
                    ---
                    title: Question Layout
                    stem: {xml_name.removesuffix(".xml")}
                    question_layout: {question_layout}
                    ---

                    ### 問題 1 {{type="true-false" answer="true"}}
                    設問本文。
                    """
                )
                source.write_text(markdown, encoding="utf-8")

                build_package(source, output, run_validation=True)

                with zipfile.ZipFile(output) as archive:
                    xml_text = archive.read(xml_name).decode("utf-8")
                    self.assertIn("<fieldlabel>QUESTION_LAYOUT</fieldlabel>", xml_text)
                    self.assertIn(f"<fieldentry>{question_layout}</fieldentry>", xml_text)

    def test_question_layout_metadata_rejects_unknown_value(self) -> None:
        markdown = textwrap.dedent(
            """\
            ---
            title: Bad Question Layout
            question_layout: X
            ---

            ### 問題 1 {type="true-false" answer="true"}
            設問本文。
            """
        )
        with tempfile.TemporaryDirectory() as temp_dir_name:
            temp_dir = Path(temp_dir_name)
            source = temp_dir / "bad-question-layout.md"
            output = temp_dir / "bad-question-layout.zip"
            source.write_text(markdown, encoding="utf-8")

            with self.assertRaises(InputValidationError):
                build_package(source, output, run_validation=True)

if __name__ == "__main__":
    unittest.main()
