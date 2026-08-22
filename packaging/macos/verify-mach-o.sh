#!/bin/bash

set -euo pipefail

if (( $# != 1 )); then
    printf 'Usage: verify-mach-o.sh PATH\n' >&2
    exit 2
fi

INPUT="$1"
MAXIMUM_MINIMUM_MACOS="${POPFE_MAXIMUM_MINIMUM_MACOS:-14.0}"
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

for command in file lipo otool vtool; do
    command -v "$command" >/dev/null || {
        printf 'ERROR: required verification command not found: %s\n' "$command" >&2
        exit 1
    }
done

version_is_greater() {
    local version="$1"
    local limit="$2"
    local version_major version_minor version_patch
    local limit_major limit_minor limit_patch
    IFS=. read -r version_major version_minor version_patch <<< "$version"
    IFS=. read -r limit_major limit_minor limit_patch <<< "$limit"
    version_minor="${version_minor:-0}"
    version_patch="${version_patch:-0}"
    limit_minor="${limit_minor:-0}"
    limit_patch="${limit_patch:-0}"
    (( version_major > limit_major )) ||
        (( version_major == limit_major && version_minor > limit_minor )) ||
        (( version_major == limit_major && version_minor == limit_minor &&
            version_patch > limit_patch ))
}

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

    minimum_versions="$(
        vtool -show-build "$candidate" 2>/dev/null |
            awk '$1 == "minos" { print $2 }'
    )"
    if [[ -z "$minimum_versions" ]]; then
        printf 'ERROR: %s has no readable macOS deployment target\n' \
            "$candidate" >&2
        FAILED=1
    else
        while IFS= read -r minimum_version; do
            if version_is_greater \
                "$minimum_version" "$MAXIMUM_MINIMUM_MACOS"; then
                printf 'ERROR: %s requires macOS %s (maximum allowed is %s)\n' \
                    "$candidate" "$minimum_version" \
                    "$MAXIMUM_MINIMUM_MACOS" >&2
                FAILED=1
            fi
        done <<< "$minimum_versions"
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
