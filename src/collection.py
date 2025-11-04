# -*- coding: utf-8 -*-
# -------------------------------------------------------------------
# Author: Bas Cornelissen
# Copyright © 2024 Bas Cornelissen
# -------------------------------------------------------------------
import glob
import os
import subprocess
from typing import Iterable

import yaml
from tqdm.auto import tqdm

MSCORE_EXECUTABLE = "/Applications/MuseScore 4.app/Contents/MacOS/mscore"

CUR_DIR = os.path.dirname(__file__)
ROOT_DIR = os.path.abspath(os.path.join(CUR_DIR, os.pardir))


class Collection:
    # Memoized properties
    _works = None

    config = {
        "include": ["**/*.mscz"],
        "exclude": ["*-draft/*"],
        "exports": {"pdf": {"extension": "pdf"}, "musicxml": {"extension": "musicxml"}},
    }

    def __init__(
        self,
        name: str | None = None,
        directory: str | None = None,
        config_fn: str = "config.yaml",
        mscore_executable: str = MSCORE_EXECUTABLE,
        config: dict | None = None,
    ) -> None:
        if name is None and directory is None:
            raise ValueError("Either 'name' or 'directory' must be provided")
        elif name is None:
            self.dir = directory
            self.name = os.path.basename(directory)
        elif directory is None:
            self.name = name
            self.dir = os.path.join(ROOT_DIR, "scores", self.name)
        if not os.path.exists(self.dir):
            raise FileExistsError(
                f"Collection not found (name={self.name}): {self.dir}"
            )

        # Set MuseScore executable. Only test if it exists when needed.
        self.mscore_exec = mscore_executable

        # Update configuration
        config_path = os.path.join(self.dir, config_fn)
        if os.path.exists(config_path):
            with open(config_path, "r") as file:
                loaded_config = yaml.safe_load(file)
                if loaded_config is not None:
                    self.config.update(loaded_config)
        if config is not None:
            self.config.update(config)

    def __len__(self) -> int:
        return len(self.works)

    def __repr__(self) -> str:
        return f"<Collection {self.name} of {len(self)} works>"

    @property
    def works(self) -> list[dict]:
        if self._works is None:
            excluded = []
            for pattern in self.config["exclude"]:
                excluded.extend(
                    glob.glob(os.path.join(self.dir, pattern), recursive=True)
                )

            included = []
            for pattern in self.config["include"]:
                included.extend(
                    glob.glob(os.path.join(self.dir, pattern), recursive=True)
                )

            self._works = []
            paths = sorted([fn for fn in included if fn not in excluded])
            for path in paths:
                name, _ = os.path.basename(path).split(".")
                work = {
                    "name": name,
                    "path": path,
                    "filename": os.path.basename(path),
                    "exports": {},
                }
                basepath = os.path.splitext(path)[0]
                for export_type, export_config in self.config["exports"].items():
                    work["exports"][export_type] = (
                        f"{basepath}.{export_config['extension']}"
                    )
                self._works.append(work)

        return self._works

    def clear_export(self, export_type: str) -> None:
        if export_type not in self.config["exports"]:
            raise ValueError(f'Unknown export type "{export_type}"')

        for work in self.works:
            path = work["exports"][export_type]
            if os.path.exists(path):
                os.remove(path)

    def clear_all_exports(self) -> None:
        for export_type in self.config["exports"].keys():
            self.clear_export(export_type)

    def mscore(self, *args: Iterable[str]) -> subprocess.CompletedProcess:
        """Run the mscore executable in a subprocess"""
        if not os.path.exists(self.mscore_exec):
            raise FileNotFoundError(
                f"MuseScore executable not found: {self.mscore_exec}"
            )
        return subprocess.run([self.mscore_exec, *args])

    def export_work(self, work: dict, export_type: str, refresh: bool = False) -> None:
        if export_type not in self.config["exports"]:
            raise ValueError(f'Unknown export type "{export_type}"')

        source = work["path"]
        target = work["exports"][export_type]
        if not os.path.exists(source):
            raise FileNotFoundError(f"Work not found: {source}")

        if not os.path.exists(target) or refresh:
            result = self.mscore("-o", target, source)
            if result.returncode != 0:
                raise Exception(
                    f"Error converting {source} to {export_type}: {result.stderr}"
                )

    def export(
        self, export_types: list[str] | None = None, refresh: bool = False
    ) -> None:
        if export_types is None:
            export_types = list(self.config["exports"].keys())

        exports = [
            (work, export_type) for work in self.works for export_type in export_types
        ]

        for work, export_type in tqdm(exports):
            self.export_work(work, export_type, refresh=refresh)
