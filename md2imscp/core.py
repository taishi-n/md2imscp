from __future__ import annotations

import copy
import hashlib
import html
import importlib.resources
import json
import re
import subprocess
import tempfile
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
import xml.etree.ElementTree as ET

XML_NS = "http://www.w3.org/XML/1998/namespace"
IMSCP_NS = "http://www.imsglobal.org/xsd/imscp_v1p1"
XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"

ET.register_namespace("", IMSCP_NS)
ET.register_namespace("xsi", XSI_NS)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

ASSESSMENT_METADATA_DEFAULTS: list[tuple[str, str]] = [
    ("AUTHORS", ""),
    ("CREATOR", ""),
    ("SHOW_CREATOR", "True"),
    ("SCALENAME", "STRONGLY_AGREE"),
    ("EDIT_AUTHORS", "True"),
    ("EDIT_DESCRIPTION", "True"),
    ("ATTACHMENT", ""),
    ("DISPLAY_TEMPLATE", "True"),
    ("START_DATE", ""),
    ("END_DATE", ""),
    ("RETRACT_DATE", ""),
    ("CONSIDER_START_DATE", "False"),
    ("CONSIDER_END_DATE", "False"),
    ("CONSIDER_RETRACT_DATE", "False"),
    ("EDIT_END_DATE", "True"),
    ("EDIT_RETRACT_DATE", "True"),
    ("ASSESSMENT_RELEASED_TO", ""),
    ("EDIT_PUBLISH_ANONYMOUS", "True"),
    ("EDIT_AUTHENTICATED_USERS", "True"),
    ("ALLOW_IP", ""),
    ("CONSIDER_ALLOW_IP", "False"),
    ("CONSIDER_USERID", "False"),
    ("PASSWORD", ""),
    ("EDIT_ALLOW_IP", "True"),
    ("EDIT_USERID", "True"),
    ("REQUIRE_LOCKED_BROWSER", "False"),
    ("EXIT_PASSWARD", ""),
    ("CONSIDER_DURATION", "False"),
    ("AUTO_SUBMIT", "True"),
    ("EDIT_DURATION", "True"),
    ("EDIT_AUTO_SUBMIT", "True"),
    ("NAVIGATION", "RANDOM"),
    ("QUESTION_LAYOUT", "I"),
    ("QUESTION_NUMBERING", "CONTINUOUS"),
    ("EDIT_NAVIGATION", "True"),
    ("EDIT_QUESTION_LAYOUT", "True"),
    ("EDIT_QUESTION_NUMBERING", "True"),
    ("MARK_FOR_REVIEW", "False"),
    ("LATE_HANDLING", "True"),
    ("MAX_ATTEMPTS", "1"),
    ("EDIT_LATE_HANDLING", "True"),
    ("EDIT_MAX_ATTEMPTS", "True"),
    ("AUTO_SAVE", "False"),
    ("EDIT_AUTO_SAVE", "True"),
    ("EDIT_ASSESSFEEDBACK", "True"),
    ("SUBMISSION_MESSAGE", ""),
    ("FINISH_URL", ""),
    ("EDIT_FINISH_URL", "True"),
    ("FEEDBACK_DELIVERY", "NONE"),
    ("FEEDBACK_COMPONENT_OPTION", "SELECT_COMPONENTS"),
    ("FEEDBACK_AUTHORING", "QUESTION"),
    ("FEEDBACK_DELIVERY_DATE", ""),
    ("FEEDBACK_DELIVERY_END_DATE", ""),
    ("EDIT_FEEDBACK_DELIVERY", "True"),
    ("EDIT_FEEDBACK_COMPONENTS", "True"),
    ("FEEDBACK_SHOW_CORRECT_RESPONSE", "False"),
    ("FEEDBACK_SHOW_STUDENT_SCORE", "False"),
    ("FEEDBACK_SHOW_STUDENT_QUESTIONSCORE", "False"),
    ("FEEDBACK_SHOW_ITEM_LEVEL", "False"),
    ("FEEDBACK_SHOW_SELECTION_LEVEL", "False"),
    ("FEEDBACK_SHOW_GRADER_COMMENT", "False"),
    ("FEEDBACK_SHOW_STATS", "False"),
    ("FEEDBACK_SHOW_QUESTION", "True"),
    ("FEEDBACK_SHOW_RESPONSE", "False"),
    ("ANONYMOUS_GRADING", "False"),
    ("GRADE_SCORE", "HIGHEST_SCORE"),
    ("GRADEBOOK_OPTIONS", "NONE"),
    ("EDIT_GRADEBOOK_OPTIONS", "True"),
    ("EDIT_ANONYMOUS_GRADING", "True"),
    ("EDIT_GRADE_SCORE", "True"),
    ("BGCOLOR", ""),
    ("BGIMG", ""),
    ("EDIT_BGCOLOR", "True"),
    ("EDIT_BGIMG", "True"),
    ("EDIT_ASSESSMENT_METADATA", "True"),
    ("EDIT_COLLECT_SECTION_METADATA", "True"),
    ("EDIT_COLLECT_ITEM_METADATA", "True"),
    ("ASSESSMENT_KEYWORDS", ""),
    ("ASSESSMENT_OBJECTIVES", ""),
    ("ASSESSMENT_RUBRICS", ""),
    ("COLLECT_SECTION_METADATA", "False"),
    ("COLLECT_ITEM_METADATA", ""),
    ("LAST_MODIFIED_ON", ""),
    ("LAST_MODIFIED_BY", ""),
    ("templateInfo_isInstructorEditable", "false"),
    ("assessmentAuthor_isInstructorEditable", "true"),
    ("assessmentCreator_isInstructorEditable", ""),
    ("description_isInstructorEditable", "true"),
    ("dueDate_isInstructorEditable", "true"),
    ("retractDate_isInstructorEditable", "true"),
    ("anonymousRelease_isInstructorEditable", "true"),
    ("authenticatedRelease_isInstructorEditable", "true"),
    ("ipAccessType_isInstructorEditable", "true"),
    ("passwordRequired_isInstructorEditable", "true"),
    ("lockedBrowser_isInstructorEditable", "true"),
    ("timedAssessment_isInstructorEditable", "true"),
    ("timedAssessmentAutoSubmit_isInstructorEditable", "true"),
    ("itemAccessType_isInstructorEditable", "true"),
    ("displayChunking_isInstructorEditable", "true"),
    ("displayNumbering_isInstructorEditable", "true"),
    ("displayScores_isInstructorEditable", "true"),
    ("submissionModel_isInstructorEditable", "true"),
    ("lateHandling_isInstructorEditable", "true"),
    ("instructorNotification_isInstructorEditable", "True"),
    ("automaticSubmission_isInstructorEditable", ""),
    ("autoSave_isInstructorEditable", ""),
    ("submissionMessage_isInstructorEditable", "true"),
    ("finalPageURL_isInstructorEditable", "true"),
    ("feedbackType_isInstructorEditable", "true"),
    ("feedbackComponents_isInstructorEditable", "true"),
    ("testeeIdentity_isInstructorEditable", "true"),
    ("toGradebook_isInstructorEditable", "true"),
    ("recordedScore_isInstructorEditable", "true"),
    ("bgColor_isInstructorEditable", "true"),
    ("bgImage_isInstructorEditable", "true"),
    ("metadataAssess_isInstructorEditable", "true"),
    ("metadataParts_isInstructorEditable", ""),
    ("metadataQuestions_isInstructorEditable", "true"),
    ("honorpledge_isInstructorEditable", "true"),
]

