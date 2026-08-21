"""Cross-platform runtime paths for source and packaged POP-FE builds."""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Optional, Union


APPLICATION_NAME = "Pop-FE"
PathLike = Union[str, os.PathLike]


class RuntimePathError(RuntimeError):
    """Base class for runtime resource and tool errors."""


class MissingResourceError(RuntimePathError):
    """Raised when a required packaged resource is unavailable."""


class MissingToolError(RuntimePathError):
    """Raised when a required conversion helper is unavailable."""


class MountedDeviceNotFoundError(RuntimePathError):
    """Raised when automatic removable-device discovery finds no target."""


_SOURCE_TOOL_PATHS = {
    "atracdenc": ("atracdenc/src/atracdenc",),
    "binmerge": ("binmerge/binmerge", "binmerge.py"),
    "cue2cu2": ("Cue2cu2/cue2cu2.py", "cue2cu2.py"),
    "libcrypt-patcher": ("lcp",),
    "pkg": ("PSL1GHT/tools/ps3py/pkg.py",),
    "psx-undither": ("psx-undither/build/psxund",),
    "sign3": ("sign3.py",),
}

_TOOL_EXECUTABLE_NAMES = {
    "atracdenc": "atracdenc",
    "binmerge": "binmerge",
    "chdman": "chdman",
    "cue2cu2": "cue2cu2",
    "ffmpeg": "ffmpeg",
    "libcrypt-patcher": "lcp",
    "pkg": "pkg",
    "psx-undither": "psxund",
    "sign3": "sign3",
    "xdelta3": "xdelta3",
}


def _resolved(path: PathLike) -> Path:
    return Path(path).expanduser().resolve()


def _absolute_environment_path(
    environment: Mapping[str, str],
    name: str,
    fallback: Path,
) -> Path:
    value = environment.get(name)
    if value:
        path = Path(value).expanduser()
        if path.is_absolute():
            return path.resolve()
    return fallback.resolve()


