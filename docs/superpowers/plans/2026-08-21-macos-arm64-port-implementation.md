# macOS Apple Silicon Port Implementation Plan

**Design:** `docs/superpowers/specs/2026-08-21-macos-arm64-port-design.md`

**Branch:** `codex/macos-arm64-port`

**Target:** A self-contained, ad-hoc-signed macOS 14+ Apple Silicon DMG with
the PSP GUI, PS3 GUI, and full POP-FE CLI.

## Working rules

- Keep each phase independently reviewable and commit it only after its stated
  checks pass.
- Add regression tests before or with behavior changes.
- Preserve the existing Windows and Linux branches unless the runtime adapter
  explicitly replaces them with equivalent behavior.
- Never rely on the application current directory, the user's `PATH`,
  Homebrew, or a writable application bundle in packaged mode.
- Use only redistributable fixtures and dependencies, retain licenses, and pin
  every downloaded source or binary with a checksum.
- Treat the existing case-only checkout collision as upstream data to repair;
  never include the macOS checkout's accidental binary modification in a
  commit.

## Phase 1: Make the repository portable to a case-insensitive checkout

**Files**

- Remove redundant uppercase variants below `pspconfigs/` while retaining the
  lowercase paths referenced by `gamedb.py`.
- Remove `testimages/vs/vs.CUE` and retain `testimages/vs/vs.cue`.
- Modify `.github/workflows/py.yml` so the uppercase-extension test copies the
  lowercase fixture to a temporary uppercase filename during the job.
- Add `tests/test_repository_portability.py` to reject future case-folded path
  collisions.

**Checks**

```sh
python3 -m unittest tests.test_repository_portability -v
git status --short
git diff --check
```

**Commit:** `build: remove case-insensitive path collisions`

## Phase 2: Introduce the platform runtime adapter

**Files**

- Add `popfe_runtime.py` containing a `RuntimePaths` value object and pure
  helpers for source/frozen resource lookup, tool lookup, user data paths,
  unique work directories, preference files, logs, and mounted-volume roots.
- Add `tests/test_popfe_runtime.py` using only `unittest`, `tempfile`, and mocks
  from the Python standard library.
- Add `tests/__init__.py` so tests are directly addressable on every CI host.

**Behavior**

- Source runs resolve resources from the repository directory.
- PyInstaller runs resolve resources from `sys._MEIPASS` and the executable's
  bundle location.
- macOS preferences, logs, and cache paths follow the design document.
- Windows and Linux retain user-facing behavior while gaining explicit path
  objects.
- Tool lookup returns bundled absolute paths first and uses `PATH` only for
  non-frozen source runs.
- Work directories are unique and carry enough metadata for cleanup and
  diagnostic reporting.

**Checks**

```sh
python3 -m unittest tests.test_popfe_runtime -v
python3 -m compileall -q popfe_runtime.py tests
git diff --check
```

**Commit:** `refactor: add cross-platform runtime paths`

## Phase 3: Route backend resources and helper processes through the adapter

**Files**

- Modify `pop-fe.py` to initialize one runtime context and resolve
  `PS3LOGO.DAT`, databases, patches, configs, and helper programs through it.
- Modify `gamedb.py` only where database values must become resource-relative
  rather than current-directory-relative.
- Extend `tests/test_popfe_runtime.py` and add focused subprocess argument tests
  in `tests/test_popfe_tools.py`.

**Behavior**

- Replace `python3 <helper.py>` calls with the frozen Python helper entry point
  or current interpreter in source mode.
- Resolve FFmpeg, CHDMan, Xdelta3, ATRACDENC, LibCrypt Patcher,
  PSX-Undither, CUE2CU2, binmerge, `sign3`, and PS3 package tooling by logical
  tool name.
- Use absolute paths and argument arrays; do not invoke a shell.
- Preserve Windows `.exe` names and existing Linux fallbacks.
- Raise a typed, actionable error before conversion when a required helper is
  absent.

**Checks**

```sh
python3 -m unittest tests.test_popfe_runtime tests.test_popfe_tools -v
python3 -m compileall -q pop-fe.py gamedb.py popfe_runtime.py tests
git diff --check
```

**Commit:** `refactor: resolve resources and tools portably`

## Phase 4: Move GUI mutable state out of the application directory

**Files**

- Modify `pop-fe-psp.py` and `pop-fe-ps3.py` to use the runtime adapter for UI
  resources, preferences, logs, and per-run work directories.
- Add `tests/test_gui_paths.py` without creating a Tk window; test extracted
  path and preference helpers in isolation.

**Behavior**

- GUI configuration lives in Application Support on macOS.
- Every reset creates or reuses only the active run's cache directory.
- Successful conversions clean their work directory; failures retain it.
- Finder launch and Terminal launch behave identically.
- Errors surface a concise message and the log path without redesigning the
  interface.

**Checks**

```sh
python3 -m unittest tests.test_gui_paths -v
python3 -m compileall -q pop-fe-psp.py pop-fe-ps3.py
git diff --check
```

**Commit:** `feat: use per-user state for graphical apps`

## Phase 5: Add macOS removable-volume discovery

**Files**

- Modify `popfe_runtime.py` with volume enumeration and target predicates.
- Modify `pop-fe.py` functions `find_psp_mount` and `find_psc_mount` to use the
  adapter on Darwin while preserving Linux `/proc/self/mounts` and Windows
  drive enumeration.
- Add fixtures and cases to `tests/test_popfe_runtime.py` for PSP, Vita,
  PlayStation Classic, irrelevant, unreadable, and multiple candidate volumes.

**Checks**

```sh
python3 -m unittest tests.test_popfe_runtime -v
python3 -m compileall -q pop-fe.py popfe_runtime.py
git diff --check
```

