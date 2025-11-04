from pathlib import Path
import json
from datetime import date

import pytest
import yaml

import src.index_cli as index_cli_module
import src.readme as readme_module
import src.schema_cli as schema_cli_module

from src.extract_cli import run as extract_cli_run
from src.index_cli import run as index_cli_run
from src.schema_cli import run as schema_cli_run
from src.metadata import (
    Composer,
    ComposerIndex,
    EditionFile,
    EditionIndex,
    EditionMetadata,
    composer_schema,
    composer_schema_dict,
    edition_index_schema,
    edition_index_schema_dict,
    load_composers,
)
from src.musicxml_metadata import apply_musicxml_metadata, extract_musicxml_metadata
from src.readme import ReadmeDocument


def test_index_yaml_matches_schema() -> None:
    yaml_path = Path("editions/index.yaml")
    raw_data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    index = EditionIndex.model_validate(raw_data)
    assert len(index.entries) > 0


def test_json_schema_generation_produces_expected_structure() -> None:
    schema_dict = edition_index_schema_dict()
    assert schema_dict["title"] == "EditionIndex"
    assert "entries" in schema_dict["properties"]

    schema_json = edition_index_schema()
    parsed = json.loads(schema_json)
    assert parsed == schema_dict


def test_yaml_schema_generation_is_valid_yaml() -> None:
    schema_yaml = edition_index_schema(format="yaml")
    parsed = yaml.safe_load(schema_yaml)
    assert parsed == edition_index_schema_dict()


def test_file_paths_must_be_relative() -> None:
    with pytest.raises(ValueError):
        EditionFile(path="/absolute/path.pdf")


def test_file_title_cannot_be_extension_only() -> None:
    with pytest.raises(ValueError):
        EditionFile(path="score.pdf", title="PDF")


def test_requires_core_fields_without_parent() -> None:
    with pytest.raises(ValueError):
        EditionMetadata(
            id="demo-piece",
            files=[EditionFile(path="score.pdf")],
        )


def test_parent_allows_optional_fields() -> None:
    metadata = EditionMetadata(
        id="demo-piece-variant",
        parent="README.md",
        files=[EditionFile(path="transposed.musicxml")],
    )
    assert metadata.parent == "README.md"

def test_files_cannot_be_empty() -> None:
    with pytest.raises(ValueError):
        EditionMetadata(
            id="demo-piece",
            composer=Composer(id="demo-composer", name="Demo Composer"),
            title="Title",
            copyright="Copyright",
            license="CC BY-SA 4.0",
            files=[],
        )


def test_composer_required_when_no_parent() -> None:
    with pytest.raises(ValueError):
        EditionMetadata(
            id="demo-piece",
            title="Title",
            copyright="Copyright",
            license="CC BY-SA 4.0",
            files=[EditionFile(path="score.pdf")],
        )


def test_metadata_accepts_composer_object() -> None:
    metadata = EditionMetadata(
        id="demo-piece",
        composer=Composer(id="demo-composer", name="Demo Composer"),
        title="Title",
        copyright="Copyright",
        license="CC BY-SA 4.0",
        files=[EditionFile(path="score.pdf")],
        comments="Some note",
    )
    assert metadata.composer.name == "Demo Composer"
    assert metadata.comments == "Some note"


def test_composer_yaml_matches_schema(tmp_path: Path) -> None:
    sample_path = tmp_path / "composers.yaml"
    sample_path.write_text(
        yaml.safe_dump(
            [
                {
                    "id": "bach-cpe",
                    "name": "Carl Philipp Emanuel Bach",
                    "lastname": "Bach",
                    "initials": "CPE",
                    "year_born": 1714,
                    "year_death": 1788,
                    "wikidata": "https://www.wikidata.org/wiki/Q1331",
                },
                {
                    "id": "albert-h",
                    "name": "Heinrich Albert",
                },
            ]
        ),
        encoding="utf-8",
    )

    composers = load_composers(sample_path)
    assert isinstance(composers, ComposerIndex)
    assert len(composers.entries) == 2


def test_composer_schema_roundtrip() -> None:
    schema_dict = composer_schema_dict()
    assert schema_dict["title"] == "ComposerIndex"
    assert "entries" in schema_dict["properties"]

    parsed_json = json.loads(composer_schema())
    assert parsed_json == schema_dict

    parsed_yaml = yaml.safe_load(composer_schema(format="yaml"))
    assert parsed_yaml == schema_dict


