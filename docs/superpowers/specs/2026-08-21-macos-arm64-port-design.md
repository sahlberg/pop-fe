# macOS Apple Silicon Port Design

**Status:** Approved for implementation planning

**Date:** 2026-08-21

**Target:** macOS 14 or later on Apple Silicon (`arm64`)

## Context

POP-FE currently supports Linux and Windows and converts PlayStation disc
images for PSP/Vita, PSIO, PS2, PS3, RetroArch, and PlayStation Classic. The
Windows release bundles Python and helper executables, while much of the
runtime assumes that the current working directory is writable and that
external programs can be found through relative paths or `PATH`.

The macOS release must provide the same conversion capabilities as the
Windows release without requiring users to install Python, Homebrew, or any
other runtime dependency. It will be distributed from GitHub as a disk image,
outside the Mac App Store, and will deliberately use ad-hoc code signing
instead of paid Developer ID signing and notarization. Users therefore need to
approve the first launch through macOS Privacy & Security.

## Goals

- Deliver one Apple Silicon-only artifact named
  `Pop-FE-<version>-macOS-arm64.dmg`.
- Preserve the existing Python conversion backend and Tk/pygubu user
  interfaces rather than rewriting them in a macOS-native framework.
- Provide graphical entry points for the PSP/Vita EBOOT and PS3 PKG workflows.
- Bundle a command-line entry point that exposes every target supported by the
  existing Windows command-line build: PSP/Vita, PSIO, PS2, PS3, RetroArch,
  and PlayStation Classic.
- Support the same accepted inputs and conversion options, including
  single-disc and multi-disc images, CUE/BIN, CCD/IMG, ZIP, CHD, CDDA/ATRAC3,
  LibCrypt patches, PSX-Undither, manuals, artwork, themes, and PPF/Xdelta ROM
  hacks where applicable.
- Build and test the distributable artifact in GitHub Actions.
- Keep existing Linux and Windows behavior and tests working.

## Non-goals

- Intel (`x86_64`) Macs and universal binaries.
- Mac App Store distribution.
- Developer ID signing, Apple notarization, or automatic Gatekeeper approval.
- A native Swift/SwiftUI rewrite or visual redesign.
- Automatic application updates.
- Requiring Homebrew, MacPorts, a system Python installation, Rosetta 2, or
  developer tools on the end user's Mac.

## Distribution and user experience

The DMG contains:

```text
Pop-FE-<version>-macOS-arm64.dmg
├── Pop-FE PSP.app
├── Pop-FE PS3.app
├── pop-fe
├── Install CLI.command
├── Applications -> /Applications
└── README-macOS.txt
```

The two application bundles launch the current Tk interfaces. The `pop-fe`
executable is a self-contained command-line build. `Install CLI.command`
offers to install that executable into a user-selected location and must not
require administrator access by default. Users may instead copy or invoke the
CLI directly from the mounted image.

The applications and executables are ad-hoc signed after assembly. The README
explains that the first launch will be blocked because the application is not
notarized and gives the supported flow: attempt to open it once, then use
System Settings > Privacy & Security > Open Anyway. The project does not ask
users to disable Gatekeeper globally and does not remove quarantine attributes
programmatically.

The release page publishes the DMG and a SHA-256 checksum. The artifact name,
application metadata, and `--version` output all derive from one version value.

## Architecture

### Existing application layers

The existing backend in `pop-fe.py`, supporting Python modules, databases, and
Tk/pygubu interfaces remain the source of truth. Platform-specific behavior is
moved behind a small runtime layer instead of being distributed through new
`sys.platform` branches across the codebase.

The runtime layer owns:

- discovery of immutable bundled resources;
- discovery and validation of bundled helper tools;
- application support, cache, log, and preferences paths;
- creation and cleanup of per-run working directories;
- removable-volume discovery;
- subprocess environment and invocation;
- frozen-versus-source execution differences.

Linux and Windows continue to use their current locations and executable
names unless a change is required to route them through this layer.

### macOS filesystem model

Packaged resources are read-only and live below each bundle's
`Contents/Resources` directory. The application never assumes its bundle,
mounted DMG, or current working directory is writable.

Mutable files use standard per-user directories:

| Purpose | Location |
| --- | --- |
| Preferences | `~/Library/Application Support/Pop-FE/` |
| Logs | `~/Library/Logs/Pop-FE/` |
| Per-run working data | `~/Library/Caches/Pop-FE/<unique-run-id>/` |
| Final output | User-selected directory or mounted target |

