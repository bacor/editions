# Scores

Metadata tooling for the editions stored in this repository.

## CLI commands

- `poetry run extract <edition-dir>` – parse MusicXML files in an edition directory and refresh the edition README front matter.
- `poetry run index [root-dir]` – generate/refresh `index.yaml` files for every composer and the global `editions/index.yaml`, and inject an "Index" table into the corresponding README files.
- `poetry run schema [--format json|yaml] [--out path]` – export the JSON schema for `editions/index.yaml` (defaults to `editions/schema.json`).

## Development

- Install Poetry 1.9+ and run `poetry config virtualenvs.in-project true --global` once to keep the virtualenv in `.venv`.
- Install dependencies with `poetry install`.
- Run the test-suite with `poetry run pytest`.