def test_readme_roundtrip_and_section_edit(tmp_path: Path) -> None:
    readme_path = tmp_path / "README.md"
    readme_path.write_text(
        "---\n"
        "composer:\n"
        "  id: demo\n"
        "  name: Demo Composer\n"
        "---\n"
        "\n"
        "# Title\n\n"
        "## Works\n"
        "Old content\n\n"
        "## Notes\n"
        "Existing note\n",
        encoding="utf-8",
    )

    doc = ReadmeDocument.load(readme_path)
    doc.set_front_matter("extra", True)
    doc.set_section("Works", "| Title |\n| ----- |\n| Piece |\n")
    doc.write()

    updated = readme_path.read_text(encoding="utf-8")
    assert "extra: true" in updated
    assert "| Piece |" in updated
    assert "Old content" not in updated
    assert "## Notes" in updated


def test_set_section_appends_when_missing() -> None:
    doc = ReadmeDocument(path=None, front_matter={}, body="# Intro\n")
    doc.set_section("Works", "Listing\n")
    assert "## Works" in doc.body
    assert "Listing" in doc.body


def test_extract_musicxml_metadata_returns_expected_fields(tmp_path: Path) -> None:
    from music21 import metadata as m21metadata, note, stream, meter

    score = stream.Score()
    score.metadata = m21metadata.Metadata()
    score.metadata.title = "Demo Piece"
    score.metadata.composer = "Demo Composer"
    score.metadata.movementName = "Movement I"
    score.metadata.movementNumber = "1"
    score.metadata.date = "2024"

    part = stream.Part()
    part.id = "part"
    part.partName = "Voice"
    part.append(meter.TimeSignature("3/4"))
    part.append(note.Note("C4"))
    score.insert(0, part)

    musicxml_path = tmp_path / "score.musicxml"
    score.write("musicxml", fp=musicxml_path)

    metadata = extract_musicxml_metadata(musicxml_path)
    assert metadata["title"] == "Demo Piece"
    assert metadata["composer"] == "Demo Composer"
    assert metadata["movement_name"] == "Movement I"
    assert metadata["time_signature"] == "3/4"
    assert "parts" in metadata


def test_apply_musicxml_metadata_updates_front_matter_without_touching_body(tmp_path: Path) -> None:
    readme_path = tmp_path / "README.md"
    readme_path.write_text(
        "---\n"
        "composer:\n"
        "  id: demo\n"
        "  name: Demo Composer\n"
        "---\n"
        "\n"
        "# Existing Content\n",
        encoding="utf-8",
    )

    from music21 import metadata as m21metadata, note, stream, meter

    score = stream.Score()
    score.metadata = m21metadata.Metadata()
    score.metadata.title = "Demo Piece"
    score.metadata.composer = "Another Composer"
    score.metadata.date = "2024-05-01"
    score.metadata.lyricist = "Lyricist Name"

    part = stream.Part()
    part.partName = "Voice"
    part.append(meter.TimeSignature("4/4"))
    part.append(note.Note("D4"))
    score.insert(0, part)

    musicxml_path = tmp_path / "piece.musicxml"
    score.write("musicxml", fp=musicxml_path)

    from xml.etree import ElementTree as ET

    tree = ET.parse(musicxml_path)
    root = tree.getroot()
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    def q(tag: str) -> str:
        return f"{ns}{tag}" if ns else tag

    identification = root.find(q("identification"))
    if identification is None:
        identification = ET.SubElement(root, q("identification"))
    encoding = identification.find(q("encoding"))
    if encoding is None:
        encoding = ET.SubElement(identification, q("encoding"))
    for existing in list(encoding.findall(q("software"))):
        encoding.remove(existing)
    for existing in list(encoding.findall(q("software"))):
        encoding.remove(existing)
    encoding_date = encoding.find(q("encoding-date"))
    if encoding_date is None:
        encoding_date = ET.SubElement(encoding, q("encoding-date"))
    encoding_date.text = "2024-05-01"
    software = ET.SubElement(encoding, q("software"))
    software.text = "MuseScore 4"

    for existing in list(identification.findall(q("creator"))):
        if existing.get("type") == "lyricist":
            identification.remove(existing)
    lyricist = ET.SubElement(identification, q("creator"), attrib={"type": "lyricist"})
    lyricist.text = "Lyricist Name"
    tree.write(musicxml_path, encoding="utf-8", xml_declaration=True)

    apply_musicxml_metadata(readme_path, musicxml_path)

    document = ReadmeDocument.load(readme_path)
    assert document.front_comment == "Composer: Demo Composer (details inherited from parent)"
    assert document.front_matter["title"] == "Demo Piece"
    assert document.front_matter["created"] == date(2024, 5, 1)
    assert document.front_matter["updated"] == date(2024, 5, 1)
    assert document.front_matter["license"] == "CC BY-SA 4.0"
    assert document.front_matter["editor"] == "Bas Cornelissen"
    files = document.front_matter["files"]
    assert files[0]["title"] == "README"
    assert any(entry["path"].endswith("piece.musicxml") for entry in files)
    other = document.front_matter["other"]
    assert other["parts"] == ["Voice"]
    assert "MuseScore 4" in other["software"]
    assert document.front_matter["lyricist"] == "Lyricist Name"
    assert document.body == "\n# Existing Content\n"


