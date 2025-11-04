from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

from music21 import converter, meter

from .readme import ReadmeDocument, relative_to_root, slugify


def extract_musicxml_metadata(path: str | Path) -> dict[str, Any]:
    """Return structured metadata extracted from a MusicXML file using music21."""

    score = converter.parse(path)
    meta = score.metadata
    data: dict[str, Any] = {}

    def _safe_get(attribute: str) -> Any:
        if meta is None:
            return None
        try:
            return getattr(meta, attribute)
        except AttributeError:
            return None

    if meta is not None:
        title = _safe_get("title")
        if title:
            data["title"] = title
        composer = _safe_get("composer")
        if composer:
            data["composer"] = composer
        movement_name = _safe_get("movementName")
        if movement_name:
            data["movement_name"] = movement_name
        work_title = _safe_get("workTitle")
        if work_title:
            data["work_title"] = work_title
        lyricist = _safe_get("lyricist") or _safe_get("poet")
        if lyricist:
            data["lyricist"] = lyricist
        movement_number = _safe_get("movementNumber")
        if movement_number:
            data["movement_number"] = movement_number
        date_value = _safe_get("date")
        if date_value:
            data["date"] = date_value
        language = _safe_get("language")
        if language:
            data["language"] = language
        source = _safe_get("source")
        if source:
            data["source"] = source
        rights = _safe_get("rights")
        if rights:
            data["license"] = rights
        copyright_value = _safe_get("copyright")
        if copyright_value:
            data["copyright"] = copyright_value
        catalog_number = _safe_get("catalogNumber")
        if catalog_number:
            data["catalog_number"] = catalog_number

    encoding_date, software_list, lyricist_xml = _parse_encoding_info(path)
    if encoding_date and "date" not in data:
        data["date"] = encoding_date
    if software_list:
        data["software"] = ", ".join(software_list)
    if lyricist_xml and "lyricist" not in data:
        data["lyricist"] = lyricist_xml

    if "title" not in data:
        fallback_title = data.get("movement_name") or _safe_get("workTitle")
        if fallback_title:
            data["title"] = fallback_title

    try:
        analyzed_key = score.analyze("key")
    except Exception:  # pragma: no cover - music21 may raise various errors
        analyzed_key = None
    if analyzed_key is not None:
        data["key"] = analyzed_key.name

    time_signatures = list(score.recurse().getElementsByClass(meter.TimeSignature))
    if time_signatures:
        data["time_signature"] = time_signatures[0].ratioString

    part_names: list[str] = []
    for idx, part in enumerate(score.parts):
        name = part.partName or part.partAbbreviation or part.id
        if name:
            part_names.append(name)
        else:
            part_names.append(f"Part {idx + 1}")
    if part_names:
        data["parts"] = part_names

    # Remove empty values
    return {key: value for key, value in data.items() if value not in (None, "", [])}


def _collect_files(directory: Path) -> list[dict[str, str]]:
    exts = {".pdf", ".musicxml", ".mscz"}
    files: list[dict[str, str]] = []
    for path in sorted(directory.glob("*")):
        if path.is_file() and path.suffix.lower() in exts:
            files.append({"path": relative_to_root(path)})
    return files


