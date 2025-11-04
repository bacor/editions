import copy
from pathlib import Path

import pytest

from src.collection import Collection


@pytest.fixture(autouse=True)
def reset_collection_state():
    original_config = copy.deepcopy(Collection.config)
    try:
        yield
    finally:
        Collection.config = copy.deepcopy(original_config)
        Collection._works = None


@pytest.fixture
def collection_dir(tmp_path: Path) -> Path:
    collection_root = tmp_path / "demo"
    collection_root.mkdir()
    for name in ("first_piece", "second_piece"):
        (collection_root / f"{name}.mscz").write_text("dummy musescore data")
    return collection_root


def test_works_are_discovered(collection_dir: Path) -> None:
    collection = Collection(directory=str(collection_dir))

    works = collection.works
    assert len(works) == 2
    assert {work["name"] for work in works} == {"first_piece", "second_piece"}
    assert all("pdf" in work["exports"] for work in works)


def test_clear_export_removes_existing_files(collection_dir: Path) -> None:
    collection = Collection(directory=str(collection_dir))
    pdf_targets = [Path(work["exports"]["pdf"]) for work in collection.works]

    for target in pdf_targets:
        target.touch()
        assert target.exists()

    collection.clear_export("pdf")
    assert all(not target.exists() for target in pdf_targets)


def test_clear_export_rejects_unknown_type(collection_dir: Path) -> None:
    collection = Collection(directory=str(collection_dir))

    with pytest.raises(ValueError):
        collection.clear_export("unknown")


def test_mscore_requires_existing_executable(collection_dir: Path, tmp_path: Path) -> None:
    missing_exec = tmp_path / "not-there"
    collection = Collection(
        directory=str(collection_dir), mscore_executable=str(missing_exec)
    )

    with pytest.raises(FileNotFoundError):
        collection.mscore("--version")
