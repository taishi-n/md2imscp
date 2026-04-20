# AGENTS.md

## Purpose

This repository provides `md2imscp`, a Python CLI that converts Markdown assessments into IMS Content Packaging zip files.

The current public entrypoints are:

- `md2imscp build input.md -o out.zip [--stem NAME] [--asset-root DIR] [--validate]`
- `md2imscp dump-ast input.md`
- `md2imscp validate out.zip`

The normative specification is [`SPEC.md`](./SPEC.md). `README.md` is the user-facing introduction. `docs/` contains implementation-oriented reference material.

## Repository Map

- `md2imscp/cli.py`
  - Thin `argparse` wrapper around core functions.
- `md2imscp/core.py`
  - Main implementation. Parsing, normalization, HTML rendering, XML generation, zip writing, and validation all live here.
- `md2imscp/resources/imscp_v1p1.xsd`
  - Bundled schema used during manifest validation.
- `tests/test_build.py`
  - Current integration-style regression tests.
- `examples/sample_assessment.md`
  - Main sample input fixture.
- `examples/exportAssessment.zip`
  - Compatibility reference output.
- `docs/codebase.md`
  - Short implementation map.
- `docs/input-format.md`
  - Input-format summary, not normative.
- `docs/testing.md`
  - Current testing guidance.

## Environment And Commands

Preferred setup:

```bash
uv sync
```

Run the CLI:

```bash
uv run md2imscp build examples/sample_assessment.md -o /tmp/out.zip --validate
uv run md2imscp dump-ast examples/sample_assessment.md
uv run md2imscp validate /tmp/out.zip
```

Run tests:

```bash
python3 -m unittest discover -s tests -q
```

External tools the code expects:

- `pandoc` for Markdown -> Pandoc JSON AST conversion
- `xmllint` for manifest schema validation
- a locally available `xml.xsd` in one of the hard-coded paths checked by `find_local_xml_schema(...)`

Python packaging is intentionally minimal:

- runtime dependencies in `pyproject.toml`: none
- build backend: `setuptools`
- test framework: stdlib `unittest`, not `pytest`

## Architecture Notes

The code path for `build` is:

1. `build_package(...)`
2. `run_pandoc_json(...)`
3. `parse_meta_map(...)`
4. `build_assessment_model(...)`
5. `parse_sections(...)`
6. `build_item(...)`
7. `build_package_files(...)`
8. `build_manifest_xml(...)` and `build_assessment_xml(...)`
9. `write_zip(...)`
10. optional `validate_package(...)`

Key internal models are dataclasses in `core.py`:

- `Assessment`
- `Section`
- `Item`
- `ChoiceOption`
- `ClozeBlank`
- `MatchingPrompt`
- `MatchingTarget`
- `AssetRecord`
- `RawSection`
- `RawItem`

Important implementation boundaries:

- `cli.py` should stay thin.
- Most feature work lands in `core.py`.
- HTML generation is centralized in `HtmlRenderer`.
- CDATA handling is centralized in `CDataSerializer`.
- asset path rewriting is centralized in `AssetManager`.

## Supported Input And Behavior

Supported item types:

- `single-choice`
- `multiple-choice`
- `true-false`
- `numeric`
- `cloze`
- `matching`

High-level parsing rules:

- `##` starts a section.
- `###` starts an item.
- no `##` means an implicit `Default` section is created.
- YAML front matter drives assessment-level metadata.
- item heading attributes provide `type`, `shuffle`, `answer`, and `answers`.
- feedback uses fenced divs with `.feedback` and `kind="correct"` or `kind="incorrect"`.

Output shape:

- a zip containing `imsmanifest.xml`
- one QTI XML file named `<stem>.xml`
- optional `assets/` entries for rewritten relative references

The spec source of truth for expected behavior is `SPEC.md`, but the current implementation also has practical constraints listed below.

## Testing And Verification Expectations

When changing behavior, prefer all of the following:

```bash
python3 -m unittest discover -s tests -q
uv run md2imscp build examples/sample_assessment.md -o /tmp/sample.zip --validate
unzip -l /tmp/sample.zip
```

If the change touches rendering or XML structure, inspect the generated XML directly:

```bash
unzip -p /tmp/sample.zip sample.xml | sed -n '1,240p'
```

Current automated coverage is narrow. It mainly verifies:

- sample package builds
- validation passes
- core XML fragments appear
- some assessment metadata is propagated
- legacy `true-false` with `answer=` still works

If you add or change a question type, asset handling, raw HTML, or validation behavior, extend `tests/test_build.py` or add new `unittest` cases.

## Known Constraints And Pitfalls

- `md2imscp/core.py` is the center of gravity; avoid accidental regressions when editing multiple behaviors at once.
- Task-list parsing depends on Pandoc emitting `☐` and `☒`.
- `cloze` blanks are parsed from rendered HTML text using `[[...]]` regex matching.
- Unsupported Pandoc block or inline types raise `InputValidationError`.
- raw HTML is rejected unless `allow_raw_html: true`.
- matching items require a 2-column table.
- option identifiers currently support only 26 choices because `option_ident(...)` stops at `Z`.
- manifest validation depends on local system schema availability, not just the bundled XSD.
- scoring logic is structurally incomplete: current `setvar` values are placeholders (`0` / `0.0`), so be careful when claiming scoring correctness.

## Change Guidance

- Keep user-facing behavior aligned with `SPEC.md`.
- Keep `README.md` focused on setup and usage; keep normative detail in `SPEC.md`.
- If behavior changes, update the relevant documentation alongside code:
  - `SPEC.md` for normative behavior
  - `README.md` for setup or user-facing examples
  - `docs/` for implementation notes
- Prefer small, targeted changes in `core.py`; many functions are tightly coupled.
- Do not add new third-party Python dependencies casually. The project currently has none.
- Preserve deterministic outputs where possible. `write_zip(...)` intentionally fixes timestamps and sorts entries.

## Safe Starting Points For Common Tasks

Add or modify a question type:

- inspect `SUPPORTED_ITEM_TYPES`, `QMD_ITEM_TYPES`, `ITEM_TYPE_METADATA`
- update `build_item(...)`
- update the XML builder branch in `build_item_xml(...)`
- add tests and update `SPEC.md` if behavior changes

Change input parsing:

- inspect `parse_sections(...)`, `build_item(...)`, and helpers such as `extract_task_choices(...)`, `extract_matching(...)`, `parse_cloze_prompt(...)`, and `parse_answer_list(...)`

Change HTML/XML rendering:

- inspect `HtmlRenderer`
- inspect `build_manifest_xml(...)`, `build_assessment_xml(...)`, and the per-item XML builders

Change validation behavior:

- inspect `validate_package(...)`
- inspect `run_manifest_schema_validation(...)`, `prepare_manifest_schema(...)`, and `find_local_xml_schema(...)`
