#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd -P)"
REPOSITORY_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd -P)"
LOCK_FILE="$SCRIPT_DIR/dependencies.lock.json"
BUILD_ROOT="${POPFE_BUILD_ROOT:-$REPOSITORY_ROOT/build/macos}"
DOWNLOAD_ROOT="${POPFE_DOWNLOAD_ROOT:-$BUILD_ROOT/downloads}"
STAGE_ROOT="${POPFE_HELPER_STAGE:-$BUILD_ROOT/helpers}"
PYTHON_BIN="${PYTHON_BIN:-}"
JOBS="${JOBS:-}"
ONLY="${POPFE_HELPERS_ONLY:-all}"
MINIMUM_MACOS="14.0"

if [[ -z "$JOBS" ]]; then
    JOBS="$(sysctl -n hw.logicalcpu 2>/dev/null || printf '4')"
fi

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
        PYTHON_BIN="$(pyenv which python3 2>/dev/null || true)"
    fi

    if [[ -z "$PYTHON_BIN" ]]; then
        PYTHON_BIN="$(command -v python3 2>/dev/null || true)"
    fi

    [[ -n "$PYTHON_BIN" ]] || fail \
        'Python 3.12 was not found; activate it with pyenv or set PYTHON_BIN'
}

usage() {
    printf '%s\n' \
        'Usage: build-helpers.sh [--only component[,component...]]' \
        '' \
        'Components: ffmpeg, atracdenc, xdelta3, chdman,' \
        '            libcrypt-patcher, psx-undither, python, all'
}

while (( $# > 0 )); do
    case "$1" in
        --only)
            (( $# >= 2 )) || fail '--only requires a value'
            ONLY="$2"
            shift 2
            ;;
        --help|-h)
            usage
            exit 0
            ;;
        *)
            fail "unknown argument: $1"
            ;;
    esac
done

if [[ "$ONLY" != 'all' ]]; then
    IFS=',' read -r -a requested_components <<< "$ONLY"
    (( ${#requested_components[@]} > 0 )) || fail 'no helper component selected'
    for component in "${requested_components[@]}"; do
        case "$component" in
            ffmpeg|atracdenc|xdelta3|chdman|libcrypt-patcher|psx-undither|python) ;;
            *) fail "unknown helper component: $component" ;;
        esac
    done
fi

[[ "$(uname -s)" == 'Darwin' ]] || fail 'helper builds require macOS'
[[ "$(uname -m)" == 'arm64' ]] || fail 'helper builds require Apple Silicon'

resolve_python
"$PYTHON_BIN" - <<'PY' || fail \
    'helper builds require a native arm64 Python 3.12 (activate it with pyenv or set PYTHON_BIN)'
import platform
import sys

if sys.version_info[:2] != (3, 12) or platform.machine() != "arm64":
    raise SystemExit(1)
PY

for command in \
    "$PYTHON_BIN" clang cmake curl ditto git install_name_tool libtool make \
    otool patch shasum tar; do
    command -v "$command" >/dev/null || fail "required build command not found: $command"
done

mkdir -p "$BUILD_ROOT" "$DOWNLOAD_ROOT" "$STAGE_ROOT"
WORK_ROOT="$(mktemp -d "$BUILD_ROOT/helpers-work.XXXXXX")"
SNDFILE_PREFIX="$WORK_ROOT/libsndfile-prefix"

cleanup() {
    case "$WORK_ROOT" in
        "$BUILD_ROOT"/helpers-work.*) rm -rf "$WORK_ROOT" ;;
        *) say "refusing to remove unexpected work directory: $WORK_ROOT" ;;
    esac
}
trap cleanup EXIT

