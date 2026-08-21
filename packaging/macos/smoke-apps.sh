#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
DIST_ROOT="${POPFE_DIST_ROOT:-$REPOSITORY_ROOT/build/macos/dist}"
CLI="$DIST_ROOT/pop-fe"
PSP_APP="$DIST_ROOT/Pop-FE PSP.app"
PS3_APP="$DIST_ROOT/Pop-FE PS3.app"

for path in "$CLI" "$PSP_APP" "$PS3_APP"; do
    [[ -e "$path" ]] || {
        printf 'ERROR: missing packaged target: %s\n' "$path" >&2
        exit 1
    }
done

"$CLI" --help >/dev/null
VERSION="$(plutil -extract CFBundleShortVersionString raw -o - \
    "$PSP_APP/Contents/Info.plist")"
[[ "$("$CLI" --version)" == "$VERSION" ]]
"$PSP_APP/Contents/Frameworks/nodejs_wheel/bin/node" --version >/dev/null
POPFE_GUI_SMOKE_TEST=1 "$PSP_APP/Contents/MacOS/Pop-FE PSP"
POPFE_GUI_SMOKE_TEST=1 "$PS3_APP/Contents/MacOS/Pop-FE PS3"
codesign --verify --deep --strict "$PSP_APP"
codesign --verify --deep --strict "$PS3_APP"

printf 'CLI and GUI smoke tests passed\n'