def apply_musicxml_metadata(
    readme_path: str | Path,
    musicxml_path: str | Path,
    *,
    key: str = "musicxml",
) -> dict[str, Any]:
    """Extract metadata from MusicXML and merge it into README front matter under the given key."""

    readme_path = Path(readme_path)
    musicxml_path = Path(musicxml_path)

    metadata = extract_musicxml_metadata(musicxml_path)

    if readme_path.exists():
        document = ReadmeDocument.load(readme_path)
    else:
        document = ReadmeDocument(path=readme_path, front_matter={}, body="")

    readme_dir = readme_path.parent
    edition_relative = relative_to_root(readme_dir)
    document.front_matter.setdefault("id", slugify(edition_relative))
    document.front_matter.pop("directory", None)

    composer_readme = readme_dir.parent / "README.md"
    if composer_readme.exists():
        relative_parent = Path(
            os.path.relpath(composer_readme, readme_dir)
        ).as_posix()
        document.front_matter["parent"] = relative_parent

    files = _collect_files(readme_dir)
    readme_relative = relative_to_root(readme_path)
    document.front_matter["files"] = [
        {"path": readme_relative, "title": "README"},
        *files,
    ]

    existing_comment = document.get_composer_from_comment()
    existing_composer_field = document.front_matter.pop("composer", None)

    composer_name = existing_comment
    if composer_name is None and isinstance(existing_composer_field, dict):
        composer_name = existing_composer_field.get("name")
    if composer_name is None and isinstance(existing_composer_field, str):
        composer_name = existing_composer_field

    metadata_composer = metadata.pop("composer", None)
    if composer_name is None:
        composer_name = metadata_composer
    if composer_name is None:
        composer_name = readme_dir.parent.name.replace("_", " ")
    document.set_composer_comment(composer_name)

    title = metadata.pop("title", None)
    if not title:
        title = document.front_matter.get("title")
    if not title:
        title = readme_dir.name.replace("_", " ")
    document.ensure_title(title)

    def _parse_date(value: str | None) -> date | None:
        if isinstance(value, date):
            return value
        if not value:
            return None
        try:
            return date.fromisoformat(value)
        except ValueError:
            return None

    created_value = metadata.pop("date", None)
    created_date = _parse_date(created_value)
    if created_date:
        document.front_matter["created"] = created_date
    else:
        existing_created = document.front_matter.get("created")
        parsed_existing = _parse_date(existing_created)
        if parsed_existing:
            document.front_matter["created"] = parsed_existing

    existing_created = document.front_matter.get("created")
    created_iso = None
    if isinstance(existing_created, date):
        created_iso = existing_created.isoformat()
    elif isinstance(existing_created, str):
        parsed_existing = _parse_date(existing_created)
        if parsed_existing:
            document.front_matter["created"] = parsed_existing
            created_iso = parsed_existing.isoformat()
        else:
            created_iso = existing_created

    existing_updated = document.front_matter.get("updated")
    parsed_updated = _parse_date(existing_updated)
    if parsed_updated:
        document.front_matter["updated"] = parsed_updated
    elif created_iso and existing_created:
        document.front_matter["updated"] = date.fromisoformat(created_iso)

    def _clean_text(value: str | None) -> str | None:
        if isinstance(value, str):
            return " ".join(value.split())
        return value

    license_value = _clean_text(metadata.pop("license", None))
    if license_value:
        document.front_matter["license"] = license_value
    else:
        document.front_matter.setdefault("license", "CC BY-SA 4.0")

    copyright_value = _clean_text(metadata.pop("copyright", None))
    if copyright_value:
        document.front_matter.setdefault("copyright", copyright_value)

    source_value = metadata.pop("source", None)
    if source_value and not document.front_matter.get("source"):
        document.front_matter["source"] = source_value

    document.front_matter.setdefault("editor", "Bas Cornelissen")

    lyricist_value = metadata.pop("lyricist", None)
    if lyricist_value and not document.front_matter.get("lyricist"):
        document.front_matter["lyricist"] = lyricist_value

    document.front_matter["other"] = metadata.copy()

    if not document.body.strip():
        composer_display = composer_name or "Unknown composer"
        document.body = f"# {composer_display} — {title}\n"

    order = [
        "id",
        "parent",
        "title",
        "reference",
        "source",
        "created",
        "updated",
        "copyright",
        "license",
        "editor",
        "lyricist",
        "files",
        "comments",
        "other",
    ]
    document.reorder_front_matter(order)

    document.write()
    return metadata


def _parse_encoding_info(path: Path) -> tuple[str | None, list[str], str | None]:
    try:
        tree = ET.parse(path)
    except ET.ParseError:
        return None, [], None

    root = tree.getroot()
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    def find(tag: str) -> Any:
        return root.find(f".//{ns}{tag}")

    def findall(tag: str) -> list[Any]:
        return root.findall(f".//{ns}{tag}")

    encoding_date_node = find("encoding-date")
    encoding_date = (
        encoding_date_node.text.strip() if encoding_date_node is not None and encoding_date_node.text else None
    )

    software_nodes = findall("software")
    software_list = [
        node.text.strip() for node in software_nodes if node is not None and node.text and node.text.strip()
    ]
    software_list = list(dict.fromkeys(software_list))

    lyricist = None
    for creator in root.findall(f".//{ns}creator"):
        if creator.get("type") in {"lyricist", "poet"} and creator.text and creator.text.strip():
            lyricist = creator.text.strip()
            break

    return encoding_date, software_list, lyricist
