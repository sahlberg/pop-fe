POP-FE for macOS (Apple Silicon)
================================

Requirements
------------

- Apple Silicon Mac (M1 or newer)
- macOS 14 Sonoma or newer
- No Python, Homebrew, Rosetta, or developer tools are required

Install the graphical applications
----------------------------------

Drag Pop-FE PSP.app and Pop-FE PS3.app onto the Applications shortcut in this
window. POP-FE is distributed outside the Mac App Store with an ad-hoc
signature and is not notarized, so macOS will block its first launch.

To approve an application:

1. Try to open it once from Applications, then dismiss the warning.
2. Open System Settings > Privacy & Security.
3. Scroll to Security and click Open Anyway for the POP-FE application.
4. Authenticate if macOS asks, then confirm Open.

Repeat this once for the other POP-FE application. Do not disable Gatekeeper.
Apple notes that Open Anyway is available for about one hour after the blocked
launch attempt:
https://support.apple.com/guide/mac-help/open-an-app-by-overriding-security-settings-mh40617/mac

Install the command-line tool
-----------------------------

Control-click Install CLI.command and choose Open. The default destination is
~/.local/bin/pop-fe and does not require administrator access. You can choose
another directory when prompted, or run ./pop-fe directly from this disk.

If ~/.local/bin is not already on PATH, add this line to ~/.zshrc:

    export PATH="$HOME/.local/bin:$PATH"

Then open a new Terminal window and run:

    pop-fe --help

The single-file CLI may take several seconds to prepare its embedded runtime
when it starts. No files are installed globally and no network access is used
for this preparation.

The bundle handles CUE/BIN, CCD/IMG, BIN/IMG, ZIP, and CHD game images without
external tools. PDF, ZIP, and image-directory manuals are self-contained. CBR
manual extraction has the same optional external UNRAR requirement as the
existing desktop builds.

Data and removal
----------------

Preferences: ~/Library/Application Support/Pop-FE/
Logs:         ~/Library/Logs/Pop-FE/
Work cache:   ~/Library/Caches/Pop-FE/

To uninstall, remove the two applications, ~/.local/bin/pop-fe if installed,
and the three data directories above if you no longer need their contents.

POP-FE never requires writing inside an application bundle or this disk image.
See THIRD_PARTY_NOTICES.md for bundled software and licensing information.
