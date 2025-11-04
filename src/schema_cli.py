from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

import yaml

from .metadata import edition_index_schema_dict
from .readme import PROJECT_ROOT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schema",
        description="Export the JSON schema for editions/index.yaml",
    )
    parser.add_argument(
        "--format",
        choices=["json", "yaml"],
        default="json",
        help="Output format (default: json).",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional file path to write the schema. "
        "Defaults to editions/schema.json (or schema.yaml when --format yaml).",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    schema = edition_index_schema_dict()
    if args.format == "json":
        payload = json.dumps(schema, indent=2)
    else:
        payload = yaml.safe_dump(schema, sort_keys=False, allow_unicode=True)

    if args.out:
        output_path = args.out
    else:
        default_dir = PROJECT_ROOT / "editions"
        default_dir.mkdir(parents=True, exist_ok=True)
        suffix = ".yaml" if args.format == "yaml" else ".json"
        output_path = default_dir / f"schema{suffix}"

    output_path.write_text(payload, encoding="utf-8")
    print(f"Wrote schema to {output_path}")

    return 0


def main(argv: Sequence[str] | None = None) -> None:
    try:
        exit_code = run(argv)
    except Exception as exc:  # pragma: no cover
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(exit_code)
