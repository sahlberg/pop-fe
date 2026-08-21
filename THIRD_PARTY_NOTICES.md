# Third-party software bundled with POP-FE

The macOS distribution contains separate helper executables built from the
sources below.  Exact source revisions, archive checksums, and output names are
recorded in `packaging/macos/dependencies.lock.json`.  The corresponding build
instructions are in `packaging/macos/build-helpers.sh`.

| Component | Purpose | License | Source |
| --- | --- | --- | --- |
| FFmpeg | Audio and media conversion | LGPL-2.1-or-later | <https://ffmpeg.org/> |
| libsndfile | Statically linked ATRACDENC audio input library | LGPL-2.1-or-later | <https://github.com/libsndfile/libsndfile> |
| ATRACDENC | ATRAC audio encoding | LGPL-2.1-or-later | <https://github.com/dcherednik/atracdenc> |
| Xdelta3 | Binary patch application | Apache-2.0 | <https://github.com/jmacd/xdelta> |
| MAME CHDMan | CHD image conversion | GPL-2.0-only | <https://github.com/mamedev/mame> |
| LibCrypt Patcher | PlayStation LibCrypt patching | BSD-3-Clause | <https://github.com/alex-free/libcrypt-patcher> |
| lib-enigma | LibCrypt Patcher support library | BSD-3-Clause | <https://github.com/alex-free/lib-enigma> |
| PSX-Undither | PlayStation image patching | GPL-2.0-only | <https://github.com/alex-free/psx-undither> |
| lib-ps-cd-id | PSX-Undither support library | GPL-2.0-only | <https://github.com/alex-free/lib-ps-cd-id> |
| Cue2cu2 | PSIO CU2 generation | Apache-2.0 | <https://github.com/NRGDEAD/Cue2cu2> |
| binmerge | Multi-track BIN merging | GPL-2.0-or-later | <https://github.com/putnam/binmerge> |
| PSL1GHT ps3py | PS3 package generation | MIT | <https://github.com/ps3dev/PSL1GHT> |
| ECDSA | Signing support used by `sign3` | MIT | <https://github.com/tlsfuzzer/python-ecdsa> |

## Python application and runtime components

Python package versions are pinned in `packaging/macos/requirements-*.txt`.
The build copies the license and notice files published in each installed
wheel into the `licenses/` directory of the applications and disk image.

| Component | Version | License | Source |
| --- | --- | --- | --- |
| CPython | 3.12.13 | PSF-2.0 | <https://www.python.org/downloads/release/python-31213/> |
| Tcl/Tk | 8.6.18 | TCL license | <https://www.tcl-lang.org/software/tcltk/8.6.html> |
| PyInstaller | 6.22.2 | GPL-2.0-or-later with bootloader exception | <https://pyinstaller.org/> |
| PyInstaller hooks contrib | 2026.6 | Apache-2.0 and GPL-2.0-only | <https://github.com/pyinstaller/pyinstaller-hooks-contrib> |
| Pillow | 12.3.0 | MIT-CMU | <https://python-pillow.org/> |
| PyPDF2 | 3.0.1 | BSD-3-Clause | <https://github.com/py-pdf/PyPDF2> |
| OpenCV contrib Python | 5.0.0.93 | Apache-2.0 and bundled third-party licenses | <https://github.com/opencv/opencv-python> |
| NumPy | 2.5.2 | BSD-3-Clause and bundled third-party licenses | <https://numpy.org/> |
| pycdlib | 1.20.0 | LGPL-2.1-only | <https://github.com/clalancette/pycdlib> |
| PyCryptodome | 3.23.0 | BSD-2-Clause and public domain | <https://github.com/Legrandin/pycryptodome> |
| pygubu | 0.41.2 | MIT | <https://github.com/alejandroautalan/pygubu> |
| pytubefix | 10.11.0 | MIT | <https://github.com/JuanBindez/pytubefix> |
| Node.js wheel and Node.js | 24.19.0 | MIT and bundled third-party licenses | <https://github.com/njzjz/nodejs-wheel> |
| rarfile | 4.5 | ISC | <https://github.com/markokr/rarfile> |
| Requests | 2.34.2 | Apache-2.0 | <https://requests.readthedocs.io/> |
| tkinterdnd2 / TkDND | 0.6.2 | MIT | <https://github.com/Eliav2/tkinterdnd2> |
| aiohappyeyeballs | 2.7.1 | PSF-2.0 | <https://github.com/aio-libs/aiohappyeyeballs> |
| aiohttp | 3.14.3 | Apache-2.0 and MIT | <https://github.com/aio-libs/aiohttp> |
| aiosignal | 1.4.0 | Apache-2.0 | <https://github.com/aio-libs/aiosignal> |
| attrs | 26.1.0 | MIT | <https://github.com/python-attrs/attrs> |
| certifi | 2026.7.22 | MPL-2.0 | <https://github.com/certifi/python-certifi> |
| charset-normalizer | 3.5.1 | MIT | <https://github.com/jawah/charset_normalizer> |
| frozenlist | 1.8.0 | Apache-2.0 | <https://github.com/aio-libs/frozenlist> |
| idna | 3.19 | BSD-3-Clause | <https://github.com/kjd/idna> |
| multidict | 6.7.1 | Apache-2.0 | <https://github.com/aio-libs/multidict> |
| packaging | 26.3 | Apache-2.0 or BSD-2-Clause | <https://github.com/pypa/packaging> |
| propcache | 0.5.2 | Apache-2.0 | <https://github.com/aio-libs/propcache> |
| six | 1.17.0 | MIT | <https://github.com/benjaminp/six> |
| typing_extensions | 4.16.0 | PSF-2.0 | <https://github.com/python/typing_extensions> |
| urllib3 | 2.7.0 | MIT | <https://github.com/urllib3/urllib3> |
| yarl | 1.24.5 | Apache-2.0 | <https://github.com/aio-libs/yarl> |

Build-only packages such as PyYAML, altgraph, and macholib are also pinned,
and their license files are retained by the same collection step.

POP-FE itself is distributed under the GNU Lesser General Public License 2.1.
License texts and copyright notices exposed by the pinned Python distributions
are collected into the release at build time. The exact corresponding source
code can be obtained from the URLs above and the immutable revisions in the
dependency lock file.
