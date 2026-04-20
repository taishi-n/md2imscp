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
