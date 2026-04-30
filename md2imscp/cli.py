from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .core import (
    Md2ImscpError,
    build_package,
    dump_ast,
    validate_package,
)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="md2imscp")
    subparsers = parser.add_subparsers(dest="command", required=True)

    build_parser = subparsers.add_parser("build", help="Build an IMS Content Packaging zip from Markdown.")
    build_parser.add_argument("input", type=Path, help="Input Markdown file.")
    build_parser.add_argument("-o", "--output", type=Path, required=True, help="Output zip path.")
    build_parser.add_argument("--stem", help="Override the generated XML stem name.")
    build_parser.add_argument(
        "--asset-root",
        type=Path,
        help="Base directory used to resolve relative assets. Defaults to the Markdown file directory.",
    )
    build_parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the generated package after building it.",
    )
    build_parser.add_argument(
        "--shuffle-items",
        action="store_true",
        help="Shuffle item order before writing the package.",
    )
    build_parser.add_argument(
        "--item-limit",
        type=positive_int,
        help="Keep only the first N items after optional shuffling.",
    )
    build_parser.add_argument(
        "--shuffle-seed",
        type=int,
        help="Seed used with --shuffle-items for reproducible item order.",
    )
    build_parser.add_argument(
        "--horizontal-rule-item-type",
        choices=["single-choice", "multiple-choice", "true-false", "cloze", "matching"],
        help="Treat each horizontal-rule-delimited block in the input Markdown as one item of the given type.",
    )
    build_parser.add_argument(
        "--generated-markdown-out",
        type=Path,
        help="Write the generated standard Markdown used for build when --horizontal-rule-item-type is enabled.",
    )

    dump_ast_parser = subparsers.add_parser("dump-ast", help="Dump the Pandoc JSON AST.")
    dump_ast_parser.add_argument("input", type=Path, help="Input Markdown file.")

    validate_parser = subparsers.add_parser("validate", help="Validate an existing package zip.")
    validate_parser.add_argument("input", type=Path, help="Package zip path.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.command == "build":
            output = build_package(
                input_path=args.input,
                output_path=args.output,
                stem=args.stem,
                asset_root=args.asset_root,
                run_validation=args.validate,
                shuffle_items=args.shuffle_items,
                item_limit=args.item_limit,
                shuffle_seed=args.shuffle_seed,
                horizontal_rule_item_type=args.horizontal_rule_item_type,
                generated_markdown_out=args.generated_markdown_out,
            )
            print(output)
            return 0
        if args.command == "dump-ast":
            print(dump_ast(args.input))
            return 0
        if args.command == "validate":
            validate_package(args.input)
            print(f"validated {args.input}")
            return 0
    except Md2ImscpError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code

    parser.error(f"unknown command: {args.command}")
    return 1
