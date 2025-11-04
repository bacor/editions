from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .indexer import (
    build_composer_index,
    build_root_index,
    update_readme_with_index,
    write_index,
)
from .readme import PROJECT_ROOT, ReadmeDocument


def _is_composer_directory(path: Path) -> bool:
    readme = path / "README.md"
    if not readme.exists():
        return False
    document = ReadmeDocument.load(readme)
    return isinstance(document.front_matter.get("composer"), dict)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="index",
        description="Generate index.yaml files for composers and editions.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="editions",
        help="Target directory to index. Defaults to the editions root.",
    )
    parser.add_argument(
        "--no-global",
        action="store_true",
        help="When indexing the editions root, skip writing the aggregated index.",
    )
    parser.add_argument(
        "--no-readme",
        action="store_true",
        help="Skip updating README files with index tables.",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    target = Path(args.target)
    if not target.exists():
        raise FileNotFoundError(f"Target path does not exist: {target}")

    if _is_composer_directory(target):
        data = build_composer_index(target)
        write_index(target / "index.yaml", data)
        if not args.no_readme:
            update_readme_with_index(
                target / "README.md", data["composers"], data["editions"]
            )
        print(f"Written {target / 'index.yaml'}")
        return 0

    if target.is_dir():
        extra_readmes: list[Path] | None = None
        default_editions_root = (PROJECT_ROOT / "editions").resolve()
        if not args.no_readme and target.resolve() == default_editions_root:
            extra_readmes = [PROJECT_ROOT / "README.md"]

        data = build_root_index(
            target,
            write_composer_indexes=not args.no_readme,
            update_readmes=not args.no_readme,
            extra_readmes=extra_readmes,
        )
        if not args.no_global:
            write_index(target / "index.yaml", data)
            print(f"Written {target / 'index.yaml'}")
        return 0

    raise ValueError("Target must be a directory containing composer editions.")


def main(argv: Sequence[str] | None = None) -> None:
    try:
        exit_code = run(argv)
    except Exception as exc:  # pragma: no cover - CLI errors
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(exit_code)