def _write_demo_musicxml(path: Path) -> None:
    from music21 import metadata as m21metadata, note, stream, meter
    from xml.etree import ElementTree as ET

    score = stream.Score()
    score.metadata = m21metadata.Metadata()
    score.metadata.title = "Demo Piece"
    score.metadata.composer = "Demo Composer"
    score.metadata.date = "2024-05-01"
    part = stream.Part()
    part.partName = "Voice"
    part.append(meter.TimeSignature("4/4"))
    part.append(note.Note("C4"))
    score.insert(0, part)
    score.write("musicxml", fp=path)

    tree = ET.parse(path)
    root = tree.getroot()
    ns = ""
    if root.tag.startswith("{"):
        ns = root.tag.split("}")[0] + "}"

    def q(tag: str) -> str:
        return f"{ns}{tag}" if ns else tag

    identification = root.find(q("identification"))
    if identification is None:
        identification = ET.SubElement(root, q("identification"))

    encoding = identification.find(q("encoding"))
    if encoding is None:
        encoding = ET.SubElement(identification, q("encoding"))

    encoding_date = encoding.find(q("encoding-date"))
    if encoding_date is None:
        encoding_date = ET.SubElement(encoding, q("encoding-date"))
    encoding_date.text = "2024-05-01"

    for existing in list(encoding.findall(q("software"))):
        encoding.remove(existing)
    software = ET.SubElement(encoding, q("software"))
    software.text = "MuseScore 4"

    for existing in list(identification.findall(q("creator"))):
        if existing.get("type") == "lyricist":
            identification.remove(existing)
    lyricist = ET.SubElement(identification, q("creator"), attrib={"type": "lyricist"})
    lyricist.text = "Lyricist Name"

    tree.write(path, encoding="utf-8", xml_declaration=True)


def test_cli_updates_readme(tmp_path: Path) -> None:
    edition_dir = tmp_path / "edition"
    edition_dir.mkdir()
    readme_path = edition_dir / "README.md"
    readme_path.write_text(
        "---\n"
        "composer:\n"
        "  id: demo\n"
        "  name: Demo Composer\n"
        "---\n\n# Body\n",
        encoding="utf-8",
    )
    musicxml_path = edition_dir / "score.musicxml"
    _write_demo_musicxml(musicxml_path)

    exit_code = extract_cli_run([str(edition_dir)])
    assert exit_code == 0

    doc = ReadmeDocument.load(readme_path)
    assert doc.front_comment == "Composer: Demo Composer (details inherited from parent)"
    assert doc.front_matter["title"] == "Demo Piece"
    assert doc.front_matter["created"] == date(2024, 5, 1)
    assert doc.front_matter["updated"] == date(2024, 5, 1)
    assert doc.front_matter["license"] == "CC BY-SA 4.0"
    assert doc.front_matter["editor"] == "Bas Cornelissen"
    files = doc.front_matter["files"]
    assert files[0]["title"] == "README"
    assert files[0]["path"].endswith("README.md")
    assert any(entry["path"].endswith("score.musicxml") for entry in files)
    other = doc.front_matter["other"]
    assert other["parts"] == ["Voice"]
    assert "MuseScore 4" in other["software"]
    assert doc.front_matter["lyricist"] == "Lyricist Name"


def test_cli_dry_run_does_not_modify_readme(tmp_path: Path) -> None:
    edition_dir = tmp_path / "edition"
    edition_dir.mkdir()
    readme_path = edition_dir / "README.md"
    original_content = (
        "---\n"
        "composer:\n"
        "  id: demo\n"
        "  name: Demo Composer\n"
        "---\n\n# Body\n"
    )
    readme_path.write_text(original_content, encoding="utf-8")
    musicxml_path = edition_dir / "score.musicxml"
    _write_demo_musicxml(musicxml_path)

    exit_code = extract_cli_run(["--dry-run", str(edition_dir)])
    assert exit_code == 0
    assert readme_path.read_text(encoding="utf-8") == original_content