lock_field() {
    "$PYTHON_BIN" - "$LOCK_FILE" "$1" "$2" <<'PY'
import json
import pathlib
import sys

lock = json.loads(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8"))
print(lock["dependencies"][sys.argv[2]][sys.argv[3]])
PY
}

component_enabled() {
    [[ "$ONLY" == 'all' || ",$ONLY," == *",$1,"* ]]
}

download_archive() {
    local dependency="$1"
    local url filename expected archive temporary actual
    url="$(lock_field "$dependency" url)"
    filename="$(lock_field "$dependency" filename)"
    expected="$(lock_field "$dependency" sha256)"
    archive="$DOWNLOAD_ROOT/$filename"
    temporary="$archive.partial"

    if [[ -f "$archive" ]]; then
        actual="$(shasum -a 256 "$archive" | awk '{print $1}')"
        if [[ "$actual" == "$expected" ]]; then
            printf '%s\n' "$archive"
            return
        fi
        say "discarding cached $filename with an invalid SHA-256"
        rm -f "$archive"
    fi

    say "downloading $dependency"
    rm -f "$temporary"
    if ! curl --fail --location --retry 3 --output "$temporary" "$url"; then
        rm -f "$temporary"
        fail "could not download $dependency"
    fi
    actual="$(shasum -a 256 "$temporary" | awk '{print $1}')"
    [[ "$actual" == "$expected" ]] || fail "SHA-256 mismatch for $dependency"
    mv "$temporary" "$archive"
    printf '%s\n' "$archive"
}

extract_archive() {
    local dependency="$1"
    local destination="$2"
    local archive
    archive="$(download_archive "$dependency")"
    mkdir -p "$destination"
    tar -xf "$archive" --strip-components=1 -C "$destination"
}

assert_submodule_revision() {
    local dependency="$1"
    local path expected actual
    path="$(lock_field "$dependency" path)"
    expected="$(lock_field "$dependency" revision)"
    [[ -e "$REPOSITORY_ROOT/$path/.git" ]] || \
        fail "submodule is not initialized: $path"
    actual="$(git -C "$REPOSITORY_ROOT/$path" rev-parse HEAD)"
    [[ "$actual" == "$expected" ]] || \
        fail "$path is at $actual; expected locked revision $expected"
}

install_helper() {
    local source="$1"
    local name="$2"
    [[ -f "$source" ]] || fail "expected helper was not built: $source"
    install -m 0755 "$source" "$STAGE_ROOT/$name"
}

build_ffmpeg() {
    local source="$WORK_ROOT/ffmpeg-source"
    extract_archive ffmpeg "$source"
    say 'building FFmpeg'
    (
        cd "$source"
        ./configure \
            --prefix="$WORK_ROOT/ffmpeg-prefix" \
            --arch=arm64 \
            --target-os=darwin \
            --cc=clang \
            --disable-shared \
            --enable-static \
            --disable-doc \
            --disable-debug \
            --disable-ffplay \
            --disable-ffprobe \
            --disable-network \
            --disable-autodetect \
            --disable-iconv \
            --disable-securetransport \
            --disable-videotoolbox \
            --disable-audiotoolbox \
            --extra-cflags="-arch arm64 -mmacosx-version-min=$MINIMUM_MACOS" \
            --extra-ldflags="-arch arm64 -mmacosx-version-min=$MINIMUM_MACOS"
    )
    make -C "$source" -j "$JOBS" ffmpeg
    install_helper "$source/ffmpeg" ffmpeg
}

build_libsndfile() {
    local source="$WORK_ROOT/libsndfile-source"
    local build="$WORK_ROOT/libsndfile-build"
    extract_archive libsndfile "$source"
    say 'building static libsndfile for ATRACDENC'
    cmake -S "$source" -B "$build" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
        -DCMAKE_INSTALL_PREFIX="$SNDFILE_PREFIX" \
        -DCMAKE_OSX_ARCHITECTURES=arm64 \
        -DCMAKE_OSX_DEPLOYMENT_TARGET="$MINIMUM_MACOS" \
        -DBUILD_SHARED_LIBS=OFF \
        -DBUILD_PROGRAMS=OFF \
        -DBUILD_EXAMPLES=OFF \
        -DBUILD_REGTEST=OFF \
        -DBUILD_TESTING=OFF \
        -DENABLE_EXTERNAL_LIBS=OFF \
        -DENABLE_MPEG=OFF \
        -DENABLE_CPACK=OFF
    cmake --build "$build" --parallel "$JOBS"
    cmake --install "$build"
}

build_atracdenc() {
    local build source
    assert_submodule_revision atracdenc
    build_libsndfile
    source="$REPOSITORY_ROOT/atracdenc"
    build="$WORK_ROOT/atracdenc-build"
    say 'building ATRACDENC'
    cmake -S "$source" -B "$build" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
        -DCMAKE_OSX_ARCHITECTURES=arm64 \
        -DCMAKE_OSX_DEPLOYMENT_TARGET="$MINIMUM_MACOS" \
        -DLIBSNDFILE_INCLUDE_DIR="$SNDFILE_PREFIX/include" \
        -DSNDFILE_LIBRARY="$SNDFILE_PREFIX/lib/libsndfile.a"
    cmake --build "$build" --parallel "$JOBS" --target atracdenc
    install_helper "$build/src/atracdenc" atracdenc
}

build_xdelta3() {
    local source="$WORK_ROOT/xdelta-source"
    local build="$WORK_ROOT/xdelta-build"
    extract_archive xdelta3 "$source"
    say 'building Xdelta3'
    cmake -S "$source/xdelta3" -B "$build" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_OSX_ARCHITECTURES=arm64 \
        -DCMAKE_OSX_DEPLOYMENT_TARGET="$MINIMUM_MACOS" \
        -DBUILD_SHARED_LIBS=OFF \
        -DXD3_ARMOR=OFF \
        -DXD3_LZMA_MODE=off \
        -DXD3_BUILD_LIB=OFF \
        -DXD3_BUILD_TESTS=OFF
    cmake --build "$build" --parallel "$JOBS" --target xdelta3
    install_helper "$build/xdelta3" xdelta3
}

build_chdman() {
    local source="$WORK_ROOT/mame-source"
    extract_archive mame-chdman "$source"
    say 'building MAME CHDMan (this is the longest helper build)'
    make -C "$source" -j "$JOBS" \
        REGENIE=1 \
        TOOLS=1 \
        EMULATOR=0 \
        OSD=mac \
        PTR64=1 \
        OVERRIDE_CC=clang \
        OVERRIDE_CXX=clang++ \
        ARCHOPTS="-arch arm64 -mmacosx-version-min=$MINIMUM_MACOS"
    install_helper "$source/chdman" chdman
}

build_libcrypt_patcher() {
    local source="$WORK_ROOT/libcrypt-source"
    local enigma="$WORK_ROOT/lib-enigma-source"
    local build="$WORK_ROOT/libcrypt-build"
    local -a flags
    extract_archive libcrypt-patcher "$source"
    extract_archive lib-enigma "$enigma"
    mkdir -p "$build" "$source/lib-enigma"
    flags=(-arch arm64 "-mmacosx-version-min=$MINIMUM_MACOS" -O3)
    say 'building LibCrypt Patcher'
    clang "${flags[@]}" \
        -Wno-return-type \
        -Wno-unused-but-set-variable \
        -Wno-unused-variable \
        -c "$enigma/lib-enigma.c" \
        -o "$build/lib-enigma.o"
    libtool -static -o "$build/libenigma.a" "$build/lib-enigma.o"
    install -m 0644 "$enigma/lib-enigma.h" "$source/lib-enigma/lib-enigma.h"
    clang "${flags[@]}" \
        '-DVERSION="v1.1.0"' \
        "$source/lcp.c" \
        "$build/libenigma.a" \
        -o "$build/lcp"
    install_helper "$build/lcp" lcp
}

build_psx_undither() {
    local source="$REPOSITORY_ROOT/psx-undither"
    local cdid="$source/lib-ps-cd-id"
    local build="$WORK_ROOT/psx-undither-build"
    local -a flags
    assert_submodule_revision psx-undither
    assert_submodule_revision lib-ps-cd-id
    mkdir -p "$build"
    flags=(-arch arm64 "-mmacosx-version-min=$MINIMUM_MACOS" -O3)
    say 'building PSX-Undither'
    clang "${flags[@]}" -c "$cdid/lib-ps-cd-id.c" -o "$build/lib-ps-cd-id.o"
    libtool -static -o "$build/libpscdid.a" "$build/lib-ps-cd-id.o"
    clang "${flags[@]}" -c "$source/error_recalc.c" -o "$build/error_recalc.o"
    clang "${flags[@]}" \
        -Wno-gnu-folding-constant \
        '-DVERSION="v1.0"' \
        -I "$cdid" \
        "$source/psx-undither.c" \
        "$build/error_recalc.o" \
        "$build/libpscdid.a" \
        -o "$build/psxund"
    install_helper "$build/psxund" psxund
}

pyinstaller_helper() {
    local name="$1"
    local source="$2"
    shift 2
    PYINSTALLER_CONFIG_DIR="$WORK_ROOT/pyinstaller-cache" \
    "$PYTHON_BIN" -m PyInstaller \
        --noconfirm \
        --clean \
        --onefile \
        --target-architecture arm64 \
        --name "$name" \
        --distpath "$STAGE_ROOT" \
        --workpath "$WORK_ROOT/pyinstaller-work/$name" \
        --specpath "$WORK_ROOT/pyinstaller-specs" \
        "$@" \
        "$source"
}

strip_local_rpaths() {
    local binary="$1"
    local rpath
    while IFS= read -r rpath; do
        case "$rpath" in
            @*|/System/*|/usr/lib/*) ;;
            *)
                say "removing local build rpath from $(basename "$binary"): $rpath"
                install_name_tool -delete_rpath "$rpath" "$binary"
                ;;
        esac
    done < <(
        otool -l "$binary" | awk '
            $1 == "cmd" && $2 == "LC_RPATH" { capture = 1; next }
            capture && $1 == "path" { print $2; capture = 0 }
        '
    )
}

build_python_helpers() {
    local ps3py="$WORK_ROOT/ps3py"
    local pkgcrypt_extension
    assert_submodule_revision cue2cu2
    assert_submodule_revision binmerge
    assert_submodule_revision ps3py
    "$PYTHON_BIN" -c 'import PyInstaller, ecdsa, setuptools' || \
        fail 'Python helper builds require pyinstaller, ecdsa, and setuptools'

    say 'freezing Python helper executables'
    pyinstaller_helper cue2cu2 "$REPOSITORY_ROOT/Cue2cu2/cue2cu2.py"
    pyinstaller_helper binmerge "$REPOSITORY_ROOT/binmerge/binmerge"
    pyinstaller_helper sign3 "$REPOSITORY_ROOT/sign3.py"

    mkdir -p "$ps3py"
    ditto "$REPOSITORY_ROOT/PSL1GHT/tools/ps3py" "$ps3py"
    patch -d "$ps3py" -p1 < "$SCRIPT_DIR/patches/ps3py-setuptools.patch"
    (
        cd "$ps3py"
        ARCHFLAGS='-arch arm64' \
        MACOSX_DEPLOYMENT_TARGET="$MINIMUM_MACOS" \
            "$PYTHON_BIN" setup.py build_ext --inplace
    )
    pkgcrypt_extension="$(find "$ps3py" -maxdepth 1 -name 'pkgcrypt*.so' -print -quit)"
    [[ -n "$pkgcrypt_extension" ]] || fail 'pkgcrypt extension was not built'
    strip_local_rpaths "$pkgcrypt_extension"
    "$SCRIPT_DIR/verify-mach-o.sh" "$pkgcrypt_extension"
    pyinstaller_helper pkg "$ps3py/pkg.py" \
        --paths "$ps3py" \
        --hidden-import pkgcrypt
}

component_enabled ffmpeg && build_ffmpeg
component_enabled atracdenc && build_atracdenc
component_enabled xdelta3 && build_xdelta3
component_enabled chdman && build_chdman
component_enabled libcrypt-patcher && build_libcrypt_patcher
component_enabled psx-undither && build_psx_undither
component_enabled python && build_python_helpers

"$SCRIPT_DIR/verify-mach-o.sh" "$STAGE_ROOT"
say "helpers staged in $STAGE_ROOT"
