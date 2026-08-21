#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
BUILD_ROOT="${POPFE_BUILD_ROOT:-$REPOSITORY_ROOT/build/macos}"
DIST_ROOT="${POPFE_DIST_ROOT:-$BUILD_ROOT/dist}"
WORK_ROOT="$BUILD_ROOT/pyinstaller-work"
VENV_ROOT="${POPFE_BUILD_VENV:-$BUILD_ROOT/app-venv}"
PYTHON_BIN="${PYTHON_BIN:-}"
PYENV_BUILD_VERSION="${POPFE_PYENV_VERSION:-3.12.13}"
ICON_PATH="$BUILD_ROOT/Pop-FE.icns"
VERSION="${POPFE_VERSION:-0.0.0}"
GENERATED_ROOT="$BUILD_ROOT/generated"

say() {
    printf '[pop-fe macOS] %s\n' "$*" >&2
}

fail() {
    say "ERROR: $*"
    exit 1
}

resolve_python() {
    if [[ -n "$PYTHON_BIN" ]]; then
        return
    fi

    if command -v pyenv >/dev/null 2>&1; then
        pyenv_prefix="$(pyenv prefix "$PYENV_BUILD_VERSION" 2>/dev/null || true)"
        if [[ -n "$pyenv_prefix" && -x "$pyenv_prefix/bin/python3" ]]; then
            PYTHON_BIN="$pyenv_prefix/bin/python3"
        fi
    fi

    if [[ -z "$PYTHON_BIN" ]]; then
        PYTHON_BIN="$(command -v python3 2>/dev/null || true)"
    fi
    [[ -n "$PYTHON_BIN" ]] || fail \
        'Python 3.12 with Tk was not found; install it with pyenv or set PYTHON_BIN'
}

create_icon() {
    local iconset="$BUILD_ROOT/Pop-FE.iconset"
    local source="$BUILD_ROOT/Pop-FE-icon-source.png"
    rm -rf "$iconset"
    mkdir -p "$iconset"
    cp "$REPOSITORY_ROOT/pop-fe-ps3.png" "$source"
    sips --padToHeightWidth 1024 1024 --padColor FFFFFF "$source" >/dev/null
    for size in 16 32 128 256 512; do
        sips -z "$size" "$size" "$source" \
            --out "$iconset/icon_${size}x${size}.png" >/dev/null
        double_size=$((size * 2))
        sips -z "$double_size" "$double_size" "$source" \
            --out "$iconset/icon_${size}x${size}@2x.png" >/dev/null
    done
    iconutil -c icns "$iconset" -o "$ICON_PATH"
}

[[ "$(uname -s)" == 'Darwin' ]] || fail 'application builds require macOS'
[[ "$(uname -m)" == 'arm64' ]] || fail 'application builds require Apple Silicon'

resolve_python
"$PYTHON_BIN" - <<'PY' || fail \
    'application builds require native arm64 Python 3.12 with Tk 8.6 support'
import platform
import sys
import tkinter

if (
    sys.version_info[:2] != (3, 12)
    or platform.machine() != "arm64"
    or tkinter.TkVersion < 8.6
):
    raise SystemExit(1)
PY

for command in iconutil sips; do
    command -v "$command" >/dev/null || fail "required build command not found: $command"
done

[[ "$VERSION" =~ ^[0-9]+([.][0-9]+){1,2}$ ]] || fail \
    'POPFE_VERSION must contain two or three numeric components (for example 1.2.0)'

if [[ ! -x "$VENV_ROOT/bin/python3" ]]; then
    say "creating build environment from $PYTHON_BIN"
    "$PYTHON_BIN" -m venv "$VENV_ROOT"
fi

VENV_PYTHON="$VENV_ROOT/bin/python3"
"$VENV_PYTHON" - <<'PY' || fail \
    'the cached build environment is incompatible; remove build/macos/app-venv'
import platform
import sys
import tkinter

if sys.version_info[:2] != (3, 12) or platform.machine() != "arm64":
    raise SystemExit(1)
PY

say 'installing pinned packaging dependencies'
"$VENV_PYTHON" -m pip install \
    --disable-pip-version-check \
    --requirement "$SCRIPT_DIR/requirements-build.txt" \
    --requirement "$SCRIPT_DIR/requirements-runtime.txt"

for helper in atracdenc binmerge chdman cue2cu2 ffmpeg lcp pkg psxund sign3 xdelta3; do
    [[ -x "$BUILD_ROOT/helpers/$helper" ]] || fail \
        "missing helper $helper; run packaging/macos/build-helpers.sh first"
done

rm -rf "$DIST_ROOT" "$WORK_ROOT"
mkdir -p "$DIST_ROOT" "$WORK_ROOT" "$GENERATED_ROOT"
printf 'VERSION = "%s"\n' "$VERSION" > "$GENERATED_ROOT/popfe_build_version.py"
create_icon

for spec in pop-fe-cli.spec pop-fe-psp.spec pop-fe-ps3.spec; do
    say "building $spec"
    POPFE_VERSION="$VERSION" \
    POPFE_ICON_PATH="$ICON_PATH" \
    PYINSTALLER_CONFIG_DIR="$BUILD_ROOT/pyinstaller-cache" \
        "$VENV_PYTHON" -m PyInstaller \
            --noconfirm \
            --clean \
            --distpath "$DIST_ROOT" \
            --workpath "$WORK_ROOT" \
            "$SCRIPT_DIR/$spec"
done

rm -rf "$DIST_ROOT/Pop-FE PSP" "$DIST_ROOT/Pop-FE PS3"
"$SCRIPT_DIR/verify-mach-o.sh" "$DIST_ROOT"
say "applications staged in $DIST_ROOT"
