from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Iterable, Sequence

from .musicxml_metadata import apply_musicxml_metadata, extract_musicxml_metadata


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extract",
        description="Extract metadata from MusicXML files and store it in an edition README front matter.",
    )
    parser.add_argument(
        "target",
        help="Edition directory or README file to update.",
    )
    parser.add_argument(
        "--musicxml",
        "-m",
        action="append",
        help="Path to a MusicXML file. When omitted, all *.musicxml files in the edition directory are used.",
    )
    parser.add_argument(
        "--key",
        "-k",
        default="musicxml",
        help="Front matter key under which metadata is stored. When multiple files are processed, "
        "keys are suffixed with each file's stem.",
    )
    parser.add_argument(
        "--recursive",
        "-r",
        action="store_true",
        help="Recursively search for MusicXML files when --musicxml is not provided.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print extracted metadata instead of updating the README.",
    )
    return parser


def _resolve_readme_path(target: str) -> Path:
    path = Path(target)
    if path.is_file():
        return path
    if path.is_dir():
        for candidate in ("README.md", "Readme.md", "readme.md"):
            readme = path / candidate
            if readme.exists():
                return readme
        return path / "README.md"
    if path.suffix.lower() == ".md":
        return path
    raise FileNotFoundError(f"Could not locate README for target: {target}")


def _resolve_musicxml_paths(
    readme_path: Path, provided: Iterable[str] | None, recursive: bool
) -> list[Path]:
    if provided:
        files = []
        for p in provided:
            path = Path(p)
            if not path.is_absolute():
                path = (readme_path.parent / path).resolve()
            files.append(path)
    else:
        search_root = readme_path.parent
        if recursive:
            files = sorted(search_root.rglob("*.musicxml"))
        else:
            files = sorted(search_root.glob("*.musicxml"))
    if not files:
        raise FileNotFoundError(
            f"No MusicXML files found for README at {readme_path}"
        )
    return files


def _derive_key(base_key: str, file_path: Path, index: int) -> str:
    if index == 0:
        return base_key
    return f"{base_key}_{file_path.stem}"


def run(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    readme_path = _resolve_readme_path(args.target)
    musicxml_files = _resolve_musicxml_paths(
        readme_path, args.musicxml, args.recursive
    )

    for idx, musicxml_path in enumerate(musicxml_files):
        metadata = extract_musicxml_metadata(musicxml_path)
        key = _derive_key(args.key, Path(musicxml_path), idx)

        if args.dry_run:
            print(f"[DRY RUN] {musicxml_path} -> key '{key}': {metadata}")
            continue
        apply_musicxml_metadata(readme_path, musicxml_path, key=key)
        print(
            f"Updated {readme_path} with metadata from {musicxml_path} (key '{key}')"
        )

    return 0


def main(argv: Sequence[str] | None = None) -> None:
    try:
        exit_code = run(argv)
    except Exception as exc:  # pragma: no cover - CLI errors
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    else:
        sys.exit(exit_code)
