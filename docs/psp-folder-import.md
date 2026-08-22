# PSP folder import

## Scope

Improve the shared PSP GUI without changing the manual file workflow. The
window remains a single, resizable view. Folder import works on macOS, Windows,
and Linux.

## Layout

The left column contains:

- game files;
- metadata and local assets;
- output directory.

The right column contains the main preview, the ICON0/PIC0/PIC1 thumbnails,
and the PIC0 placement controls. Advanced options and the action buttons stay
at the bottom.

Only loaded disc rows are shown. `Add disc...` keeps manual selection
available. `Import folder...` starts automatic discovery. `Import all discs`
is enabled by default.

## Folder scan

The scanner reads only files directly below the selected directory. It ignores
hidden files, subdirectories, and existing EBOOT output.

Supported disc inputs are CUE, CCD, CHD, ZIP, IMG, and raw BIN. A BIN referenced
by a CUE is not returned as a separate disc. Results use natural filename order.
With multi-disc import disabled, only the first result is used. At most five
discs are loaded.

The controller reads the game ID from the first disc. The database title takes
priority; a cleaned folder name is the fallback.

## Asset precedence

Names are matched without case sensitivity. Local files are checked first:

- `ICON0.PNG`;
- `PIC0.PNG`;
- `PIC1.PNG`;
- `SND0.AT3` or a supported WAV file;
- `MANUAL.PDF`, `MANUAL.ZIP`, or `MANUAL.CBR`;
- `LOGO.PNG`.

Local files are never overwritten. Existing theme, database, and online lookup
fills each missing field. `BOOT.PNG` and `ICON1.PMF` are ignored because the PSP
GUI has no matching inputs.

## Code boundaries

A standalone scanner returns a result containing disc paths, local assets,
warnings, and the fallback title. It does not access the network or Tk.

The PSP controller applies that result, extracts disc metadata through the
existing backend, and requests only missing assets. Manual file selection and
folder import share the same disc-loading method.

## Errors

- An empty or invalid folder leaves the current form unchanged.
- More than five discs loads the first five and adds a warning.
- An unreadable disc is reported and no final output is created.
- Missing optional online assets do not block conversion.
- Ambiguous local assets use the exact standard name first and add a warning.

The GUI shows one short import summary instead of one dialog per file.

## Tests

Unit tests cover CUE/BIN deduplication, natural ordering, the five-disc limit,
single-disc mode, case-insensitive assets, ignored subdirectories, local
precedence, and invalid folders. Controller tests cover field population and
unchanged state on failure. The existing unit suite, GUI smoke test, conversion
matrix, Mach-O checks, and mounted-DMG smoke test remain required.
