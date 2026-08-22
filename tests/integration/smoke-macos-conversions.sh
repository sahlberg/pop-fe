#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
CLI="${1:-$REPOSITORY_ROOT/build/macos/dist/pop-fe}"
CHDMAN="${POPFE_CHDMAN:-$REPOSITORY_ROOT/build/macos/helpers/chdman}"
FIXTURES="$REPOSITORY_ROOT/testimages/vs"
SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/popfe-conversions.XXXXXX")"
WORK_ROOT="$SCRATCH/Pop FE é"
TEST_HOME="$SCRATCH/home"
READ_ONLY_CWD="$SCRATCH/read-only"

CLI="$(cd "$(dirname "$CLI")" && pwd -P)/$(basename "$CLI")"
CHDMAN="$(cd "$(dirname "$CHDMAN")" && pwd -P)/$(basename "$CHDMAN")"

cleanup() {
    chmod 755 "$READ_ONLY_CWD" 2>/dev/null || true
    if [[ "${POPFE_KEEP_INTEGRATION:-0}" == '1' ]]; then
        printf 'Retained integration output at %s\n' "$SCRATCH" >&2
        return
    fi
    rm -rf "$SCRATCH"
}
trap cleanup EXIT

for command in "$CLI" "$CHDMAN" zip; do
    command -v "$command" >/dev/null || {
        printf 'ERROR: required conversion smoke command is missing: %s\n' "$command" >&2
        exit 1
    }
done

mkdir -p \
    "$WORK_ROOT/formats" \
    "$WORK_ROOT/psp/PSP/GAME" \
    "$WORK_ROOT/ps2/POPS" \
    "$WORK_ROOT/ps2/ART" \
    "$WORK_ROOT/ps3" \
    "$WORK_ROOT/psc/Games" \
    "$WORK_ROOT/psio" \
    "$WORK_ROOT/retroarch/bin" \
    "$WORK_ROOT/retroarch/cue" \
    "$WORK_ROOT/retroarch/pbp" \
    "$WORK_ROOT/retroarch/thumbnails" \
    "$TEST_HOME" \
    "$READ_ONLY_CWD"

cp "$FIXTURES/vs.bin" "$WORK_ROOT/formats/vs.img"
printf '%s\n' \
    '[CloneCD]' \
    'Version=3' \
    '[TRACK 1]' \
    'MODE=2' \
    'INDEX 1=0' > "$WORK_ROOT/formats/vs.ccd"
(
    cd "$FIXTURES"
    zip -q -j "$WORK_ROOT/formats/vs.zip" vs.cue vs.bin
)
"$CHDMAN" createcd \
    -f \
    -i "$FIXTURES/vs.cue" \
    -o "$WORK_ROOT/formats/vs.chd" >/dev/null

chmod 555 "$READ_ONLY_CWD"
COMMON_ARGS=(
    --title 'POP-FE Smoke'
    --cover "$FIXTURES/blank.png"
    --pic0 "$FIXTURES/blank.png"
    --pic1 "$FIXTURES/blank.png"
    --force-no-assets
    --no-libcrypt
)
FORMAT_ARGS=(
    "$FIXTURES/vs.cue"
    "$WORK_ROOT/formats/vs.ccd"
    "$WORK_ROOT/formats/vs.zip"
    "$WORK_ROOT/formats/vs.chd"
)
(
    cd "$READ_ONLY_CWD"
    HOME="$TEST_HOME" "$CLI" \
        "${COMMON_ARGS[@]}" \
        --psp-dir "$WORK_ROOT/psp" \
        --ps2-dir "$WORK_ROOT/ps2" \
        --ps3-pkg "$WORK_ROOT/ps3/POP-FE-Smoke.pkg" \
        --snd0 "$FIXTURES/sine.wav" \
        "${FORMAT_ARGS[@]}"

    # create_ps3 removes the process-global temporary files when it finishes,
    # so targets dispatched after PS3 must run in a fresh process.
    HOME="$TEST_HOME" "$CLI" \
        "${COMMON_ARGS[@]}" \
        --psc-dir "$WORK_ROOT/psc" \
        --psio-dir "$WORK_ROOT/psio" \
        --retroarch-bin-dir "$WORK_ROOT/retroarch/bin" \
        --retroarch-cue-dir "$WORK_ROOT/retroarch/cue" \
        --retroarch-pbp-dir "$WORK_ROOT/retroarch/pbp" \
        --retroarch-thumbnail-dir "$WORK_ROOT/retroarch/thumbnails" \
        "${FORMAT_ARGS[@]}"
)

require_output() {
    local root="$1"
    local pattern="$2"
    [[ -n "$(find "$root" -type f -name "$pattern" -print -quit)" ]] || {
        printf 'ERROR: no %s output below %s\n' "$pattern" "$root" >&2
        exit 1
    }
}

require_output "$WORK_ROOT/psp" 'EBOOT.PBP'
require_output "$WORK_ROOT/ps2" '*.VCD'
require_output "$WORK_ROOT/ps3" '*.pkg'
require_output "$WORK_ROOT/psc" '*.PBP'
require_output "$WORK_ROOT/psio" '*.cu2'
require_output "$WORK_ROOT/retroarch/bin" '*.m3u'
require_output "$WORK_ROOT/retroarch/cue" 'PSISO.m3u'
require_output "$WORK_ROOT/retroarch/pbp" '*.pbp'
require_output "$WORK_ROOT/retroarch/thumbnails" '*.png'

if find "$TEST_HOME/Library/Caches/Pop-FE" \
    -maxdepth 1 -type d -name 'cli-*' -print -quit 2>/dev/null | grep -q .; then
    printf 'ERROR: successful CLI conversion left a macOS work directory behind\n' >&2
    exit 1
fi

printf 'Packaged CLI conversion formats and targets passed\n'
