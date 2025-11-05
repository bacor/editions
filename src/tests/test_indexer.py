from pathlib import Path

import yaml

from src.index_cli import run as index_cli_run


def test_index_cli_builds_composer_and_global_indexes(tmp_path: Path) -> None:
    editions_root = tmp_path / "editions"
    composer_dir = editions_root / "composer"
    edition_dir = composer_dir / "work"
    edition_dir.mkdir(parents=True)

    composer_readme = composer_dir / "README.md"
    composer_readme.write_text(
        "---\n"
        "composer:\n"
        "  id: composer-id\n"
        "  name: Composer Name\n"
        "  lastname: Name\n"
        "---\n\n# Composer Name\n",
        encoding="utf-8",
    )

    edition_readme = edition_dir / "README.md"
    edition_readme.write_text(
        "---\n"
        "# Composer: Composer Name (details inherited from parent)\n"
        "id: composer-work\n"
        "parent: ../README.md\n"
        "title: Work Title\n"
        "reference: Wq. 162\n"
        "source: \"  Source Info  \"\n"
        "created: 2024-01-01\n"
        "copyright: Copyright Info\n"
        "license: CC BY-SA 4.0\n"
        "files:\n"
        "  - path: editions/composer/work/README.md\n"
        "    title: README\n"
        "  - path: editions/composer/work/work.pdf\n"
        "comments: \"  First draft  \"\n"
        "---\n\n# Composer Name — Work Title\n",
        encoding="utf-8",
    )

    # Build indexes for the root directory
    exit_code = index_cli_run([str(editions_root)])
    assert exit_code == 0

    composer_index_path = composer_dir / "index.yaml"
    global_index_path = editions_root / "index.yaml"

    assert composer_index_path.exists()
    assert global_index_path.exists()

    composer_index = yaml.safe_load(composer_index_path.read_text(encoding="utf-8"))
    global_index = yaml.safe_load(global_index_path.read_text(encoding="utf-8"))

    assert isinstance(composer_index, list)
    edition_entry = composer_index[0]
    composer_info = edition_entry["composer"]
    assert composer_info["id"] == "composer-id"
    assert composer_info["name"] == "Composer Name"
    assert edition_entry["source"] == "Source Info"
    assert edition_entry["comments"] == "First draft"
    assert edition_entry["created"] == "2024-01-01"
    assert edition_entry["updated"] == "2024-01-01"
    assert edition_entry["reference"] == "Wq. 162"
    assert "lyricist" not in edition_entry
    assert "other" not in edition_entry

    assert isinstance(global_index, list)
    first_global = global_index[0]
    assert first_global["composer"]["id"] == "composer-id"
    assert first_global["source"] == "Source Info"

    composer_readme = (composer_dir / "README.md").read_text(encoding="utf-8")
    assert "## Index" in composer_readme
    assert "| Composer | Title | Ref. | PDF | MusicXML |" in composer_readme


def test_index_cli_handles_composer_directory(tmp_path: Path) -> None:
    composer_dir = tmp_path / "composer"
    edition_dir = composer_dir / "work"
    edition_dir.mkdir(parents=True)

    composer_dir.joinpath("README.md").write_text(
        "---\ncomposer:\n  name: Composer Name\n---\n",
        encoding="utf-8",
    )
    edition_dir.joinpath("README.md").write_text(
        "---\n# Composer: Composer Name (details inherited from parent)\n"
        "id: test-work\n"
        "license: CC BY-SA 4.0\n"
        "files:\n  - path: editions/composer/work/README.md\n    title: README\n"
        "---\n",
        encoding="utf-8",
    )

    exit_code = index_cli_run([str(composer_dir)])
    assert exit_code == 0
    assert (composer_dir / "index.yaml").exists()

    composer_readme = (composer_dir / "README.md").read_text(encoding="utf-8")
    assert "## Index" in composer_readme
