from __future__ import annotations

import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path

from md2imscp.core import build_package, validate_package


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


if __name__ == "__main__":
    unittest.main()