def test_cli_creates_readme_when_missing(tmp_path: Path) -> None:
    edition_dir = tmp_path / "edition"
    edition_dir.mkdir()
    musicxml_path = edition_dir / "score.musicxml"
    _write_demo_musicxml(musicxml_path)

    exit_code = extract_cli_run([str(edition_dir)])
    assert exit_code == 0

    readme_path = edition_dir / "README.md"
    assert readme_path.exists()
    doc = ReadmeDocument.load(readme_path)
    assert doc.front_comment == "Composer: Demo Composer (details inherited from parent)"
    assert doc.front_matter["title"] == "Demo Piece"
    assert doc.front_matter["created"] == date(2024, 5, 1)
    assert doc.front_matter["updated"] == date(2024, 5, 1)
    assert doc.front_matter["license"] == "CC BY-SA 4.0"
    assert doc.front_matter["editor"] == "Bas Cornelissen"
    files = doc.front_matter["files"]
    assert files[0]["title"] == "README"
    assert files[0]["path"].endswith("README.md")
    assert any(entry["path"].endswith("score.musicxml") for entry in files)
    other = doc.front_matter["other"]
    assert other["parts"] == ["Voice"]
    assert "MuseScore 4" in other["software"]
    assert doc.front_matter["lyricist"] == "Lyricist Name"
    first_line = doc.body.lstrip().splitlines()[0]
    assert first_line == "# Demo Composer — Demo Piece"


def test_cli_sets_parent_when_composer_readme_exists(tmp_path: Path) -> None:
    composer_dir = tmp_path / "composer"
    edition_dir = composer_dir / "edition"
    edition_dir.mkdir(parents=True)

    composer_readme = composer_dir / "README.md"
    composer_readme.write_text(
        "---\ncomposer:\n  id: demo-composer\n  name: Demo Composer\n---\n", encoding="utf-8"
    )

    musicxml_path = edition_dir / "score.musicxml"
    _write_demo_musicxml(musicxml_path)

    exit_code = extract_cli_run([str(edition_dir)])
    assert exit_code == 0

    doc = ReadmeDocument.load(edition_dir / "README.md")
    assert doc.front_matter.get("parent") == "../README.md"
    assert doc.front_comment == "Composer: Demo Composer (details inherited from parent)"


def test_index_cli_updates_project_readme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    editions_root = repo_root / "editions"
    composer_dir = editions_root / "composer"
    edition_dir = composer_dir / "work"
    edition_dir.mkdir(parents=True)

    (repo_root / "README.md").write_text("# Root\n\nSome intro\n", encoding="utf-8")

    composer_dir.joinpath("README.md").write_text(
        "---\n"
        "composer:\n"
        "  id: composer-id\n"
        "  name: Composer Name\n"
        "  lastname: Name\n"
        "---\n\n# Composer Name\n",
        encoding="utf-8",
    )

    edition_dir.joinpath("README.md").write_text(
        "---\n"
        "# Composer: Composer Name (details inherited from parent)\n"
        "id: composer-work\n"
        "parent: ../README.md\n"
        "title: Work Title\n"
        "source: Source Info\n"
        "created: 2024-01-01\n"
        "copyright: Copyright Info\n"
        "license: CC BY-SA 4.0\n"
        "files:\n"
        "  - path: editions/composer/work/README.md\n"
        "    title: README\n"
        "  - path: editions/composer/work/work.pdf\n"
        "---\n\n# Composer Name — Work Title\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(index_cli_module, "PROJECT_ROOT", repo_root)
    monkeypatch.setattr(readme_module, "PROJECT_ROOT", repo_root)

    exit_code = index_cli_run([str(editions_root)])
    assert exit_code == 0

    root_readme = (repo_root / "README.md").read_text(encoding="utf-8")
    assert "## Index" in root_readme
    assert "| Composer | Title | Ref. | PDF | MusicXML |" in root_readme


def test_schema_cli_writes_default_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    repo_root = tmp_path / "repo"
    editions_root = repo_root / "editions"
    editions_root.mkdir(parents=True)

    monkeypatch.setattr(schema_cli_module, "PROJECT_ROOT", repo_root)

    exit_code = schema_cli_run([])
    assert exit_code == 0

    expected_path = editions_root / "schema.json"
    assert expected_path.exists()
    content = expected_path.read_text(encoding="utf-8")
    parsed = json.loads(content)
    assert parsed == edition_index_schema_dict()
