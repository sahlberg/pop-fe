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

POP-FE itself is distributed under the GNU Lesser General Public License 2.1.
Complete license texts and copyright notices from dependencies are retained in
the source tree and are copied into the macOS disk image by the release build.
The exact corresponding source code can be obtained from the URLs and immutable
revisions in the dependency lock file.
