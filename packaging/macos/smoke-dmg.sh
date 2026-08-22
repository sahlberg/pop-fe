#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
DMG_PATH="${1:-}"
[[ -n "$DMG_PATH" && -f "$DMG_PATH" ]] || {
    printf 'usage: %s /path/to/Pop-FE-<version>-macOS-arm64.dmg\n' "$0" >&2
    exit 2
}
DMG_PATH="$(cd "$(dirname "$DMG_PATH")" && pwd -P)/$(basename "$DMG_PATH")"
MOUNT_POINT="$(mktemp -d "${TMPDIR:-/tmp}/popfe-dmg-mount.XXXXXX")"
INSTALL_ROOT="$(mktemp -d "${TMPDIR:-/tmp}/popfe-cli-install.XXXXXX")"
MOUNTED=0

cleanup() {
    if [[ "$MOUNTED" -eq 1 ]]; then
        hdiutil detach "$MOUNT_POINT" >/dev/null || true
    fi
    rmdir "$MOUNT_POINT" 2>/dev/null || true
    if [[ -f "$INSTALL_ROOT/pop-fe" ]]; then
        rm -f "$INSTALL_ROOT/pop-fe"
    fi
    rmdir "$INSTALL_ROOT" 2>/dev/null || true
}
trap cleanup EXIT

if [[ -f "$DMG_PATH.sha256" ]]; then
    (
        cd "$(dirname "$DMG_PATH")"
        shasum -a 256 -c "$(basename "$DMG_PATH.sha256")"
    )
fi

hdiutil attach -readonly -nobrowse -mountpoint "$MOUNT_POINT" "$DMG_PATH" >/dev/null
MOUNTED=1

CLI="$MOUNT_POINT/pop-fe"
PSP_APP="$MOUNT_POINT/Pop-FE PSP.app"
PS3_APP="$MOUNT_POINT/Pop-FE PS3.app"
INSTALLER="$MOUNT_POINT/Install CLI.command"

for target in "$CLI" "$PSP_APP" "$PS3_APP" "$INSTALLER" \
    "$MOUNT_POINT/README-macOS.txt" "$MOUNT_POINT/Applications"; do
    [[ -e "$target" ]] || {
        printf 'ERROR: DMG target is missing: %s\n' "$target" >&2
        exit 1
    }
done
[[ "$(readlink "$MOUNT_POINT/Applications")" == '/Applications' ]]
[[ -f "$MOUNT_POINT/licenses/MANIFEST.txt" ]]

codesign --verify --strict "$CLI"
codesign --verify --deep --strict "$PSP_APP"
codesign --verify --deep --strict "$PS3_APP"
"$SCRIPT_DIR/verify-mach-o.sh" "$MOUNT_POINT"
"$CLI" --help >/dev/null
"$CLI" --version >/dev/null
POPFE_GUI_SMOKE_TEST=1 "$PSP_APP/Contents/MacOS/Pop-FE PSP"
POPFE_GUI_SMOKE_TEST=1 "$PS3_APP/Contents/MacOS/Pop-FE PS3"
POPFE_INSTALL_DEST="$INSTALL_ROOT" "$INSTALLER" >/dev/null
"$INSTALL_ROOT/pop-fe" --help >/dev/null

printf 'Mounted DMG layout, signatures, CLI, installer, and GUIs passed\n'