Each conversion receives a unique work directory. Paths passed to the backend
are absolute so launching from Finder, Terminal, the DMG, or `/Applications`
produces the same behavior. Successful conversions remove their work
directory. Failed conversions retain it and report its location for diagnosis.

User preferences are stored outside the bundle. Existing relative GUI config
files migrate on first launch when found in a source checkout; packaged builds
write only to Application Support.

### Resources and case sensitivity

Data files such as `PS3LOGO.DAT`, `libcrypt`, `ppf`, `ps3configs`,
`pspconfigs`, UI definitions, themes, and icons are accessed through the
runtime resource resolver.

The repository currently contains names that differ only by letter case,
including PSP config pairs and the upper/lower-case CUE fixtures. A normal
checkout on the default case-insensitive macOS filesystem cannot represent
both paths. Before packaging, colliding resources are normalized to unique
portable names or deduplicated when their contents are identical. Tests that
exercise case-insensitive extensions generate or copy their fixtures at test
time rather than tracking case-only filename pairs.

### Helper tools

The artifact bundles native `arm64` builds or frozen Python executables for all
helpers required by supported workflows:

- FFmpeg;
- CHDMan;
- Xdelta3;
- ATRACDENC;
- LibCrypt Patcher;
- PSX-Undither;
- CUE2CU2;
- binmerge;
- PS3 `pkg`/`pkgcrypt` support;
- `sign3`.

Build inputs are pinned to auditable versions or submodule commits. Python
helpers run inside the frozen distribution and do not launch `python3` from
the user's `PATH`. Native helpers are invoked by absolute bundle paths.
Packaging verifies that native Mach-O files contain the `arm64` architecture
and that their dynamic-library references resolve inside the bundle or to
macOS system libraries.

The PS3 helper is updated away from the removed `distutils` API so the pinned
Python 3.12 build works. PSX-Undither receives portable compiler and linker
settings for Darwin: no Linux static-link flags and no deprecated optimization
mode promoted to an error.

Every bundled third-party component retains its required license and notice.
The release documentation records source revision, build flags, and license.

### Python application packaging

GitHub Actions builds on an Apple Silicon macOS runner using a pinned Python
3.12 `arm64` interpreter with Tk support. PyInstaller creates the two `.app`
bundles and the CLI distribution. Common Python code and resources may be
duplicated between the three deliverables in the first release when that keeps
the build deterministic and avoids fragile cross-bundle links.

PyInstaller specifications explicitly declare hidden imports, Tk/pygubu
resources, native helpers, game databases, configuration data, and licenses.
No build step depends on files left over from an earlier target build.

The deployment target is macOS 14. Building on the oldest supported macOS
runner prevents accidental linkage to newer SDK functionality.

## Conversion flow

1. A GUI or CLI entry point creates a run context through the runtime layer.
2. The context resolves resources, creates a unique work directory, opens a
   log file, and validates helpers required by the selected options.
3. Input paths are normalized without modifying the source images.
4. The existing conversion backend performs extraction, patching, artwork and
   manual processing, audio conversion, and target packaging inside the work
   directory.
5. Output is written to a temporary file or directory beside its final
   destination and renamed into place only after validation succeeds.
6. On success, the UI reports the destination and the run context removes
   temporary data. On failure, partial final output is removed, the working
   directory is retained, and the UI or CLI reports both the error and log
   location.

Network asset fetching remains optional. If remote artwork, metadata, theme,
or manual sources fail, the conversion proceeds when local/default resources
are sufficient and reports which optional asset was unavailable.

## Removable media

The Linux `/proc/self/mounts` implementation remains in place for Linux.
macOS automatic PSP/Vita and PlayStation Classic discovery scans mounted
volumes below `/Volumes` and validates a candidate by its expected directory
layout rather than by volume name alone. Explicit paths always take precedence
over automatic discovery.

Writes to removable media use the same staged-output rule. Permission errors,
read-only media, unavailable space, and a device being disconnected are
reported without leaving a valid-looking partial package.

## Error handling and diagnostics

Before conversion starts, the application validates the input set, output
destination, free space when determinable, required bundled resources, helper
existence, helper architecture, and executable permission.

The GUI displays a concise actionable error and the log path. The CLI writes a
concise error to standard error and exits non-zero. Detailed logs include the
application version, macOS version, architecture, selected operation, helper
versions, sanitized commands, exit codes, and exception tracebacks. Logs do
not include secrets, downloaded credentials, or entire copyrighted image
contents.

Subprocess failures include the helper name and its useful stderr tail. A
missing or incompatible helper is a packaging defect, not an invitation to
install software at runtime.

## Build and release workflow

A dedicated GitHub Actions macOS job performs these stages from a clean
checkout:

1. initialize pinned submodules and Python dependencies;
2. build or obtain each helper for `arm64`;
3. run Python unit and portability tests;
4. run representative PSP and PS3 conversion smoke tests;
5. assemble the CLI and both application bundles;
6. verify resources, Mach-O architectures, dynamic-library closure, and
   executable permissions;
7. ad-hoc sign nested binaries first and application bundles last;
8. verify signatures with `codesign`;
9. build the DMG, mount it, and smoke-test its layout and launch executables;
10. generate the SHA-256 checksum and upload both artifacts.

Tagged releases attach the artifacts to GitHub Releases. Pull requests build
an artifact for review but do not publish a release. Existing Linux tests and
the Windows PyInstaller build remain required checks.

## Test strategy

### Automated tests

- Unit-test platform path selection, source/frozen resource lookup, executable
  suffix selection, work-directory lifecycle, and `/Volumes` discovery using
  isolated temporary directories.
- Test paths containing spaces, non-ASCII characters, and mixed-case
  extensions.
- Test helper resolution without depending on the process current directory or
  `PATH`.
- Test clean success, helper failure, network failure, and interrupted output
  handling.
- Run representative single- and multi-disc PSP EBOOT conversions.
- Run representative single- and multi-disc PS3 PKG conversions.
- Exercise CUE/BIN, CCD/IMG, ZIP, and CHD ingestion.
- Cover CDDA/ATRAC3, LibCrypt, PSX-Undither, manuals, and PPF/Xdelta paths with
  focused tests or deterministic fixtures where redistribution permits.
- Exercise the CLI parser and one smoke conversion for every output target
  exposed by the Windows build.
- Mount the generated DMG and verify both app bundles and the CLI.

Large or copyrighted game images are never added to the repository. Existing
synthetic fixtures are reused and additional minimal fixtures are generated or
stored only when their license permits redistribution.

### Manual release acceptance

Test on a clean Apple Silicon Mac that has no Homebrew and no user-installed
Python:

- mount the DMG and copy both applications to `/Applications`;
- complete the documented Privacy & Security > Open Anyway flow;
- launch both applications from Finder;
- create and validate a PSP/Vita EBOOT and PS3 PKG from known-good legal test
  media, including a multi-disc conversion when available;
- invoke the CLI directly and after running `Install CLI.command`;
- detect and write to a PSP/Vita or PlayStation Classic volume below
  `/Volumes` when hardware is available;
- confirm uninstall consists of deleting the apps/CLI and optionally the
  documented user data directories.

## Acceptance criteria

The port is ready for an upstream pull request when:

- the DMG is produced reproducibly by GitHub Actions from a clean checkout;
- all bundled executables and libraries are Apple Silicon-native;
- the applications run without Python, package-manager, network, or developer
  tool prerequisites for conversions using local assets;
- graphical PSP/Vita and PS3 workflows match the functional options of their
  Windows counterparts;
- the CLI exposes every target and relevant option exposed by Windows;
- representative PSP EBOOT and PS3 PKG outputs pass existing structural checks
  and real-device/emulator validation available to the project;
- application data never requires the current directory or app bundle to be
  writable;
- expected failures leave no valid-looking partial final output and point the
  user to a diagnostic log;
- existing Linux and Windows CI remains green;
- installation and Gatekeeper instructions accurately match the unsigned,
  non-notarized release.

## Delivery structure

The pull request should be reviewable as four logical commit groups:

1. portable paths, process execution, removable-media discovery, and
   case-collision cleanup;
2. Darwin-compatible helper builds and pinned dependency metadata;
3. PyInstaller, signing, DMG, and GitHub Actions release automation;
4. automated tests, manual validation record, user documentation, and license
   notices.

This grouping keeps platform-neutral changes separate from packaging and makes
it possible for upstream maintainers to review or revise individual decisions
without discarding the entire port.

## Risks and mitigations

- **Gatekeeper friction:** document the exact per-app Open Anyway process and
  never claim that an ad-hoc signature is notarization.
- **Native dependency availability:** build every helper early, pin sources,
  and fail CI on non-`arm64` or unresolved binaries.
- **Case-insensitive filesystem collisions:** normalize tracked names before
  relying on macOS CI or local checkouts.
- **Large bundle size:** favor reliability in the first release; measure and
  deduplicate only after parity tests pass.
- **Upstream churn:** keep the runtime adapter narrow and commits scoped so the
  branch can be rebased onto active POP-FE development.
- **Sparse real-hardware coverage:** combine deterministic conversion tests
  with a documented manual device matrix and record exactly which checks were
  performed for each release.