SECTION_METADATA_DEFAULTS: list[tuple[str, str]] = [
    ("SECTION_INFORMATION", ""),
    ("SECTION_OBJECTIVE", ""),
    ("SECTION_KEYWORD", ""),
    ("SECTION_RUBRIC", ""),
    ("ATTACHMENT", ""),
    ("QUESTIONS_ORDERING", "1"),
]

ITEM_METADATA_COMMON: list[tuple[str, str]] = [
    ("TEXT_FORMAT", "HTML"),
    ("ITEM_OBJECTIVE", ""),
    ("ITEM_KEYWORD", ""),
    ("ITEM_RUBRIC", ""),
    ("ITEM_TAGS", ""),
    ("ATTACHMENT", ""),
]

ITEM_TYPE_METADATA: dict[str, list[tuple[str, str]]] = {
    "single-choice": [
        ("hasRationale", "false"),
        ("PARTIAL_CREDIT", "FALSE"),
        ("RANDOMIZE", "false"),
    ],
    "multiple-choice": [
        ("hasRationale", "false"),
        ("RANDOMIZE", "false"),
    ],
    "true-false": [
        ("hasRationale", "false"),
    ],
    "numeric": [],
    "cloze": [
        ("MUTUALLY_EXCLUSIVE", "false"),
        ("CASE_SENSITIVE", "false"),
        ("IGNORE_SPACES", "false"),
    ],
    "matching": [],
}

QMD_ITEM_TYPES: dict[str, str] = {
    "single-choice": "Multiple Choice",
    "multiple-choice": "Multiple Correct Answer",
    "true-false": "True False",
    "numeric": "Numeric Response",
    "cloze": "Fill In the Blank",
    "matching": "Matching",
}

SUPPORTED_ITEM_TYPES = set(QMD_ITEM_TYPES)
TASK_UNCHECKED = "☐"
TASK_CHECKED = "☒"
RAW_HTML_ATTR_RE = re.compile(
    r'(?P<attr>\b(?:src|href)\s*=\s*)(?P<quote>["\'])(?P<value>[^"\']+)(?P=quote)',
    re.IGNORECASE,
)
CLOZE_RE = re.compile(r"\[\[(.+?)\]\]")


class Md2ImscpError(Exception):
    exit_code = 3


class UsageError(Md2ImscpError):
    exit_code = 1


class InputValidationError(Md2ImscpError):
    exit_code = 2


class BuildError(Md2ImscpError):
    exit_code = 3


class ValidationError(Md2ImscpError):
    exit_code = 4


@dataclass(slots=True)
class AssetRecord:
    source: Path
    href: str


@dataclass(slots=True)
class ChoiceOption:
    ident: str
    html: str
    correct: bool


@dataclass(slots=True)
class ClozeBlank:
    ident: str
    answers: list[str]


@dataclass(slots=True)
class MatchingPrompt:
    ident: str
    html: str
    target_ident: str


@dataclass(slots=True)
class MatchingTarget:
    ident: str
    html: str


@dataclass(slots=True)
class Item:
    ident: str
    title: str
    item_type: str
    prompt_html: str
    shuffle: bool = False
    correct_feedback_html: str = ""
    incorrect_feedback_html: str = ""
    choices: list[ChoiceOption] = field(default_factory=list)
    answers: list[str] = field(default_factory=list)
    cloze_segments: list[str] = field(default_factory=list)
    cloze_blanks: list[ClozeBlank] = field(default_factory=list)
    matching_prompts: list[MatchingPrompt] = field(default_factory=list)
    matching_targets: list[MatchingTarget] = field(default_factory=list)
    response_ident: str = ""


@dataclass(slots=True)
class Section:
    ident: str
    title: str
    description_html: str
    items: list[Item]


@dataclass(slots=True)
class Assessment:
    ident: str
    title: str
    stem: str
    duration: str
    metadata: dict[str, str]
    sections: list[Section]
    assets: list[AssetRecord]


@dataclass(slots=True)
class RawItem:
    ident_hint: str
    title: str
    attrs: dict[str, str]
    blocks: list[dict[str, Any]]
    section_index: int
    item_index: int


@dataclass(slots=True)
class RawSection:
    ident_hint: str
    title: str
    description_blocks: list[dict[str, Any]]
    items: list[RawItem]
    section_index: int


class AssetManager:
    def __init__(self, source_path: Path, asset_root: Path | None) -> None:
        self.source_path = source_path.resolve()
        self.asset_root = (asset_root or self.source_path.parent).resolve()
        self._records_by_source: dict[Path, AssetRecord] = {}
        self._sources_by_href: dict[str, Path] = {}

    def rewrite_reference(self, reference: str) -> str:
        parsed = urlparse(reference)
        if parsed.scheme and parsed.scheme != "file":
            return reference
        if reference.startswith("#"):
            return reference

        if parsed.scheme == "file":
            candidate = Path(parsed.path)
        else:
            candidate = Path(reference)

        source = candidate if candidate.is_absolute() else (self.asset_root / candidate)
        source = source.resolve()
        if not source.exists() or not source.is_file():
            raise InputValidationError(f"asset not found: {reference}")

        existing = self._records_by_source.get(source)
        if existing is not None:
            return existing.href

        href = self._assign_href(source)
        record = AssetRecord(source=source, href=href)
        self._records_by_source[source] = record
        self._sources_by_href[href] = source
        return href

    def records(self) -> list[AssetRecord]:
        return sorted(self._records_by_source.values(), key=lambda record: record.href)

    def _assign_href(self, source: Path) -> str:
        base_name = source.name
        href = f"assets/{base_name}"
        if href not in self._sources_by_href:
            return href

        digest = hashlib.sha1(str(source).encode("utf-8")).hexdigest()[:8]
        stem = source.stem
        suffix = source.suffix
        href = f"assets/{stem}-{digest}{suffix}"
        if href in self._sources_by_href and self._sources_by_href[href] != source:
            raise BuildError(f"could not assign a unique asset name for {source}")
        return href