@dataclass(frozen=True)
class RuntimePaths:
    """Resolved filesystem and executable locations for one POP-FE process."""

    platform: str
    frozen: bool
    source_root: Path
    resource_root: Path
    executable: Path
    home: Path
    cwd: Path
    environ: Mapping[str, str] = field(repr=False, compare=False)

    @classmethod
    def detect(
        cls,
        *,
        platform: Optional[str] = None,
        frozen: Optional[bool] = None,
        source_file: Optional[PathLike] = None,
        executable: Optional[PathLike] = None,
        meipass: Optional[PathLike] = None,
        home: Optional[PathLike] = None,
        environ: Optional[Mapping[str, str]] = None,
        cwd: Optional[PathLike] = None,
    ) -> "RuntimePaths":
        """Detect runtime paths, with injectable values for deterministic tests."""
        detected_platform = platform or sys.platform
        detected_frozen = (
            bool(getattr(sys, "frozen", False)) if frozen is None else frozen
        )
        detected_source_file = _resolved(source_file or __file__)
        source_root = detected_source_file.parent
        detected_executable = _resolved(executable or sys.executable)
        detected_home = _resolved(home or Path.home())
        detected_cwd = _resolved(cwd or Path.cwd())
        detected_environment = dict(os.environ if environ is None else environ)

        detected_meipass = meipass
        if detected_frozen and detected_meipass is None:
            detected_meipass = getattr(sys, "_MEIPASS", None)
        resource_root = (
            _resolved(detected_meipass)
            if detected_frozen and detected_meipass is not None
            else source_root
        )

        return cls(
            platform=detected_platform,
            frozen=detected_frozen,
            source_root=source_root,
            resource_root=resource_root,
            executable=detected_executable,
            home=detected_home,
            cwd=detected_cwd,
            environ=detected_environment,
        )

    @property
    def is_macos(self) -> bool:
        return self.platform == "darwin"

    @property
    def is_windows(self) -> bool:
        return self.platform.startswith("win")

    @property
    def config_dir(self) -> Path:
        if self.is_macos:
            return self.home / "Library" / "Application Support" / APPLICATION_NAME
        if self.is_windows:
            root = _absolute_environment_path(
                self.environ,
                "APPDATA",
                self.home / "AppData" / "Roaming",
            )
            return root / APPLICATION_NAME
        root = _absolute_environment_path(
            self.environ,
            "XDG_CONFIG_HOME",
            self.home / ".config",
        )
        return root / "pop-fe"

    @property
    def log_dir(self) -> Path:
        if self.is_macos:
            return self.home / "Library" / "Logs" / APPLICATION_NAME
        if self.is_windows:
            root = _absolute_environment_path(
                self.environ,
                "LOCALAPPDATA",
                self.home / "AppData" / "Local",
            )
            return root / APPLICATION_NAME / "Logs"
        root = _absolute_environment_path(
            self.environ,
            "XDG_STATE_HOME",
            self.home / ".local" / "state",
        )
        return root / "pop-fe"

    @property
    def cache_dir(self) -> Path:
        if self.is_macos:
            return self.home / "Library" / "Caches" / APPLICATION_NAME
        if self.is_windows:
            root = _absolute_environment_path(
                self.environ,
                "LOCALAPPDATA",
                self.home / "AppData" / "Local",
            )
            return root / APPLICATION_NAME / "Cache"
        root = _absolute_environment_path(
            self.environ,
            "XDG_CACHE_HOME",
            self.home / ".cache",
        )
        return root / "pop-fe"

    @property
    def mounted_volume_root(self) -> Optional[Path]:
        if self.is_macos:
            return Path("/Volumes")
        return None

    def mounted_volumes(self, volume_root: Optional[PathLike] = None) -> tuple[Path, ...]:
        """Return macOS mounted volumes in deterministic name order."""
        root = _resolved(volume_root or self.mounted_volume_root or "/Volumes")
        try:
            volumes = [path.resolve() for path in root.iterdir() if path.is_dir()]
        except OSError:
            return ()
        return tuple(sorted(volumes, key=lambda path: path.name.casefold()))

    def find_psp_mount(self, volume_root: Optional[PathLike] = None) -> Path:
        """Find a mounted PSP memory stick or Vita `pspemu` directory."""
        for volume in self.mounted_volumes(volume_root):
            if (volume / "PSP" / "GAME").is_dir():
                return volume
            vita_root = volume / "pspemu"
            if (vita_root / "PSP" / "GAME").is_dir():
                return vita_root
        raise MountedDeviceNotFoundError(
            "Could not find a PSP or Vita memory card under /Volumes"
        )

    def find_psc_mount(self, volume_root: Optional[PathLike] = None) -> Path:
        """Find a mounted PlayStation Classic AutoBleem device."""
        for volume in self.mounted_volumes(volume_root):
            if (volume / "Games").is_dir():
                return volume
        raise MountedDeviceNotFoundError(
            "Could not find a PlayStation Classic AutoBleem device under /Volumes"
        )

    def resource_path(self, relative_path: PathLike, *, required: bool = False) -> Path:
        """Resolve a read-only resource without allowing traversal outside it."""
        relative = Path(relative_path)
        if relative.is_absolute():
            raise ValueError("Resource paths must be relative")

        root = self.resource_root.resolve()
        candidate = (root / relative).resolve()
        if candidate != root and root not in candidate.parents:
            raise ValueError("Resource path escapes the POP-FE resource directory")
        if required and not candidate.exists():
            raise MissingResourceError(
                f"Required POP-FE resource is missing: {relative_path} "
                f"(expected at {candidate})"
            )
        return candidate

    def preference_path(self, filename: str) -> Path:
        if not filename or Path(filename).name != filename:
            raise ValueError("Preference filename must not contain directories")
        return self.config_dir / filename

    def application_preference_path(self, filename: str) -> Path:
        """Use macOS user storage while retaining legacy paths elsewhere."""
        if self.is_macos:
            return self.preference_path(filename)
        if not filename or Path(filename).name != filename:
            raise ValueError("Preference filename must not contain directories")
        return self.cwd / filename

    def application_work_dir(self, component: str, legacy_name: str) -> Path:
        """Create a unique macOS workspace or return the legacy local path."""
        if self.is_macos:
            return self.create_work_dir(component)
        if not legacy_name or Path(legacy_name).name != legacy_name:
            raise ValueError("Legacy work directory must be a single name")
        return (self.cwd / legacy_name).resolve()

    def ensure_user_directories(self) -> None:
        for directory in (self.config_dir, self.log_dir, self.cache_dir):
            directory.mkdir(parents=True, exist_ok=True)

    def create_work_dir(self, component: str = "run") -> Path:
        safe_component = re.sub(r"[^A-Za-z0-9._-]+", "-", component).strip("-.")
        if not safe_component:
            safe_component = "run"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        return Path(
            tempfile.mkdtemp(prefix=f"{safe_component}-", dir=self.cache_dir)
        ).resolve()

    def remove_work_dir(self, path: PathLike) -> None:
        candidate = _resolved(path)
        root = self.cache_dir.resolve()
        if candidate == root or root not in candidate.parents:
            raise ValueError("Refusing to remove a directory outside the POP-FE cache")
        shutil.rmtree(candidate, ignore_errors=True)

    def new_log_path(self, component: str = "pop-fe") -> Path:
        safe_component = re.sub(r"[^A-Za-z0-9._-]+", "-", component).strip("-.")
        if not safe_component:
            safe_component = "pop-fe"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        unique = uuid.uuid4().hex[:10]
        return self.log_dir / f"{safe_component}-{timestamp}-{unique}.log"

    def _tool_names(self, logical_name: str) -> tuple[str, ...]:
        executable_name = _TOOL_EXECUTABLE_NAMES.get(logical_name, logical_name)
        if self.is_windows and not executable_name.lower().endswith(".exe"):
            return (f"{executable_name}.exe",)
        return (executable_name,)

    def _tool_is_usable(self, candidate: Path) -> bool:
        if not candidate.is_file():
            return False
        if self.is_windows or candidate.suffix == ".py":
            return True
        return os.access(candidate, os.X_OK)

    def tool_path(
        self,
        logical_name: str,
        *,
        required: bool = False,
        path_search: Callable[[str], Optional[str]] = shutil.which,
    ) -> Optional[Path]:
        """Resolve a helper by logical name, preferring packaged tools."""
        searched = []
        names = self._tool_names(logical_name)

        for name in names:
            for relative in (Path("tools") / name, Path(name)):
                candidate = self.resource_path(relative)
                searched.append(candidate)
                if self._tool_is_usable(candidate):
                    return candidate

        if not self.frozen:
            for relative in _SOURCE_TOOL_PATHS.get(logical_name, ()):
                candidate = (self.source_root / relative).resolve()
                searched.append(candidate)
                if self._tool_is_usable(candidate):
                    return candidate

            for name in names:
                found = path_search(name)
                if found:
                    candidate = _resolved(found)
                    searched.append(candidate)
                    return candidate

        if required:
            searched_locations = ", ".join(str(path) for path in searched)
            raise MissingToolError(
                f"Required POP-FE helper '{logical_name}' was not found or is not "
                f"executable. Searched: {searched_locations}"
            )
        return None

    def tool_command(
        self,
        logical_name: str,
        *arguments: object,
        path_search: Callable[[str], Optional[str]] = shutil.which,
    ) -> list[str]:
        """Build an argument vector for a required native or Python helper."""
        tool = self.tool_path(
            logical_name,
            required=True,
            path_search=path_search,
        )
        command = [str(tool)]
        if tool.suffix == ".py":
            if self.frozen:
                raise MissingToolError(
                    f"Packaged helper '{logical_name}' must be a standalone "
                    "executable, not a Python source file"
                )
            command.insert(0, str(self.executable))
        command.extend(str(argument) for argument in arguments)
        return command


runtime = RuntimePaths.detect()
