import re
from dataclasses import dataclass
from pathlib import Path


DISC_EXTENSIONS = (".cue", ".ccd", ".chd", ".zip", ".img", ".bin")
DISC_PRIORITY = {extension: index for index, extension in enumerate(DISC_EXTENSIONS)}
ASSET_NAMES = {
    "icon0": ("ICON0.PNG",),
    "pic0": ("PIC0.PNG",),
    "pic1": ("PIC1.PNG",),
    "snd0": ("SND0.AT3", "SND0.WAV"),
    "manual": ("MANUAL.PDF", "MANUAL.ZIP", "MANUAL.CBR"),
    "logo": ("LOGO.PNG",),
}
_CUE_FILE_PATTERN = re.compile(
    r'^\s*FILE\s+(?:"([^"]+)"|(\S+))\s+', re.IGNORECASE
)
_BRACKETED_TAG_PATTERN = re.compile(r"\[[^\]]*\]")
_NUMBER_PATTERN = re.compile(r"(\d+)")


class FolderImportError(ValueError):
    pass


@dataclass(frozen=True)
class FolderImportResult:
    directory: Path
    discs: tuple[Path, ...]
    assets: dict[str, Path]
    fallback_title: str
    warnings: tuple[str, ...]


def natural_key(path: Path) -> tuple:
    return tuple(
        int(part) if part.isdigit() else part
        for part in _NUMBER_PATTERN.split(path.name.casefold())
    )


def _cue_companions(path: Path) -> set[str]:
    companions = {f"{path.stem.casefold()}.bin"}
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return companions

    for line in lines:
        match = _CUE_FILE_PATTERN.match(line)
        if match:
            companions.add(Path(match.group(1) or match.group(2)).name.casefold())
    return companions


def _discover_discs(files: list[Path]) -> list[Path]:
    candidates = [path for path in files if path.suffix.casefold() in DISC_PRIORITY]
    ignored_companions: set[str] = set()
    for path in candidates:
        extension = path.suffix.casefold()
        if extension == ".cue":
            ignored_companions.update(_cue_companions(path))
        elif extension == ".ccd":
            ignored_companions.add(f"{path.stem.casefold()}.img")

    candidates = [
        path
        for path in candidates
        if not (
            path.suffix.casefold() in {".bin", ".img"}
            and path.name.casefold() in ignored_companions
        )
    ]

    by_stem: dict[str, Path] = {}
    for path in sorted(candidates, key=natural_key):
        stem = path.stem.casefold()
        current = by_stem.get(stem)
        if current is None or DISC_PRIORITY[path.suffix.casefold()] < DISC_PRIORITY[
            current.suffix.casefold()
        ]:
            by_stem[stem] = path
    return sorted(by_stem.values(), key=natural_key)


def _find_asset(
    files_by_name: dict[str, list[Path]], names: tuple[str, ...]
) -> tuple[Path | None, str | None]:
    for name in names:
        matches = files_by_name.get(name.casefold(), [])
        if not matches:
            continue
        matches = sorted(matches, key=natural_key)
        exact = [path for path in matches if path.name == name]
        selected = exact[0] if exact else matches[0]
        warning = None
        if len(matches) > 1:
            warning = f"Multiple {name} files found; using {selected.name}."
        return selected, warning
    return None, None


def _fallback_title(directory: Path) -> str:
    title = _BRACKETED_TAG_PATTERN.sub(" ", directory.name)
    title = re.sub(r"[_\s]+", " ", title).strip(" -_")
    return title or directory.name


def scan_psp_folder(
    directory: str | Path,
    *,
    import_all_discs: bool = True,
    maximum_discs: int = 5,
) -> FolderImportResult:
    root = Path(directory).expanduser()
    if not root.is_dir():
        raise FolderImportError(f"Folder does not exist: {root}")
    if maximum_discs < 1:
        raise ValueError("maximum_discs must be at least one")

    files = sorted(
        (
            path
            for path in root.iterdir()
            if path.is_file() and not path.name.startswith(".")
        ),
        key=natural_key,
    )
    discs = _discover_discs(files)
    if not discs:
        raise FolderImportError("No supported PlayStation disc image was found.")

    warnings: list[str] = []
    if import_all_discs and len(discs) > maximum_discs:
        warnings.append(
            f"Found {len(discs)} discs; only the first {maximum_discs} were loaded."
        )
    selected_discs = discs[:maximum_discs] if import_all_discs else discs[:1]

    files_by_name: dict[str, list[Path]] = {}
    for path in files:
        files_by_name.setdefault(path.name.casefold(), []).append(path)

    assets: dict[str, Path] = {}
    for field, names in ASSET_NAMES.items():
        selected, warning = _find_asset(files_by_name, names)
        if selected is not None:
            assets[field] = selected
        if warning is not None:
            warnings.append(warning)

    return FolderImportResult(
        directory=root.resolve(),
        discs=tuple(path.resolve() for path in selected_discs),
        assets=assets,
        fallback_title=_fallback_title(root),
        warnings=tuple(warnings),
    )
