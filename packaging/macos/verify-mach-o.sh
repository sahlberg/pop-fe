#!/bin/bash

set -euo pipefail

if (( $# != 1 )); then
    printf 'Usage: verify-mach-o.sh PATH\n' >&2
    exit 2
fi

INPUT="$1"
if [[ -d "$INPUT" ]]; then
    ROOT="$(cd "$INPUT" && pwd -P)"
elif [[ -f "$INPUT" ]]; then
    ROOT="$(cd "$(dirname "$INPUT")" && pwd -P)/$(basename "$INPUT")"
else
    printf 'ERROR: path does not exist: %s\n' "$INPUT" >&2
    exit 1
fi
FOUND=0
FAILED=0

find_candidates() {
    if [[ -d "$ROOT" ]]; then
        find "$ROOT" -type f -print0
    else
        printf '%s\0' "$ROOT"
    fi
}

while IFS= read -r -d '' candidate; do
    description="$(file -b "$candidate")"
    [[ "$description" == *'Mach-O'* ]] || continue
    FOUND=$((FOUND + 1))

    architectures="$(lipo -archs "$candidate")"
    if [[ " $architectures " != *' arm64 '* ]]; then
        printf 'ERROR: %s is not arm64 (%s)\n' "$candidate" "$architectures" >&2
        FAILED=1
    fi

    load_commands="$(otool -l "$candidate")"
    load_references="$(
        awk '$1 == "name" || $1 == "path" { print $2 }' \
            <<< "$load_commands"
    )"
    if grep -E '/opt/homebrew|/usr/local|/Cellar/|/private/tmp|/var/folders|/Users/' \
        >/dev/null <<< "$load_references"; then
        printf 'ERROR: %s contains a non-portable load command\n' \
            "$candidate" >&2
        printf '%s\n' "$load_references" >&2
        FAILED=1
    fi
done < <(find_candidates)

if (( FOUND == 0 )); then
    printf 'ERROR: no Mach-O files found below %s\n' "$ROOT" >&2
    exit 1
fi

if (( FAILED != 0 )); then
    exit 1
fi

printf 'Verified %d arm64 Mach-O file(s) below %s\n' "$FOUND" "$ROOT"
