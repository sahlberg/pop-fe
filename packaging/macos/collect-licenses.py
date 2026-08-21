#!/usr/bin/env python3
"""Collect license texts from the pinned Python build environment."""

from __future__ import annotations

import argparse
import importlib.metadata
import re
import shutil
from pathlib import Path


LICENSE_MARKERS = ("license", "copying", "notice")


def safe_name(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.") or "unknown"


def collect(destination: Path) -> None:
    destination = destination.resolve()
    if destination.exists():
        shutil.rmtree(destination)
    destination.mkdir(parents=True)
    manifest = []

    distributions = sorted(
        importlib.metadata.distributions(),
        key=lambda distribution: (distribution.metadata.get("Name") or "").lower(),
    )
    for distribution in distributions:
        name = distribution.metadata.get("Name") or "unknown"
        package_root = destination / safe_name(name)
        copied = set()
        for relative in distribution.files or ():
            parts = relative.parts
            if not parts or not any(part.endswith(".dist-info") for part in parts):
                continue
            if not any(marker in relative.name.lower() for marker in LICENSE_MARKERS):
                continue
            source = Path(distribution.locate_file(relative))
            if not source.is_file():
                continue
            dist_info_index = next(
                index for index, part in enumerate(parts) if part.endswith(".dist-info")
            )
            license_relative = Path(*parts[dist_info_index + 1 :])
            target = package_root / license_relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.add(target.relative_to(destination))

        if copied:
            manifest.append(f"{name}=={distribution.version}")
            manifest.extend(f"  {path}" for path in sorted(copied))

    (destination / "MANIFEST.txt").write_text(
        "Python package license files collected at build time\n\n"
        + "\n".join(manifest)
        + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("destination", type=Path)
    arguments = parser.parse_args()
    collect(arguments.destination)


if __name__ == "__main__":
    main()
