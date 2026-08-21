#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
SOURCE="$SCRIPT_DIR/pop-fe"
DEFAULT_DESTINATION="$HOME/.local/bin"

[[ -x "$SOURCE" ]] || {
    printf 'The pop-fe executable is missing beside this installer.\n' >&2
    exit 1
}

if [[ -n "${POPFE_INSTALL_DEST:-}" ]]; then
    DESTINATION="$POPFE_INSTALL_DEST"
else
    printf 'Install the POP-FE command-line tool.\n'
    printf 'Destination directory [%s]: ' "$DEFAULT_DESTINATION"
    IFS= read -r DESTINATION
    DESTINATION="${DESTINATION:-$DEFAULT_DESTINATION}"
fi

case "$DESTINATION" in
    '~') DESTINATION="$HOME" ;;
    '~/'*) DESTINATION="$HOME/${DESTINATION#\~/}" ;;
esac

mkdir -p "$DESTINATION"
TEMPORARY="$(mktemp "$DESTINATION/.pop-fe.XXXXXX")"
cleanup() {
    [[ ! -e "$TEMPORARY" ]] || rm -f "$TEMPORARY"
}
trap cleanup EXIT
cp "$SOURCE" "$TEMPORARY"
chmod 755 "$TEMPORARY"
mv -f "$TEMPORARY" "$DESTINATION/pop-fe"

printf '\nInstalled: %s/pop-fe\n' "$DESTINATION"
printf 'If that directory is not on PATH, run it with the full path shown above.\n'
