"""Shared PyInstaller inputs for the macOS POP-FE distributions."""

from __future__ import annotations

import os
from pathlib import Path

import nodejs_wheel
from PyInstaller.utils.hooks import collect_data_files

HELPER_NAMES = (
    "atracdenc",
    "binmerge",
    "chdman",
    "cue2cu2",
    "ffmpeg",
    "lcp",
    "pkg",
    "psxund",
    "sign3",
    "xdelta3",
)

RESOURCE_DIRECTORIES = (
    "libcrypt",
    "ppf",
    "ps3configs",
    "pspconfigs",
    "romhacks",
)


def packaging_inputs(repository_root: Path, ui_file: str | None = None):
    """Return data, binaries, and hidden imports common to each target."""
    helper_root = Path(
        os.environ.get(
            "POPFE_HELPER_STAGE",
            repository_root / "build" / "macos" / "helpers",
        )
    ).resolve()
    missing = [name for name in HELPER_NAMES if not (helper_root / name).is_file()]
    if missing:
        raise SystemExit(
            "Missing staged macOS helpers: "
            + ", ".join(missing)
            + ". Run packaging/macos/build-helpers.sh first."
        )

    datas = [
        (str(repository_root / "PS3LOGO.DAT"), "."),
        (str(repository_root / "LICENCE-LGPL-2.1.txt"), "."),
        (str(repository_root / "THIRD_PARTY_NOTICES.md"), "."),
        (str(repository_root / "build" / "macos" / "licenses"), "licenses"),
    ]
    datas.extend(
        (str(repository_root / directory), directory)
        for directory in RESOURCE_DIRECTORIES
    )
    if ui_file:
        datas.append((str(repository_root / ui_file), "."))
    datas.extend(collect_data_files("pytubefix", includes=["**/*.js"]))

    binaries = [(str(helper_root / name), "tools") for name in HELPER_NAMES]
    node_root = Path(nodejs_wheel.__file__).resolve().parent
    binaries.append((str(node_root / "bin" / "node"), "nodejs_wheel/bin"))

    hidden_imports = [
        "pop-fe",
        "theme_ascii",
        "theme_dotpainting",
        "theme_opencv",
        "nodejs_wheel.executable",
        "tkinterdnd2",
    ]
    return datas, binaries, sorted(set(hidden_imports))


def bundle_info(display_name: str):
    version = os.environ.get("POPFE_VERSION", "0.0.0")
    return {
        "CFBundleDisplayName": display_name,
        "CFBundleShortVersionString": version,
        "CFBundleVersion": os.environ.get("POPFE_BUILD_NUMBER", "1"),
        "LSApplicationCategoryType": "public.app-category.utilities",
        "LSMinimumSystemVersion": "14.0",
        "LSArchitecturePriority": ["arm64"],
        "NSHighResolutionCapable": True,
    }