**Commit:** `feat: discover PlayStation volumes on macOS`

## Phase 6: Build native Apple Silicon helper dependencies

**Files**

- Add `packaging/macos/dependencies.lock.json` with source URL, immutable
  revision, SHA-256, license, and expected output for every helper.
- Add `packaging/macos/build-helpers.sh` to build into a fresh staging prefix.
- Add `packaging/macos/verify-mach-o.sh` to require `arm64`, validate dynamic
  library closure, and reject references to Homebrew or the build workspace.
- Add `packaging/macos/patches/` only for minimal reproducible upstream
  compatibility patches that cannot be expressed as build flags.
- Add `THIRD_PARTY_NOTICES.md` or extend it with every bundled component.

**Behavior**

- Build ATRACDENC and PSX-Undither with Darwin-compatible flags.
- Freeze or embed CUE2CU2, binmerge, `sign3`, and PS3 Python helpers without
  depending on `/usr/bin/python3`.
- Replace PS3 `distutils` imports with supported Python 3.12 equivalents in a
  reproducible patch or local compatibility module.
- Stage FFmpeg, CHDMan, Xdelta3, and LibCrypt Patcher as verified `arm64`
  binaries built from pinned sources.

**Checks**

```sh
packaging/macos/build-helpers.sh
packaging/macos/verify-mach-o.sh build/macos/helpers
file build/macos/helpers/*
git diff --check
```

**Commit:** `build: compile macOS arm64 helper tools`

## Phase 7: Package the CLI and application bundles

**Files**

- Add `packaging/macos/pop-fe-cli.spec`.
- Add `packaging/macos/pop-fe-psp.spec`.
- Add `packaging/macos/pop-fe-ps3.spec`.
- Add `packaging/macos/build-apps.sh` to create clean PyInstaller builds with
  explicit data, hidden imports, icons, bundle identifiers, and `arm64` target.
- Add a small launcher/runtime hook only if required to establish application
  logging or Finder-safe process state.

**Checks**

```sh
packaging/macos/build-apps.sh
packaging/macos/verify-mach-o.sh build/macos/dist
build/macos/dist/pop-fe/pop-fe --help
python3 -m unittest discover -s tests -v
git diff --check
```

**Commit:** `build: package Apple Silicon applications`

## Phase 8: Sign and assemble the DMG

**Files**

- Add `packaging/macos/sign-apps.sh` for inside-out ad-hoc signing.
- Add `packaging/macos/create-dmg.sh` for deterministic staging, Applications
  symlink, CLI, installer command, README, licenses, and checksum.
- Add `packaging/macos/Install CLI.command` with a user-writable default.
- Add `packaging/macos/README-macOS.txt` with the exact Gatekeeper Open Anyway
  flow and uninstall paths.
- Add `packaging/macos/smoke-dmg.sh` to attach, inspect, run CLI smoke checks,
  and detach the image.

**Checks**

```sh
packaging/macos/sign-apps.sh build/macos/dist
packaging/macos/create-dmg.sh
packaging/macos/smoke-dmg.sh build/macos/Pop-FE-*-macOS-arm64.dmg
codesign --verify --deep --strict --verbose=2 build/macos/dist/*.app
shasum -a 256 build/macos/Pop-FE-*-macOS-arm64.dmg
git diff --check
```

**Commit:** `build: create ad-hoc-signed macOS DMG`

## Phase 9: Add macOS CI and release automation

**Files**

- Add `.github/workflows/macos.yml` using an Apple Silicon macOS runner and
  Python 3.12 with Tk support.
- Update release documentation and workflow permissions only as required to
  attach tagged DMG/checksum artifacts.
- Keep `.github/workflows/py.yml` Linux and Windows jobs required.

**Behavior**

- Pull requests build, test, sign, smoke-test, and upload an ephemeral artifact.
- Version tags additionally publish the DMG and checksum to GitHub Releases.
- Cache keys include the dependency lock and build scripts; cache contents are
  revalidated before packaging.

**Checks**

```sh
python3 -c "import pathlib, yaml; yaml.safe_load(pathlib.Path('.github/workflows/macos.yml').read_text())"
python3 -m unittest discover -s tests -v
git diff --check
```

The YAML parse command runs in the packaging environment where PyYAML is an
explicit build dependency.

**Commit:** `ci: build and verify macOS arm64 release`

## Phase 10: Complete parity tests and user documentation

**Files**

- Add deterministic smoke scripts below `tests/integration/` for each target
  supported by the CLI.
- Update `README` with macOS installation, Gatekeeper, CLI, supported inputs,
  logging, cleanup, and limitations.
- Add `docs/macos-release-checklist.md` recording the clean-machine and
  real-device checks from the design.

**Checks**

```sh
python3 -m unittest discover -s tests -v
packaging/macos/smoke-dmg.sh build/macos/Pop-FE-*-macOS-arm64.dmg
git diff --check
git status --short
```

Run the documented PSP/Vita and PS3 manual checks with legal media when the
hardware is available, and record unavailable hardware checks honestly rather
than treating them as passed.

**Commit:** `docs: document macOS release and validation`

## Pull request completion

Before opening the upstream PR:

1. rebase the branch onto the current upstream default branch;
2. run Linux-compatible unit tests locally and all GitHub checks remotely;
3. download the CI-built DMG onto a clean Apple Silicon Mac and repeat the
   release checklist;
4. review the complete diff for generated files, private paths, unpinned
   downloads, and licenses;
5. summarize functional parity, unsigned Gatekeeper behavior, tested macOS
   versions, artifact checksum, known limitations, and manual device results in
   the PR body.
