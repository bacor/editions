from __future__ import annotations

from datetime import date
from pathlib import Path
import json
from typing import Any, Literal
import yaml
from pydantic import (
    AnyUrl,
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)


class Composer(BaseModel):
    """Metadata describing a composer referenced by editions."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ...,
        description="Stable identifier for the composer (referenced in metadata).",
        examples=["bach-cpe"],
    )
    name: str = Field(
        ...,
        description="Full display name of the composer.",
    )
    lastname: str | None = Field(
        default=None,
        description="Composer's family name.",
    )
    initials: str | None = Field(
        default=None,
        description="Initials used in abbreviations.",
    )
    year_born: int | None = Field(
        default=None,
        description="Year of birth.",
        ge=0,
    )
    year_death: int | None = Field(
        default=None,
        description="Year of death.",
        ge=0,
    )
    wikidata: AnyUrl | None = Field(
        default=None,
        description="Optional Wikidata reference.",
    )
    @field_validator("id")
    @classmethod
    def _ensure_slug_id(cls, value: str) -> str:
        if value.strip() != value:
            raise ValueError("composer id must not include leading or trailing whitespace")
        if " " in value:
            raise ValueError("composer id must not contain spaces")
        return value

    @model_validator(mode="after")
    def _check_years(self) -> "Composer":
        if self.year_born is not None and self.year_death is not None:
            if self.year_death < self.year_born:
                raise ValueError("year_death cannot be earlier than year_born")
        return self


class EditionFile(BaseModel):
    """Represents a file associated with an edition."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None,
        description="Optional human-readable label for this file (e.g. Full score PDF).",
    )
    path: str = Field(
        ...,
        description="Relative path to the file (relative to the README that defines this metadata).",
    )

    @field_validator("path")
    @classmethod
    def _ensure_relative_path(cls, value: str) -> str:
        path = Path(value)
        if path.is_absolute():
            raise ValueError("file paths must be relative")
        return value

    @field_validator("title")
    @classmethod
    def _reject_extension_only_titles(cls, value: str | None) -> str | None:
        if value is None:
            return value
        normalized = value.strip().lower()
        if normalized in {"pdf", "musicxml"}:
            raise ValueError("omit file titles that only repeat the file extension")
        return value


class EditionMetadata(BaseModel):
    """Metadata describing a single edition within the repository."""

    model_config = ConfigDict(extra="forbid")

    id: str = Field(
        ...,
        description="Stable identifier for this edition (should be unique across the repository).",
    )
    parent: str | None = Field(
        default=None,
        description="Relative path to another metadata file this entry inherits from.",
    )
    composer: Composer | None = Field(
        default=None,
        description="Composer details for the edition.",
    )
    title: str | None = Field(
        default=None,
        description="Primary title of the piece.",
    )
    subtitle: str | None = Field(
        default=None,
        description="Optional subtitle or additional descriptor.",
    )
    reference: str | None = Field(
        default=None,
        description="Catalogue reference number or other identifying code.",
    )
    source: str | None = Field(
        default=None,
        description="Bibliographic information about the engraving source.",
    )
    created: date | None = Field(
        default=None,
        description="Date the edition metadata entry was created (ISO format).",
    )
    updated: date | None = Field(
        default=None,
        description="Date the metadata was last updated (ISO format).",
    )
    readme: str | None = Field(
        default=None,
        description="Optional relative path to an edition-specific README file.",
    )
    copyright: str | None = Field(
        default=None,
        description="Copyright notice covering the materials in this edition.",
    )
    license: str | None = Field(
        default=None,
        description="License statement for the edition.",
    )
    editor: str | None = Field(
        default=None,
        description="Editor responsible for this edition metadata.",
    )
    lyricist: str | None = Field(
        default=None,
        description="Lyricist associated with the work, when applicable.",
    )
    files: list[EditionFile] = Field(
        ...,
        description="Files associated with the edition (e.g. PDFs, MusicXML exports).",
    )
    other: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata that does not fit structured fields.",
    )
    comments: str | None = Field(
        default=None,
        description="Optional free-form comments about the edition.",
    )

    @field_validator("files")
    @classmethod
    def _ensure_files_not_empty(cls, value: list[EditionFile]) -> list[EditionFile]:
        if not value:
            raise ValueError("at least one file must be provided")
        return value

    @field_validator("parent")
    @classmethod
    def _ensure_parent_is_relative(cls, value: str | None) -> str | None:
        if value is None:
            return value
        path = Path(value)
        if path.is_absolute():
            raise ValueError("parent path must be relative")
        return value

    @model_validator(mode="after")
    def _validate_required_fields(self) -> "EditionMetadata":
        required_fields = ["composer", "title", "copyright", "license"]
        if self.parent is None:
            missing = [
                field
                for field in required_fields
                if getattr(self, field) in (None, "", [])
            ]
            if missing:
                raise ValueError(
                    f"Missing required fields for standalone metadata: {', '.join(missing)}"
                )
        if self.other is not None and not isinstance(self.other, dict):
            raise ValueError("other must be a mapping when provided")
        return self


class ComposerIndexEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str | None = None
    lastname: str | None = None
    initials: str | None = None
    year_born: int | None = None
    year_death: int | None = None
    wikidata: AnyUrl | None = None
    readme: str | None = None


class EditionListing(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = None
    composer: ComposerIndexEntry
    parent: str | None = None
    title: str | None = None
    reference: str | None = None
    source: str | None = None
    created: date | str | None = None
    copyright: str | None = None
    license: str | None = None
    readme: str | None = None
    files: list[EditionFile] | None = None
    comments: str | None = None


class EditionIndex(RootModel[list[EditionListing]]):
    """Container that aggregates all edition metadata entries."""

    @property
    def entries(self) -> list[EditionListing]:
        return self.root


def load_index(path: str | Path) -> EditionIndex:
    """Parse the YAML index file and return a validated EditionIndex."""

    with Path(path).open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return EditionIndex.model_validate(data)


def edition_index_schema_dict() -> dict[str, Any]:
    """Return the JSON Schema dictionary for the EditionIndex model."""

    return EditionIndex.model_json_schema()


class ComposerIndex(BaseModel):
    """Container that aggregates all composer metadata entries."""

    model_config = ConfigDict(extra="forbid")

    entries: list[Composer] = Field(
        ...,
        description="All composer entries available for lookups.",
    )


def load_composers(path: str | Path) -> ComposerIndex:
    """Parse the composers YAML file and return a validated ComposerIndex."""

    with Path(path).open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    if not isinstance(data, list):
        raise ValueError("expected the composers YAML to contain a list of entries")
    return ComposerIndex(entries=data)


def composer_schema_dict() -> dict[str, Any]:
    """Return the JSON Schema dictionary for the ComposerIndex model."""

    return ComposerIndex.model_json_schema()


def composer_schema(format: Literal["json", "yaml"] = "json", *, indent: int = 2) -> str:
    """Render the composer schema as JSON or YAML."""

    schema = composer_schema_dict()
    if format == "json":
        return json.dumps(schema, indent=indent)
    return yaml.safe_dump(schema, sort_keys=False)


def write_composer_schema(
    path: str | Path, *, format: Literal["json", "yaml"] | None = None, indent: int = 2
) -> None:
    """Write the composer schema to disk, inferring the format from the file suffix when omitted."""

    target_path = Path(path)
    schema_format = format
    if schema_format is None:
        if target_path.suffix.lower() in {".yaml", ".yml"}:
            schema_format = "yaml"
        else:
            schema_format = "json"

    schema_text = composer_schema(format=schema_format, indent=indent)
    target_path.write_text(schema_text, encoding="utf-8")


def edition_index_schema(
    format: Literal["json", "yaml"] = "json", *, indent: int = 2
) -> str:
    """Render the EditionIndex schema as a JSON or YAML string."""

    schema = edition_index_schema_dict()
    if format == "json":
        return json.dumps(schema, indent=indent)
    return yaml.safe_dump(schema, sort_keys=False)


def write_edition_index_schema(
    path: str | Path, *, format: Literal["json", "yaml"] | None = None, indent: int = 2
) -> None:
    """Write the EditionIndex schema to disk.

    If ``format`` is omitted, it will be inferred from the file suffix (``.json`` / ``.yaml`` / ``.yml``).
    """

    target_path = Path(path)
    schema_format = format
    if schema_format is None:
        if target_path.suffix.lower() in {".yaml", ".yml"}:
            schema_format = "yaml"
        else:
            schema_format = "json"

    schema_text = edition_index_schema(format=schema_format, indent=indent)
    target_path.write_text(schema_text, encoding="utf-8")