class HtmlRenderer:
    def __init__(self, asset_manager: AssetManager, allow_raw_html: bool) -> None:
        self.asset_manager = asset_manager
        self.allow_raw_html = allow_raw_html

    def render_blocks(self, blocks: list[dict[str, Any]]) -> str:
        parts = [self.render_block(block) for block in blocks]
        return "\n".join(part for part in parts if part)

    def render_compact_blocks(self, blocks: list[dict[str, Any]]) -> str:
        if not blocks:
            return ""
        if len(blocks) == 1 and blocks[0]["t"] in {"Para", "Plain"}:
            return self.render_inlines(blocks[0]["c"])
        return self.render_blocks(blocks)

    def render_block(self, block: dict[str, Any]) -> str:
        block_type = block["t"]
        content = block.get("c")
        if block_type == "Para":
            return f"<p>{self.render_inlines(content)}</p>"
        if block_type == "Plain":
            return self.render_inlines(content)
        if block_type == "BulletList":
            items = "".join(f"<li>{self.render_list_item(item)}</li>" for item in content)
            return f"<ul>{items}</ul>"
        if block_type == "OrderedList":
            attrs, items = content
            start = attrs[0] if attrs and attrs[0] != 1 else None
            start_attr = f' start="{start}"' if start else ""
            rendered = "".join(f"<li>{self.render_list_item(item)}</li>" for item in items)
            return f"<ol{start_attr}>{rendered}</ol>"
        if block_type == "CodeBlock":
            _, text = content
            return f"<pre><code>{html.escape(text)}</code></pre>"
        if block_type == "Table":
            return self.render_table(block)
        if block_type == "HorizontalRule":
            return "<hr />"
        if block_type == "BlockQuote":
            return f"<blockquote>{self.render_blocks(content)}</blockquote>"
        if block_type == "Div":
            _, blocks = content
            return self.render_blocks(blocks)
        if block_type == "Header":
            level, _, inlines = content
            return f"<h{level}>{self.render_inlines(inlines)}</h{level}>"
        if block_type == "RawBlock":
            fmt, text = content
            return self.render_raw_html(fmt, text)
        raise InputValidationError(f"unsupported block type: {block_type}")

    def render_list_item(self, blocks: list[dict[str, Any]]) -> str:
        if len(blocks) == 1 and blocks[0]["t"] in {"Para", "Plain"}:
            return self.render_inlines(blocks[0]["c"])
        return self.render_blocks(blocks)

    def render_table(self, block: dict[str, Any]) -> str:
        _, _, _, table_head, table_bodies, table_foot = block["c"]
        head_rows = table_head[1]
        parts: list[str] = ["<table>"]
        if head_rows:
            parts.append("<thead>")
            for row in head_rows:
                parts.append("<tr>")
                for cell in row[1]:
                    parts.append(f"<th>{self.render_compact_blocks(cell[4])}</th>")
                parts.append("</tr>")
            parts.append("</thead>")
        parts.append("<tbody>")
        for body in table_bodies:
            for row in body[3]:
                parts.append("<tr>")
                for cell in row[1]:
                    parts.append(f"<td>{self.render_compact_blocks(cell[4])}</td>")
                parts.append("</tr>")
        parts.append("</tbody>")
        foot_rows = table_foot[1]
        if foot_rows:
            parts.append("<tfoot>")
            for row in foot_rows:
                parts.append("<tr>")
                for cell in row[1]:
                    parts.append(f"<td>{self.render_compact_blocks(cell[4])}</td>")
                parts.append("</tr>")
            parts.append("</tfoot>")
        parts.append("</table>")
        return "".join(parts)

    def render_inlines(self, inlines: list[dict[str, Any]]) -> str:
        return "".join(self.render_inline(inline) for inline in inlines)

    def render_inline(self, inline: dict[str, Any]) -> str:
        inline_type = inline["t"]
        content = inline.get("c")
        if inline_type == "Str":
            return html.escape(content)
        if inline_type == "Space":
            return " "
        if inline_type == "SoftBreak":
            return "\n"
        if inline_type == "LineBreak":
            return "<br />"
        if inline_type == "Emph":
            return f"<em>{self.render_inlines(content)}</em>"
        if inline_type == "Strong":
            return f"<strong>{self.render_inlines(content)}</strong>"
        if inline_type == "Underline":
            return f"<u>{self.render_inlines(content)}</u>"
        if inline_type == "Strikeout":
            return f"<s>{self.render_inlines(content)}</s>"
        if inline_type == "Superscript":
            return f"<sup>{self.render_inlines(content)}</sup>"
        if inline_type == "Subscript":
            return f"<sub>{self.render_inlines(content)}</sub>"
        if inline_type == "SmallCaps":
            return f"<span style=\"font-variant: small-caps;\">{self.render_inlines(content)}</span>"
        if inline_type == "Code":
            _, text = content
            return f"<code>{html.escape(text)}</code>"
        if inline_type == "Link":
            _, text_inlines, target = content
            href = self.asset_manager.rewrite_reference(target[0])
            return f'<a href="{html.escape(href, quote=True)}">{self.render_inlines(text_inlines)}</a>'
        if inline_type == "Image":
            _, alt_inlines, target = content
            src = self.asset_manager.rewrite_reference(target[0])
            alt = stringify_inlines(alt_inlines)
            return f'<img src="{html.escape(src, quote=True)}" alt="{html.escape(alt, quote=True)}" />'
        if inline_type == "Span":
            _, inner = content
            return f"<span>{self.render_inlines(inner)}</span>"
        if inline_type == "Quoted":
            quote_type, quoted_inlines = content
            open_quote, close_quote = ("“", "”") if quote_type["t"] == "DoubleQuote" else ("‘", "’")
            return f"{open_quote}{self.render_inlines(quoted_inlines)}{close_quote}"
        if inline_type == "Math":
            _, text = content
            return html.escape(text)
        if inline_type == "RawInline":
            fmt, text = content
            return self.render_raw_html(fmt, text)
        raise InputValidationError(f"unsupported inline type: {inline_type}")

    def render_raw_html(self, fmt: str, text: str) -> str:
        if fmt not in {"html", "html5"}:
            return html.escape(text)
        if not self.allow_raw_html:
            raise InputValidationError("raw HTML is disabled. Set allow_raw_html: true to enable it.")

        def replacer(match: re.Match[str]) -> str:
            reference = match.group("value")
            rewritten = self.asset_manager.rewrite_reference(reference)
            return (
                f"{match.group('attr')}{match.group('quote')}"
                f"{html.escape(rewritten, quote=True)}"
                f"{match.group('quote')}"
            )

        return RAW_HTML_ATTR_RE.sub(replacer, text)


class CDataSerializer:
    def __init__(self) -> None:
        self._payloads: dict[str, str] = {}

    def assign(self, element: ET.Element, text: str) -> None:
        token = f"__MD2KIBACO_CDATA_{len(self._payloads)}__"
        self._payloads[token] = text.replace("]]>", "]]]]><![CDATA[>")
        element.text = token

    def render(self, root: ET.Element) -> bytes:
        ET.indent(root, space="  ")
        xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
        for token, payload in self._payloads.items():
            xml_bytes = xml_bytes.replace(token.encode("utf-8"), f"<![CDATA[{payload}]]>".encode("utf-8"))
        return xml_bytes


def build_package(
    input_path: Path,
    output_path: Path,
    stem: str | None = None,
    asset_root: Path | None = None,
    run_validation: bool = False,
) -> Path:
    input_path = input_path.resolve()
    output_path = output_path.resolve()
    if not input_path.exists():
        raise UsageError(f"input file not found: {input_path}")
    if not input_path.is_file():
        raise UsageError(f"input is not a file: {input_path}")

    pandoc_doc = run_pandoc_json(input_path)
    meta = parse_meta_map(pandoc_doc["meta"])
    resolved_stem = sanitize_stem(stem or stringify_scalar(meta.get("stem")) or output_path.stem)
    assessment = build_assessment_model(
        source_path=input_path,
        meta=meta,
        blocks=pandoc_doc["blocks"],
        stem=resolved_stem,
        asset_root=asset_root,
    )
    package_files = build_package_files(assessment)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_zip(output_path, package_files)

    if run_validation:
        validate_package(output_path)

    return output_path


def dump_ast(input_path: Path) -> str:
    input_path = input_path.resolve()
    if not input_path.exists():
        raise UsageError(f"input file not found: {input_path}")
    return json.dumps(run_pandoc_json(input_path), ensure_ascii=False, indent=2)


