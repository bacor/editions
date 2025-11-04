from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_HEADER_RE = re.compile(r"^(#{1,6})\s+")

# Resolve project root as the parent of the src directory.
PROJECT_ROOT = Path(__file__).resolve().parents[1]


def slugify(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or "unknown"


def relative_to_root(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def _parse_front_matter(text: str) -> tuple[dict[str, Any], str, str | None]:
    if not text.startswith("---"):
        return {}, text, None

    lines = text.splitlines(keepends=True)
    front_lines: list[str] = []
    closing_index: int | None = None

    for idx, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            closing_index = idx
            break
        front_lines.append(line)

    if closing_index is None:
        raise ValueError("Invalid front matter: closing marker not found")

    comment_lines: list[str] = []
    while front_lines and front_lines[0].lstrip().startswith("#"):
        comment_lines.append(front_lines.pop(0))

    comment = None
    if comment_lines:
        comment = "\n".join(
            line.lstrip()[1:].lstrip()
            for line in comment_lines
        ).strip()

    front_text = "".join(front_lines).strip("\n")
    front_data = yaml.safe_load(front_text) or {}
    if not isinstance(front_data, dict):
        raise ValueError("Front matter must be a mapping")

    body = "".join(lines[closing_index + 1 :])
    return front_data, body, (comment or None)


def _ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


@dataclass
class ReadmeDocument:
    """Represents a README with YAML front matter and Markdown body."""

    path: Path | None
    front_matter: dict[str, Any]
    body: str
    front_comment: str | None = None

    @classmethod
    def load(cls, path: str | Path) -> "ReadmeDocument":
        file_path = Path(path)
        text = file_path.read_text(encoding="utf-8")
        front, body, comment = (
            _parse_front_matter(text) if text.startswith("---") else ({}, text, None)
        )
        return cls(path=file_path, front_matter=front, body=body, front_comment=comment)

    def dump(self) -> str:
        parts: list[str] = []
        if self.front_matter or self.front_comment:
            parts.append("---\n")
            if self.front_comment:
                for line in self.front_comment.splitlines():
                    parts.append(f"# {line}\n")
            if self.front_matter:
                front_yaml = yaml.safe_dump(
                    self.front_matter, sort_keys=False, allow_unicode=True
                ).strip()
                if front_yaml:
                    parts.append(front_yaml + "\n")
            parts.append("---\n")
            if self.body and not self.body.startswith("\n"):
                parts.append("\n")
        parts.append(self.body)
        return _ensure_trailing_newline("".join(parts))

    def write(self, path: str | Path | None = None) -> None:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("No output path specified")
        target.write_text(self.dump(), encoding="utf-8")

    def set_front_matter(self, key: str, value: Any) -> None:
        self.front_matter[key] = value

    def ensure_title(self, title: str | None) -> None:
        if title and not self.front_matter.get("title"):
            self.front_matter["title"] = title

    def ensure_other(self) -> dict[str, Any]:
        other = self.front_matter.get("other")
        if not isinstance(other, dict):
            other = {}
        self.front_matter["other"] = other
        return other

    def set_composer_comment(self, name: str | None) -> None:
        if name:
            self.front_comment = (
                f"Composer: {name} (details inherited from parent)"
            )
        else:
            self.front_comment = None

    def get_composer_from_comment(self) -> str | None:
        if not self.front_comment:
            return None
        match = re.match(r"Composer:\s*(.+?)(?:\s*\(|$)", self.front_comment)
        if match:
            return match.group(1).strip()
        return None

    def reorder_front_matter(self, keys: list[str]) -> None:
        if not self.front_matter:
            return
        ordered: dict[str, Any] = {}
        for key in keys:
            if key in self.front_matter:
                ordered[key] = self.front_matter[key]
        for key, value in self.front_matter.items():
            if key not in ordered:
                ordered[key] = value
        self.front_matter = ordered

    def set_section(self, heading: str, content: str, level: int = 2) -> None:
        """Replace or append a Markdown section under the given heading."""

        header_line = f"{'#' * level} {heading}".rstrip()
        normalized_content = content.rstrip("\n")
        if normalized_content:
            normalized_content += "\n\n"
        new_section_text = header_line + "\n\n" + normalized_content
        new_section_lines = (new_section_text + "\n").splitlines(keepends=True)

        lines = self.body.splitlines(keepends=True)
        header_index: int | None = None
        for idx, line in enumerate(lines):
            if line.rstrip("\n").strip() == header_line:
                header_index = idx
                break

        if header_index is None:
            addition = "".join(new_section_lines)
            body = self.body
            if body:
                if not body.endswith("\n"):
                    body += "\n"
                if not body.endswith("\n\n"):
                    body += "\n"
                body += addition
            else:
                body = addition
            self.body = body
            return

        end_index = len(lines)
        for idx in range(header_index + 1, len(lines)):
            stripped = lines[idx].lstrip()
            if stripped.startswith("#"):
                match = _HEADER_RE.match(stripped)
                if match and len(match.group(1)) <= level:
                    end_index = idx
                    break

        updated_lines = lines[:header_index] + new_section_lines + lines[end_index:]
        self.body = "".join(updated_lines)
