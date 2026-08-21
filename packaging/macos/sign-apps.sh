#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
DIST_ROOT="${1:-${POPFE_DIST_ROOT:-$REPOSITORY_ROOT/build/macos/dist}}"
CLI="$DIST_ROOT/pop-fe"
PSP_APP="$DIST_ROOT/Pop-FE PSP.app"
PS3_APP="$DIST_ROOT/Pop-FE PS3.app"

fail() {
    printf '[pop-fe macOS] ERROR: %s\n' "$*" >&2
    exit 1
}

sign_path() {
    local target="$1"
    local output

    if ! output="$(codesign --force --sign - --timestamp=none "$target" 2>&1)"; then
        printf '%s\n' "$output" >&2
        fail "could not sign $target"
    fi
}

sign_macho_files() {
    local root="$1"
    local candidate

    while IFS= read -r -d '' candidate; do
        if file -b "$candidate" | grep -q '^Mach-O'; then
            sign_path "$candidate"
        fi
    done < <(find "$root" -type f -print0)
}

for target in "$CLI" "$PSP_APP" "$PS3_APP"; do
    [[ -e "$target" ]] || fail "missing packaged target: $target"
done

sign_path "$CLI"
for app in "$PSP_APP" "$PS3_APP"; do
    sign_macho_files "$app/Contents"
    while IFS= read -r -d '' bundle; do
        sign_path "$bundle"
    done < <(find "$app/Contents" -depth -type d \
        \( -name '*.framework' -o -name '*.bundle' \) -print0)
    sign_path "$app"
done

codesign --verify --strict "$CLI"
codesign --verify --deep --strict "$PSP_APP"
codesign --verify --deep --strict "$PS3_APP"
"$SCRIPT_DIR/verify-mach-o.sh" "$DIST_ROOT"

printf 'Ad-hoc signatures verified below %s\n' "$DIST_ROOT"