def validate_package(package_path: Path) -> None:
    package_path = package_path.resolve()
    if not package_path.exists():
        raise UsageError(f"package not found: {package_path}")

    with zipfile.ZipFile(package_path) as archive:
        names = set(archive.namelist())
        if "imsmanifest.xml" not in names:
            raise ValidationError("imsmanifest.xml is missing from the package")

        manifest_bytes = archive.read("imsmanifest.xml")
        try:
            manifest_root = ET.fromstring(manifest_bytes)
        except ET.ParseError as exc:
            raise ValidationError(f"imsmanifest.xml is not well-formed XML: {exc}") from exc

        ns = {"imscp": IMSCP_NS}
        file_hrefs = [
            element.attrib["href"]
            for element in manifest_root.findall(".//imscp:file", ns)
            if "href" in element.attrib
        ]
        for href in file_hrefs:
            if href not in names:
                raise ValidationError(f"manifest references missing file: {href}")

        resource = manifest_root.find(".//imscp:resource", ns)
        if resource is None or "href" not in resource.attrib:
            raise ValidationError("manifest does not contain a resource href")

        qti_href = resource.attrib["href"]
        if qti_href not in names:
            raise ValidationError(f"QTI XML missing from package: {qti_href}")

        try:
            ET.fromstring(archive.read(qti_href))
        except ET.ParseError as exc:
            raise ValidationError(f"{qti_href} is not well-formed XML: {exc}") from exc

        run_manifest_schema_validation(manifest_bytes)


def run_manifest_schema_validation(manifest_bytes: bytes) -> None:
    with tempfile.TemporaryDirectory() as temp_dir_name:
        temp_dir = Path(temp_dir_name)
        manifest_path = temp_dir / "imsmanifest.xml"
        manifest_path.write_bytes(manifest_bytes)

        schema_path = prepare_manifest_schema(temp_dir)
        cmd = ["xmllint", "--noout", "--schema", str(schema_path), str(manifest_path)]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        except FileNotFoundError as exc:
            raise ValidationError("xmllint is required for schema validation but is not installed") from exc

        if proc.returncode != 0:
            message = proc.stderr.strip() or proc.stdout.strip() or "manifest schema validation failed"
            raise ValidationError(message)


def prepare_manifest_schema(temp_dir: Path) -> Path:
    with importlib.resources.as_file(
        importlib.resources.files("md2imscp").joinpath("resources", "imscp_v1p1.xsd")
    ) as bundled_schema:
        if not bundled_schema.exists():
            raise ValidationError(f"manifest schema not found: {bundled_schema}")
        schema_text = bundled_schema.read_text(encoding="utf-8")
        schema_name = bundled_schema.name

    xml_schema_path = find_local_xml_schema()
    if xml_schema_path is None:
        raise ValidationError("xml.xsd could not be found locally for manifest validation")

    schema_text = schema_text.replace(
        'schemaLocation = "http://www.w3.org/2001/03/xml.xsd"',
        f'schemaLocation = "{xml_schema_path}"',
    )

    schema_path = temp_dir / schema_name
    schema_path.write_text(schema_text, encoding="utf-8")
    return schema_path


