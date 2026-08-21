# macOS Apple Silicon release checklist

Use this checklist for every `Pop-FE-<version>-macOS-arm64.dmg` release. Do not
mark hardware or Gatekeeper checks as passed unless they were run against the
exact downloaded release candidate.

## Build provenance

- [ ] Build runs from a clean checkout of the release tag on `macos-14` ARM64.
- [ ] Recursive submodules match `packaging/macos/dependencies.lock.json`.
- [ ] Python is ARM64 3.12.13 with Tk 8.6 or newer.
- [ ] `POPFE_VERSION` matches the tag, both application plists, `pop-fe
      --version`, the DMG filename, and the checksum filename.
- [ ] The helper and Python requirement lock files have no unreviewed changes.
- [ ] `python -m unittest discover -s tests -v` passes.

## Artifact verification

Run:

```sh
packaging/macos/build-helpers.sh
packaging/macos/build-apps.sh
tests/integration/smoke-macos-conversions.sh build/macos/dist/pop-fe
packaging/macos/create-dmg.sh
packaging/macos/smoke-dmg.sh build/macos/Pop-FE-*-macOS-arm64.dmg
```

- [ ] Every Mach-O is ARM64 and has no Homebrew, build-directory, or temporary
      load path.
- [ ] Ad-hoc signatures pass `codesign --verify --deep --strict`.
- [ ] The SHA-256 file validates the exact DMG.
- [ ] The mounted image contains both applications, the CLI, CLI installer,
      Applications link, user instructions, notices, and collected licenses.
- [ ] The mounted CLI reports the release version and its help text.
- [ ] Both GUI entry points initialize Tk; PS3 also initializes TkDnD.
- [ ] The CLI installer succeeds without `sudo` into a temporary user-owned
      destination and the installed CLI starts.

## Clean-machine Gatekeeper check

Download the candidate from GitHub onto an Apple Silicon Mac that has never
approved that build. Copy both applications to `/Applications`.

Follow Apple's documented override procedure:
<https://support.apple.com/guide/mac-help/open-an-app-by-overriding-security-settings-mh40617/mac>

- [ ] A normal first launch is blocked because the app is not notarized.
- [ ] System Settings > Privacy & Security shows **Open Anyway** after the
      blocked attempt and within Apple's documented one-hour window.
- [ ] Approving Pop-FE PSP opens it without disabling Gatekeeper.
- [ ] Pop-FE PS3 requires and accepts its own one-time approval.
- [ ] Control-clicking `Install CLI.command` and choosing Open allows the CLI
      installer to run.
- [ ] No instruction or program removes quarantine metadata automatically.

Record the exact Mac model and macOS version in the release notes. Test the
minimum supported macOS 14 release and the current stable macOS release before
declaring the compatibility matrix complete.

## Synthetic parity matrix

The automated integration smoke uses redistributable fixtures and must pass
from a read-only current directory whose path contains spaces and non-ASCII
characters.

- [ ] Inputs: CUE/BIN, CCD/IMG, raw BIN/IMG, ZIP, and CHD.
- [ ] Multidisc processing.
- [ ] PSP/Vita EBOOT.PBP with ATRAC3 SND0.
- [ ] PS2 POPS VCD and artwork.
- [ ] PS3 PKG.
- [ ] PlayStation Classic PBP.
- [ ] PSIO image, CU2, and multidisc list.
- [ ] RetroArch BIN/M3U, CUE/M3U, PBP, and thumbnails.
- [ ] Successful runs leave no `cli-*` cache workspace behind.

## Focused option checks

Use only synthetic or personally owned media. Record the input type and output
hash where practical.

- [ ] Single-disc and multidisc outputs.
- [ ] CDDA to ATRAC3 and PSP `--psp-use-cdda`.
- [ ] LibCrypt patching and `--no-libcrypt`.
- [ ] `--psx-undither`.
- [ ] PPF and Xdelta ROM hacks.
- [ ] Local artwork, theme, watermark, and logo options.
- [ ] PDF, ZIP, and image-directory manuals.
- [ ] Optional YouTube SND0 path on a network-enabled test host.
- [ ] Helper failure and network failure report actionable errors.
- [ ] Failed conversion retains its work directory and successful conversion
      removes it.

CBR/RAR manual extraction retains the existing optional external UNRAR
requirement and is not a self-contained macOS test.

## Real-device checks

- [ ] PSP memory stick discovered below `/Volumes` and EBOOT launches.
- [ ] Vita `pspemu` volume discovered and EBOOT launches through Adrenaline.
- [ ] PS3 installs and launches the generated PKG.
- [ ] PS2 POPS USB layout works on hardware.
- [ ] PSIO SD layout works on hardware.
- [ ] PlayStation Classic AutoBleem volume is discovered and launches the PBP.

Unavailable hardware must be reported as **not tested**, never as passed.
