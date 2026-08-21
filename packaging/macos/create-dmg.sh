#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
BUILD_ROOT="${POPFE_BUILD_ROOT:-$REPOSITORY_ROOT/build/macos}"
DIST_ROOT="${POPFE_DIST_ROOT:-$BUILD_ROOT/dist}"
STAGING_ROOT="$BUILD_ROOT/dmg-stage"
PSP_APP="$DIST_ROOT/Pop-FE PSP.app"
PS3_APP="$DIST_ROOT/Pop-FE PS3.app"
CLI="$DIST_ROOT/pop-fe"

fail() {
    printf '[pop-fe macOS] ERROR: %s\n' "$*" >&2
    exit 1
}

for command in codesign ditto hdiutil plutil shasum; do
    command -v "$command" >/dev/null || fail "required command not found: $command"
done
for target in "$CLI" "$PSP_APP" "$PS3_APP"; do
    [[ -e "$target" ]] || fail "missing packaged target: $target"
done

PSP_VERSION="$(plutil -extract CFBundleShortVersionString raw -o - \
    "$PSP_APP/Contents/Info.plist")"
PS3_VERSION="$(plutil -extract CFBundleShortVersionString raw -o - \
    "$PS3_APP/Contents/Info.plist")"
[[ "$PSP_VERSION" == "$PS3_VERSION" ]] || fail 'application versions do not match'
VERSION="${POPFE_VERSION:-$PSP_VERSION}"
[[ "$VERSION" == "$PSP_VERSION" ]] || fail \
    'POPFE_VERSION does not match the packaged applications'
[[ "$VERSION" =~ ^[0-9]+([.][0-9]+){1,2}$ ]] || fail 'invalid release version'

DMG_PATH="$BUILD_ROOT/Pop-FE-$VERSION-macOS-arm64.dmg"
CHECKSUM_PATH="$DMG_PATH.sha256"

"$SCRIPT_DIR/sign-apps.sh" "$DIST_ROOT"

rm -rf "$STAGING_ROOT"
mkdir -p "$STAGING_ROOT"
ditto "$PSP_APP" "$STAGING_ROOT/Pop-FE PSP.app"
ditto "$PS3_APP" "$STAGING_ROOT/Pop-FE PS3.app"
ditto "$CLI" "$STAGING_ROOT/pop-fe"
ditto "$SCRIPT_DIR/Install CLI.command" "$STAGING_ROOT/Install CLI.command"
ditto "$SCRIPT_DIR/README-macOS.txt" "$STAGING_ROOT/README-macOS.txt"
ditto "$REPOSITORY_ROOT/LICENCE-LGPL-2.1.txt" \
    "$STAGING_ROOT/LICENCE-LGPL-2.1.txt"
ditto "$REPOSITORY_ROOT/THIRD_PARTY_NOTICES.md" \
    "$STAGING_ROOT/THIRD_PARTY_NOTICES.md"
chmod 755 "$STAGING_ROOT/pop-fe" "$STAGING_ROOT/Install CLI.command"
ln -s /Applications "$STAGING_ROOT/Applications"

rm -f "$DMG_PATH" "$CHECKSUM_PATH"
hdiutil create \
    -volname "Pop-FE $VERSION" \
    -srcfolder "$STAGING_ROOT" \
    -format UDZO \
    -imagekey zlib-level=9 \
    -ov \
    "$DMG_PATH"

(
    cd "$BUILD_ROOT"
    shasum -a 256 "$(basename "$DMG_PATH")" > "$(basename "$CHECKSUM_PATH")"
)

printf 'Created %s\nChecksum: %s\n' "$DMG_PATH" "$CHECKSUM_PATH"