def find_local_xml_schema() -> str | None:
    candidates = [
        Path("/Applications/Xcode.app/Contents/SystemFrameworks/SceneKit.framework/Versions/A/Resources/xml.xsd"),
        Path("/usr/share/xml/schema/xml-core/xml.xsd"),
        Path("/usr/local/share/xml/schema/xml-core/xml.xsd"),
        Path("/opt/homebrew/share/xml/schema/xml-core/xml.xsd"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def build_assessment_model(
    source_path: Path,
    meta: dict[str, Any],
    blocks: list[dict[str, Any]],
    stem: str,
    asset_root: Path | None,
) -> Assessment:
    title = stringify_scalar(meta.get("title"))
    if not title:
        raise InputValidationError("front matter must define title")

    allow_raw_html = parse_bool(meta.get("allow_raw_html"), default=False)
    asset_manager = AssetManager(source_path=source_path, asset_root=asset_root)
    renderer = HtmlRenderer(asset_manager=asset_manager, allow_raw_html=allow_raw_html)

    sections = parse_sections(blocks)
    if not sections:
        raise InputValidationError("the document does not contain any items")

    rendered_sections: list[Section] = []
    for raw_section in sections:
        if not raw_section.items:
            raise InputValidationError(f"section has no items: {raw_section.title}")
        description_html = renderer.render_blocks(raw_section.description_blocks)
        items = [build_item(raw_item, renderer) for raw_item in raw_section.items]
        rendered_sections.append(
            Section(
                ident=sanitize_ident(raw_section.ident_hint),
                title=raw_section.title,
                description_html=description_html,
                items=items,
            )
        )

    duration = stringify_scalar(meta.get("time_limit"))
    open_at = normalize_datetime(meta.get("open_at"), meta.get("timezone"))
    due_at = normalize_datetime(meta.get("due_at"), meta.get("timezone"))
    metadata = build_assessment_metadata(meta=meta, open_at=open_at, due_at=due_at, duration=duration)

    return Assessment(
        ident=sanitize_ident(stringify_scalar(meta.get("ident")) or f"assessment-{stem}"),
        title=title,
        stem=stem,
        duration=duration,
        metadata=metadata,
        sections=rendered_sections,
        assets=asset_manager.records(),
    )


def parse_sections(blocks: list[dict[str, Any]]) -> list[RawSection]:
    sections: list[RawSection] = []
    preamble_blocks: list[dict[str, Any]] = []
    current_section: RawSection | None = None
    current_item: RawItem | None = None
    section_counter = 0
    item_counter = 0

    def flush_item() -> None:
        nonlocal current_item
        if current_item is not None:
            if current_section is None:
                raise BuildError("internal error: item without section")
            current_section.items.append(current_item)
            current_item = None

    def start_default_section() -> RawSection:
        nonlocal section_counter
        section_counter += 1
        return RawSection(
            ident_hint=f"section-{section_counter:02d}",
            title="Default",
            description_blocks=[],
            items=[],
            section_index=section_counter,
        )

    for block in blocks:
        if block["t"] == "Header":
            level, attrs, inlines = block["c"]
            title = stringify_inlines(inlines)
            attr_id = attrs[0]

            if level == 2:
                flush_item()
                if current_section is not None:
                    sections.append(current_section)
                current_section = RawSection(
                    ident_hint=attr_id or f"section-{section_counter + 1:02d}",
                    title=title,
                    description_blocks=preamble_blocks if not sections and current_section is None else [],
                    items=[],
                    section_index=section_counter + 1,
                )
                preamble_blocks = []
                section_counter = current_section.section_index
                item_counter = 0
                continue

            if level == 3:
                if current_section is None:
                    current_section = start_default_section()
                    current_section.description_blocks = preamble_blocks
                    preamble_blocks = []
                flush_item()
                item_counter += 1
                current_item = RawItem(
                    ident_hint=attr_id or f"item-{current_section.section_index:02d}-{item_counter:03d}",
                    title=title,
                    attrs=dict(attrs[2]),
                    blocks=[],
                    section_index=current_section.section_index,
                    item_index=item_counter,
                )
                continue

        if current_item is not None:
            current_item.blocks.append(block)
        elif current_section is not None:
            current_section.description_blocks.append(block)
        else:
            preamble_blocks.append(block)

    flush_item()
    if current_section is not None:
        sections.append(current_section)

    return sections


def build_item(raw_item: RawItem, renderer: HtmlRenderer) -> Item:
    item_type = raw_item.attrs.get("type")
    if not item_type:
        raise InputValidationError(f"item is missing type: {raw_item.title}")
    if item_type not in SUPPORTED_ITEM_TYPES:
        raise InputValidationError(f"unsupported item type {item_type!r} in {raw_item.title}")

    body_blocks, correct_feedback_blocks, incorrect_feedback_blocks = split_feedback_blocks(raw_item.blocks)
    ident = sanitize_ident(raw_item.ident_hint)
    title = raw_item.title or QMD_ITEM_TYPES[item_type]
    shuffle = parse_bool(raw_item.attrs.get("shuffle"), default=False)
    correct_feedback_html = renderer.render_blocks(correct_feedback_blocks)
    incorrect_feedback_html = renderer.render_blocks(incorrect_feedback_blocks)

    if item_type == "single-choice":
        prompt_blocks, choices = extract_task_choices(body_blocks, renderer, allow_multiple_correct=False, title=title)
        return Item(
            ident=ident,
            title=title,
            item_type=item_type,
            prompt_html=renderer.render_blocks(prompt_blocks),
            choices=choices,
            shuffle=shuffle,
            correct_feedback_html=correct_feedback_html,
            incorrect_feedback_html=incorrect_feedback_html,
            response_ident="MCSC",
        )

    if item_type == "multiple-choice":
        prompt_blocks, choices = extract_task_choices(body_blocks, renderer, allow_multiple_correct=True, title=title)
        return Item(
            ident=ident,
            title=title,
            item_type=item_type,
            prompt_html=renderer.render_blocks(prompt_blocks),
            choices=choices,
            shuffle=shuffle,
            correct_feedback_html=correct_feedback_html,
            incorrect_feedback_html=incorrect_feedback_html,
            response_ident="LID01",
        )

    if item_type == "true-false":
        extracted = find_task_choices(body_blocks, renderer)
        if extracted is not None:
            prompt_blocks, choices = extracted
            if len(choices) != 2:
                raise InputValidationError(f"true-false item must define exactly 2 task-list choices: {title}")
            correct_count = sum(1 for choice in choices if choice.correct)
            if correct_count != 1:
                raise InputValidationError(f"true-false item must define exactly one correct choice: {title}")
            prompt_html = renderer.render_blocks(prompt_blocks)
        else:
            answer = stringify_scalar(raw_item.attrs.get("answer")).lower()
            if answer not in {"true", "false"}:
                raise InputValidationError(
                    f"true-false item must define task-list choices or answer=true|false: {title}"
                )
            choices = [
                ChoiceOption(ident="A", html="True", correct=answer == "true"),
                ChoiceOption(ident="B", html="False", correct=answer == "false"),
            ]
            prompt_html = renderer.render_blocks(body_blocks)
        return Item(
            ident=ident,
            title=title,
            item_type=item_type,
            prompt_html=prompt_html,
            choices=choices,
            shuffle=False,
            correct_feedback_html=correct_feedback_html,
            incorrect_feedback_html=incorrect_feedback_html,
            response_ident="TF02",
        )

    if item_type == "numeric":
        answers = parse_answer_list(raw_item.attrs)
        if not answers:
            raise InputValidationError(f"numeric item must define answer or answers: {title}")
        return Item(
            ident=ident,
            title=title,
            item_type=item_type,
            prompt_html=renderer.render_blocks(body_blocks),
            answers=answers,
            correct_feedback_html=correct_feedback_html,
            incorrect_feedback_html=incorrect_feedback_html,
            response_ident="FIN00",
        )

    if item_type == "cloze":
        prompt_html = renderer.render_blocks(body_blocks)
        segments, blanks = parse_cloze_prompt(prompt_html)
        return Item(
            ident=ident,
            title=title,
            item_type=item_type,
            prompt_html=prompt_html,
            cloze_segments=segments,
            cloze_blanks=blanks,
            correct_feedback_html=correct_feedback_html,
            incorrect_feedback_html=incorrect_feedback_html,
        )

    if item_type == "matching":
        prompt_blocks, prompts, targets = extract_matching(body_blocks, renderer, title=title, item_ident=ident)
        return Item(
            ident=ident,
            title=title,
            item_type=item_type,
            prompt_html=renderer.render_blocks(prompt_blocks),
            matching_prompts=prompts,
            matching_targets=targets,
            correct_feedback_html=correct_feedback_html,
            incorrect_feedback_html=incorrect_feedback_html,
            response_ident="resp_grp",
        )

    raise InputValidationError(f"unsupported item type {item_type!r}")


def split_feedback_blocks(
    blocks: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    body: list[dict[str, Any]] = []
    correct_feedback: list[dict[str, Any]] = []
    incorrect_feedback: list[dict[str, Any]] = []

    for block in blocks:
        if block["t"] != "Div":
            body.append(block)
            continue
        attrs, inner_blocks = block["c"]
        classes = set(attrs[1])
        if "feedback" not in classes:
            body.append(block)
            continue
        kind = dict(attrs[2]).get("kind")
        if kind == "correct":
            correct_feedback.extend(inner_blocks)
        elif kind == "incorrect":
            incorrect_feedback.extend(inner_blocks)
        else:
            body.append(block)

    return body, correct_feedback, incorrect_feedback


def extract_task_choices(
    blocks: list[dict[str, Any]],
    renderer: HtmlRenderer,
    allow_multiple_correct: bool,
    title: str,
) -> tuple[list[dict[str, Any]], list[ChoiceOption]]:
    extracted = find_task_choices(blocks, renderer)
    if extracted is not None:
        remaining, parsed_choices = extracted
        correct_count = sum(1 for choice in parsed_choices if choice.correct)
        if allow_multiple_correct:
            if correct_count == 0:
                raise InputValidationError(f"multiple-choice item must define at least one correct choice: {title}")
        elif correct_count != 1:
            raise InputValidationError(f"single-choice item must define exactly one correct choice: {title}")
        return remaining, parsed_choices

    expected = "task list options"
    raise InputValidationError(f"{expected} not found in {title}")


def find_task_choices(
    blocks: list[dict[str, Any]],
    renderer: HtmlRenderer,
) -> tuple[list[dict[str, Any]], list[ChoiceOption]] | None:
    for index, block in enumerate(blocks):
        if block["t"] != "BulletList":
            continue
        parsed_choices: list[ChoiceOption] = []
        for option_index, item_blocks in enumerate(block["c"]):
            parsed = parse_task_choice(item_blocks, renderer, option_index)
            if parsed is None:
                parsed_choices = []
                break
            parsed_choices.append(parsed)
        if parsed_choices:
            remaining = copy.deepcopy(blocks[:index] + blocks[index + 1 :])
            return remaining, parsed_choices
    return None


def parse_task_choice(
    item_blocks: list[dict[str, Any]],
    renderer: HtmlRenderer,
    option_index: int,
) -> ChoiceOption | None:
    if not item_blocks:
        return None
    first_block = copy.deepcopy(item_blocks[0])
    if first_block["t"] not in {"Para", "Plain"}:
        return None

    inlines = first_block["c"]
    if not inlines or inlines[0]["t"] != "Str":
        return None
    marker = inlines[0]["c"]
    if marker not in {TASK_UNCHECKED, TASK_CHECKED}:
        return None

    remainder = inlines[1:]
    if remainder and remainder[0]["t"] == "Space":
        remainder = remainder[1:]
    first_block["c"] = remainder
    rendered_blocks = [first_block] + copy.deepcopy(item_blocks[1:])
    option_html = renderer.render_compact_blocks(rendered_blocks)
    return ChoiceOption(
        ident=option_ident(option_index),
        html=option_html,
        correct=marker == TASK_CHECKED,
    )


def extract_matching(
    blocks: list[dict[str, Any]],
    renderer: HtmlRenderer,
    title: str,
    item_ident: str,
) -> tuple[list[dict[str, Any]], list[MatchingPrompt], list[MatchingTarget]]:
    for index, block in enumerate(blocks):
        if block["t"] != "Table":
            continue
        body_rows = block["c"][4]
        rows: list[Any] = []
        for body in body_rows:
            rows.extend(body[3])
        if not rows:
            raise InputValidationError(f"matching item table has no rows: {title}")

        prompt_entries: list[tuple[str, str]] = []
        target_by_html: dict[str, str] = {}
        targets: list[MatchingTarget] = []
        for row_index, row in enumerate(rows):
            cells = row[1]
            if len(cells) != 2:
                raise InputValidationError(f"matching item rows must have exactly 2 columns: {title}")
            prompt_html = renderer.render_compact_blocks(cells[0][4])
            target_html = renderer.render_compact_blocks(cells[1][4])
            if target_html not in target_by_html:
                target_ident = f"MS-{item_ident}-{len(targets) + 1}"
                target_by_html[target_html] = target_ident
                targets.append(MatchingTarget(ident=target_ident, html=target_html))
            prompt_ident = f"MT-{item_ident}-{option_ident(row_index)}"
            prompt_entries.append((prompt_ident, target_by_html[target_html]))
        prompts = [
            MatchingPrompt(ident=prompt_ident, html=renderer.render_compact_blocks(rows[idx][1][0][4]), target_ident=target_ident)
            for idx, (prompt_ident, target_ident) in enumerate(prompt_entries)
        ]
        remaining = copy.deepcopy(blocks[:index] + blocks[index + 1 :])
        return remaining, prompts, targets

    raise InputValidationError(f"matching item must contain a 2-column table: {title}")


def parse_cloze_prompt(prompt_html: str) -> tuple[list[str], list[ClozeBlank]]:
    segments: list[str] = []
    blanks: list[ClozeBlank] = []
    last_end = 0

    for index, match in enumerate(CLOZE_RE.finditer(prompt_html)):
        segments.append(prompt_html[last_end : match.start()])
        answers = [html.unescape(part).strip() for part in match.group(1).split("|")]
        answers = [answer for answer in answers if answer]
        if not answers:
            raise InputValidationError("cloze blank must contain at least one answer")
        blanks.append(ClozeBlank(ident=f"FIB{index:02d}", answers=answers))
        last_end = match.end()

    if not blanks:
        raise InputValidationError("cloze item must contain at least one [[...]] blank")

    segments.append(prompt_html[last_end:])
    return segments, blanks


def parse_answer_list(attrs: dict[str, str]) -> list[str]:
    single = stringify_scalar(attrs.get("answer"))
    multiple = stringify_scalar(attrs.get("answers"))
    values: list[str] = []
    if single:
        values.append(single)
    if multiple:
        values.extend(part.strip() for part in multiple.split(","))
    normalized = [value for value in values if value]
    return normalized


def build_assessment_metadata(
    meta: dict[str, Any],
    open_at: str,
    due_at: str,
    duration: str,
) -> dict[str, str]:
    metadata = {key: value for key, value in ASSESSMENT_METADATA_DEFAULTS}
    author = stringify_scalar(meta.get("author"))
    creator = stringify_scalar(meta.get("creator")) or author
    metadata["AUTHORS"] = author
    metadata["CREATOR"] = creator
    metadata["START_DATE"] = open_at
    metadata["END_DATE"] = due_at
    metadata["CONSIDER_START_DATE"] = "True" if open_at else "False"
    metadata["CONSIDER_END_DATE"] = "True" if due_at else "False"
    metadata["CONSIDER_DURATION"] = "True" if duration else "False"
    metadata["ASSESSMENT_RELEASED_TO"] = stringify_scalar(meta.get("released_to"))
    metadata["NAVIGATION"] = stringify_scalar(meta.get("navigation")) or metadata["NAVIGATION"]
    metadata["QUESTION_LAYOUT"] = stringify_scalar(meta.get("question_layout")) or metadata["QUESTION_LAYOUT"]
    metadata["QUESTION_NUMBERING"] = (
        stringify_scalar(meta.get("question_numbering")) or metadata["QUESTION_NUMBERING"]
    )
    metadata["MAX_ATTEMPTS"] = stringify_scalar(meta.get("max_attempts")) or metadata["MAX_ATTEMPTS"]
    return metadata


def build_package_files(assessment: Assessment) -> dict[str, bytes]:
    xml_name = f"{assessment.stem}.xml"
    files = {
        "imsmanifest.xml": build_manifest_xml(assessment, xml_name),
        xml_name: build_assessment_xml(assessment),
    }
    for asset in assessment.assets:
        files[asset.href] = asset.source.read_bytes()
    return files


def build_manifest_xml(assessment: Assessment, xml_name: str) -> bytes:
    manifest = ET.Element(
        f"{{{IMSCP_NS}}}manifest",
        {
            "identifier": "MANIFEST1",
            f"{{{XSI_NS}}}schemaLocation": (
                f"{IMSCP_NS} http://www.imsglobal.org/xsd/imscp_v1p1.xsd"
            ),
        },
    )
    metadata = ET.SubElement(manifest, f"{{{IMSCP_NS}}}metadata")
    ET.SubElement(metadata, f"{{{IMSCP_NS}}}schema").text = "IMS Content"
    ET.SubElement(metadata, f"{{{IMSCP_NS}}}schemaversion").text = "1.1.3"
    ET.SubElement(manifest, f"{{{IMSCP_NS}}}organizations")
    resources = ET.SubElement(manifest, f"{{{IMSCP_NS}}}resources")
    resource = ET.SubElement(
        resources,
        f"{{{IMSCP_NS}}}resource",
        {"identifier": "RESOURCE1", "type": "imsqti_xmlv1p1", "href": xml_name},
    )
    ET.SubElement(resource, f"{{{IMSCP_NS}}}file", {"href": xml_name})
    for asset in assessment.assets:
        ET.SubElement(resource, f"{{{IMSCP_NS}}}file", {"href": asset.href})
    ET.indent(manifest, space="  ")
    return ET.tostring(manifest, encoding="utf-8", xml_declaration=True)


def build_assessment_xml(assessment: Assessment) -> bytes:
    serializer = CDataSerializer()
    root = ET.Element("questestinterop")
    assessment_el = ET.SubElement(root, "assessment", {"ident": assessment.ident, "title": assessment.title})
    ET.SubElement(assessment_el, "qticomment").text = ""
    ET.SubElement(assessment_el, "duration").text = assessment.duration
    qtimetadata = ET.SubElement(assessment_el, "qtimetadata")
    add_qtimetadata_fields(qtimetadata, assessment.metadata)
    ET.SubElement(
        assessment_el,
        "assessmentcontrol",
        {"feedbackswitch": "Yes", "hintswitch": "Yes", "solutionswitch": "Yes", "view": "All"},
    )
    add_empty_rubric(assessment_el)
    add_flow_mat_container(assessment_el, "presentation_material", "", serializer, include_blank_image=False)
    feedback = ET.SubElement(assessment_el, "assessfeedback", {"ident": "Feedback", "title": "Feedback", "view": "All"})
    flow_mat = ET.SubElement(feedback, "flow_mat", {"class": "Block"})
    add_text_material(flow_mat, "", serializer)

    for section in assessment.sections:
        section_el = ET.SubElement(assessment_el, "section", {"ident": section.ident, "title": section.title})
        section_metadata = ET.SubElement(section_el, "qtimetadata")
        add_qtimetadata_fields(section_metadata, {key: value for key, value in SECTION_METADATA_DEFAULTS})
        add_flow_mat_container(section_el, "presentation_material", section.description_html, serializer, include_blank_image=True)
        selection_ordering = ET.SubElement(section_el, "selection_ordering", {"sequence_type": "Normal"})
        selection = ET.SubElement(selection_ordering, "selection")
        ET.SubElement(selection, "sourcebank_ref").text = ""
        ET.SubElement(selection, "selection_number").text = ""
        ET.SubElement(selection_ordering, "order", {"order_type": "Sequential"})

        for item in section.items:
            section_el.append(build_item_xml(item, serializer))

    return serializer.render(root)


def build_item_xml(item: Item, serializer: CDataSerializer) -> ET.Element:
    item_el = ET.Element("item", {"ident": item.ident, "title": item.title})
    ET.SubElement(item_el, "duration").text = ""

    itemmetadata = ET.SubElement(item_el, "itemmetadata")
    qtimetadata = ET.SubElement(itemmetadata, "qtimetadata")
    metadata_fields = {"qmd_itemtype": QMD_ITEM_TYPES[item.item_type]}
    for key, value in ITEM_METADATA_COMMON:
        metadata_fields[key] = value
    for key, value in ITEM_TYPE_METADATA[item.item_type]:
        metadata_fields[key] = value
    if item.item_type in {"single-choice", "multiple-choice"} and "RANDOMIZE" in metadata_fields:
        metadata_fields["RANDOMIZE"] = "true" if item.shuffle else "false"
    add_qtimetadata_fields(qtimetadata, metadata_fields)

    add_empty_rubric(item_el)

    if item.item_type in {"single-choice", "multiple-choice", "true-false"}:
        build_choice_item(item_el, item, serializer)
    elif item.item_type == "numeric":
        build_numeric_item(item_el, item, serializer)
    elif item.item_type == "cloze":
        build_cloze_item(item_el, item, serializer)
    elif item.item_type == "matching":
        build_matching_item(item_el, item, serializer)
    else:
        raise BuildError(f"cannot render unsupported item type: {item.item_type}")

    add_feedback_node(item_el, "Correct", item.correct_feedback_html, serializer)
    add_feedback_node(item_el, "InCorrect", item.incorrect_feedback_html, serializer)
    return item_el


def build_choice_item(item_el: ET.Element, item: Item, serializer: CDataSerializer) -> None:
    label = "Resp001" if item.item_type == "true-false" else "Resp003"
    rcardinality = "Single" if item.item_type in {"single-choice", "true-false"} else "Multiple"
    presentation = ET.SubElement(item_el, "presentation", {"label": label})
    flow = ET.SubElement(presentation, "flow", {"class": "Block"})
    add_text_material(flow, item.prompt_html, serializer)
    add_blank_matimage_material(flow)
    response_lid = ET.SubElement(
        flow,
        "response_lid",
        {"ident": item.response_ident, "rcardinality": rcardinality, "rtiming": "No"},
    )
    render_choice = ET.SubElement(
        response_lid,
        "render_choice",
        {"shuffle": "Yes" if item.shuffle else "No"},
    )
    for choice in item.choices:
        label_el = ET.SubElement(
            render_choice,
            "response_label",
            {"ident": choice.ident, "rarea": "Ellipse", "rrange": "Exact", "rshuffle": "Yes"},
        )
        add_text_material(label_el, choice.html, serializer)
        add_blank_matimage_material(label_el)

    resprocessing = ET.SubElement(item_el, "resprocessing")
    add_outcomes(resprocessing)
    for choice in item.choices:
        respcondition = ET.SubElement(
            resprocessing,
            "respcondition",
            {"continue": "No" if item.item_type in {"single-choice", "true-false"} else "Yes"},
        )
        conditionvar = ET.SubElement(respcondition, "conditionvar")
        ET.SubElement(
            conditionvar,
            "varequal",
            {"case": "Yes", "respident": item.response_ident},
        ).text = choice.ident
        ET.SubElement(respcondition, "setvar", {"action": "Add", "varname": "SCORE"}).text = "0.0"
        ET.SubElement(
            respcondition,
            "displayfeedback",
            {"feedbacktype": "Response", "linkrefid": "Correct" if choice.correct else "InCorrect"},
        )


def build_numeric_item(item_el: ET.Element, item: Item, serializer: CDataSerializer) -> None:
    presentation = ET.SubElement(item_el, "presentation", {"label": "FIN"})
    outer_flow = ET.SubElement(presentation, "flow", {"class": "Block"})
    inner_flow = ET.SubElement(outer_flow, "flow", {"class": "Block"})
    add_text_material(inner_flow, item.prompt_html, serializer)
    add_text_material(inner_flow, "", serializer)
    response = ET.SubElement(inner_flow, "response_str", {"ident": item.response_ident, "rcardinality": "Ordered", "rtiming": "No"})
    ET.SubElement(response, "render_fin", {"columns": "5", "fintype": "String", "prompt": "Box", "rows": "1"})

    resprocessing = ET.SubElement(item_el, "resprocessing")
    add_outcomes(resprocessing)
    respcondition = ET.SubElement(resprocessing, "respcondition", {"continue": "Yes"})
    conditionvar = ET.SubElement(respcondition, "conditionvar")
    or_el = ET.SubElement(conditionvar, "or")
    for answer in item.answers:
        ET.SubElement(or_el, "varequal", {"case": "No", "respident": item.response_ident}).text = answer
    ET.SubElement(respcondition, "setvar", {"action": "Add", "varname": "SCORE"}).text = "0"


def build_cloze_item(item_el: ET.Element, item: Item, serializer: CDataSerializer) -> None:
    presentation = ET.SubElement(item_el, "presentation", {"label": "FIB"})
    outer_flow = ET.SubElement(presentation, "flow", {"class": "Block"})
    inner_flow = ET.SubElement(outer_flow, "flow", {"class": "Block"})

    for segment, blank in zip(item.cloze_segments, item.cloze_blanks, strict=False):
        add_text_material(inner_flow, segment, serializer)
        response = ET.SubElement(inner_flow, "response_str", {"ident": blank.ident, "rcardinality": "Ordered", "rtiming": "No"})
        ET.SubElement(
            response,
            "render_fib",
            {"charset": "ascii-us", "columns": "5", "encoding": "UTF_8", "fibtype": "String", "prompt": "Box", "rows": "1"},
        )
    add_text_material(inner_flow, item.cloze_segments[-1], serializer)

    resprocessing = ET.SubElement(item_el, "resprocessing")
    add_outcomes(resprocessing)
    for blank in item.cloze_blanks:
        respcondition = ET.SubElement(resprocessing, "respcondition", {"continue": "Yes"})
        conditionvar = ET.SubElement(respcondition, "conditionvar")
        or_el = ET.SubElement(conditionvar, "or")
        for answer in blank.answers:
            ET.SubElement(or_el, "varequal", {"case": "No", "respident": blank.ident}).text = answer
        ET.SubElement(respcondition, "setvar", {"action": "Add", "varname": "SCORE"}).text = "0"


def build_matching_item(item_el: ET.Element, item: Item, serializer: CDataSerializer) -> None:
    presentation = ET.SubElement(item_el, "presentation")
    flow = ET.SubElement(presentation, "flow", {"class": "Block"})
    add_text_material(flow, item.prompt_html, serializer)
    add_blank_matimage_material(flow)
    response_grp = ET.SubElement(
        flow,
        "response_grp",
        {"ident": item.response_ident, "rcardinality": "Ordered", "rtiming": "No"},
    )
    render_choice = ET.SubElement(response_grp, "render_choice", {"shuffle": "No"})
    for prompt in item.matching_prompts:
        prompt_label = ET.SubElement(
            render_choice,
            "response_label",
            {"ident": prompt.ident, "rarea": "Ellipse", "rrange": "Exact", "rshuffle": "Yes"},
        )
        add_text_material(prompt_label, prompt.html, serializer)
    for target in item.matching_targets:
        target_label = ET.SubElement(
            render_choice,
            "response_label",
            {
                "ident": target.ident,
                "match_group": "",
                "match_max": "1",
                "rarea": "Ellipse",
                "rrange": "Exact",
                "rshuffle": "Yes",
            },
        )
        add_text_material(target_label, target.html, serializer)
    ET.SubElement(render_choice, "response_label", {"rarea": "Ellipse", "rrange": "Exact", "rshuffle": "Yes"})

    resprocessing = ET.SubElement(item_el, "resprocessing")
    add_outcomes(resprocessing)
    condition_index = 1
    for prompt in item.matching_prompts:
        for target in item.matching_targets:
            respcondition = ET.SubElement(resprocessing, "respcondition", {"continue": "No"})
            conditionvar = ET.SubElement(respcondition, "conditionvar")
            ET.SubElement(
                conditionvar,
                "varequal",
                {"case": "Yes", "index": str(condition_index), "respident": prompt.ident},
            ).text = target.ident
            ET.SubElement(respcondition, "setvar", {"action": "Add", "varname": "SCORE"}).text = "0.0"
            ET.SubElement(
                respcondition,
                "displayfeedback",
                {
                    "feedbacktype": "Response",
                    "linkrefid": "Correct" if target.ident == prompt.target_ident else "InCorrect",
                },
            )
            condition_index += 1


def add_empty_rubric(parent: ET.Element) -> None:
    rubric = ET.SubElement(parent, "rubric", {"view": "All"})
    material = ET.SubElement(rubric, "material")
    ET.SubElement(material, "mattext", mattext_attributes())


def add_flow_mat_container(
    parent: ET.Element,
    tag_name: str,
    html_text: str,
    serializer: CDataSerializer,
    include_blank_image: bool,
) -> None:
    container = ET.SubElement(parent, tag_name)
    flow_mat = ET.SubElement(container, "flow_mat", {"class": "Block"})
    add_text_material(flow_mat, html_text, serializer)
    if include_blank_image:
        add_blank_matimage_material(flow_mat)


def add_feedback_node(parent: ET.Element, ident: str, html_text: str, serializer: CDataSerializer) -> None:
    feedback = ET.SubElement(parent, "itemfeedback", {"ident": ident, "view": "All"})
    flow_mat = ET.SubElement(feedback, "flow_mat", {"class": "Block"})
    add_text_material(flow_mat, html_text, serializer)
    add_blank_matimage_material(flow_mat)


def add_text_material(parent: ET.Element, html_text: str, serializer: CDataSerializer) -> ET.Element:
    material = ET.SubElement(parent, "material")
    mattext = ET.SubElement(material, "mattext", mattext_attributes())
    serializer.assign(mattext, html_text)
    return material


def add_blank_matimage_material(parent: ET.Element) -> None:
    material = ET.SubElement(parent, "material")
    ET.SubElement(material, "matimage", {"embedded": "base64", "imagtype": "text/html", "uri": ""})


def add_outcomes(parent: ET.Element) -> None:
    outcomes = ET.SubElement(parent, "outcomes")
    ET.SubElement(
        outcomes,
        "decvar",
        {"defaultval": "0", "maxvalue": "0.0", "minvalue": "0.0", "varname": "SCORE", "vartype": "Integer"},
    )


def add_qtimetadata_fields(parent: ET.Element, fields: dict[str, str]) -> None:
    for key, value in fields.items():
        field = ET.SubElement(parent, "qtimetadatafield")
        ET.SubElement(field, "fieldlabel").text = key
        ET.SubElement(field, "fieldentry").text = value


def mattext_attributes() -> dict[str, str]:
    return {"charset": "ascii-us", "texttype": "text/plain", f"{{{XML_NS}}}space": "default"}


def write_zip(output_path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(files):
            info = zipfile.ZipInfo(name)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, files[name])


def run_pandoc_json(input_path: Path) -> dict[str, Any]:
    cmd = ["pandoc", "-f", "markdown", "-t", "json", str(input_path)]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise BuildError("pandoc is required but was not found") from exc

    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip() or "pandoc failed"
        raise BuildError(message)
    return json.loads(proc.stdout)


def parse_meta_map(meta: dict[str, Any]) -> dict[str, Any]:
    return {key: parse_meta_value(value) for key, value in meta.items()}


def parse_meta_value(value: dict[str, Any]) -> Any:
    value_type = value["t"]
    content = value.get("c")
    if value_type == "MetaString":
        return content
    if value_type == "MetaBool":
        return bool(content)
    if value_type == "MetaInlines":
        return stringify_inlines(content)
    if value_type == "MetaBlocks":
        return stringify_blocks(content)
    if value_type == "MetaList":
        return [parse_meta_value(entry) for entry in content]
    if value_type == "MetaMap":
        return {key: parse_meta_value(entry) for key, entry in content.items()}
    raise InputValidationError(f"unsupported metadata type: {value_type}")


def stringify_blocks(blocks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for block in blocks:
        if block["t"] in {"Para", "Plain"}:
            parts.append(stringify_inlines(block["c"]))
    return "\n\n".join(part for part in parts if part)


def stringify_inlines(inlines: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for inline in inlines:
        inline_type = inline["t"]
        content = inline.get("c")
        if inline_type == "Str":
            parts.append(content)
        elif inline_type in {"Space", "SoftBreak", "LineBreak"}:
            parts.append(" ")
        elif inline_type in {"Emph", "Strong", "Underline", "Strikeout", "Superscript", "Subscript", "SmallCaps"}:
            parts.append(stringify_inlines(content))
        elif inline_type == "Code":
            parts.append(content[1])
        elif inline_type == "Link":
            parts.append(stringify_inlines(content[1]))
        elif inline_type == "Image":
            parts.append(stringify_inlines(content[1]))
        elif inline_type == "Span":
            parts.append(stringify_inlines(content[1]))
        elif inline_type == "Quoted":
            parts.append(stringify_inlines(content[1]))
        elif inline_type in {"Math", "RawInline"}:
            parts.append(content[1])
    return collapse_spaces("".join(parts))


def collapse_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def stringify_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return ",".join(stringify_scalar(part) for part in value)
    return str(value).strip()


def parse_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    lowered = stringify_scalar(value).lower()
    if lowered in {"true", "yes", "1"}:
        return True
    if lowered in {"false", "no", "0"}:
        return False
    raise InputValidationError(f"invalid boolean value: {value}")


def normalize_datetime(value: Any, timezone_value: Any) -> str:
    text = stringify_scalar(value)
    if not text:
        return ""
    try:
        dt = datetime.fromisoformat(text)
    except ValueError as exc:
        raise InputValidationError(f"invalid datetime: {text}") from exc
    if dt.tzinfo is None:
        timezone_name = stringify_scalar(timezone_value) or "UTC"
        try:
            dt = dt.replace(tzinfo=ZoneInfo(timezone_name))
        except Exception as exc:
            raise InputValidationError(f"invalid timezone: {timezone_name}") from exc
    return dt.isoformat()


def sanitize_stem(value: str) -> str:
    value = collapse_spaces(value)
    if not value:
        raise UsageError("output stem cannot be empty")
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-")
    return sanitized or "assessment"


def sanitize_ident(value: str) -> str:
    value = value or "item"
    sanitized = re.sub(r"[^A-Za-z0-9._:-]+", "-", value).strip("-")
    return sanitized or "item"


def option_ident(index: int) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    if index < len(alphabet):
        return alphabet[index]
    raise InputValidationError("too many choices; only up to 26 are supported")
