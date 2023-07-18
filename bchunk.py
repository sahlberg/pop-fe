#!/usr/bin/env python
# coding: utf-8
#

import argparse
import os
import re
import struct
import sys

from cue import parse_cue

class bchunk(object):
    SECTLEN         = 2352
    WAV_FORMAT_HLEN = 24
    WAV_DATA_HLEN   = 8
    
    def writetrack(self, idx, fn):
        t = self.tracks[idx]
        print('Read file', idx, self.tracks[idx]['FILE']) if self._verbose else None

        with open(t['FILE'], "rb") as i:
            # Find the last index for this track. Assume this is the
            # data track
            index = None
            for _i in t['INDEX']:
                index = t['INDEX'][_i]

            i.seek(index['STARTSECT'] * self.SECTLEN)
            with open(fn, "wb") as o:
                print('Write track', fn) if self._verbose else None
                reallen = int((index['STOPSECT'] - index['STARTSECT'] + 1) * t['BSIZE'])

                if t['MODE'] == 'AUDIO' and self.towav:
                    buf = bytearray(44)
                    buf[0:4] = bytes('RIFF', encoding='utf-8')
                    struct.pack_into('<I', buf, 4, reallen + self.WAV_DATA_HLEN + self.WAV_FORMAT_HLEN + 4)
                    buf[8:12] = bytes('WAVE', encoding='utf-8')
                    buf[12:16] = bytes('fmt ', encoding='utf-8')
                    struct.pack_into('<I', buf, 16, 0x10)
                    struct.pack_into('<H', buf, 20, 0x01)
                    struct.pack_into('<H', buf, 22, 0x02)
                    struct.pack_into('<I', buf, 24, 44100)
                    struct.pack_into('<I', buf, 28, 44100 * 4)
                    struct.pack_into('<H', buf, 32, 4)
                    struct.pack_into('<H', buf, 34, 2 * 8)
                    buf[36:40] = bytes('data', encoding='utf-8')
                    struct.pack_into('<I', buf, 40, reallen)
                    
                    o.write(buf)

                sect = index['STARTSECT']
                while sect <= index['STOPSECT']:
                    buf = i.read(self.SECTLEN)
                    if len(buf) == 0:
                        break
                    if t['MODE'] == 'AUDIO':
                        if self.swapaudio:
                            for pos in range(t['BSTART'], t['BSTART'] + t['BSIZE'], 2):
                                buf[pos:pos+2] = struct.pack('>H', struct.unpack('<H', buf[pos:pos+2])[0])

                    o.write(buf[t['BSTART']:t['BSTART'] + t['BSIZE']])
                    sect = sect + 1
        
    def __init__(self):
        self._file = None
        self._verbose = False
        self._raw = False
        self._psxtruncate = False
        self._towav = False
        self._swapaudio = False
        
    def open(self, cue):
        print('Cue:', cue) if self._verbose else None
        self.tracks = parse_cue(cue)['TRACKS']

    def bin(self, idx):
        return self.tracks[idx]['bin']

    @property
    def cue(self):
        return self.tracks

    @property
    def raw(self):
        return self._raw

    @raw.setter
    def raw(self, value):
        self._raw = value

    @property
    def verbose(self):
        return self._verbose

    @verbose.setter
    def verbose(self, value):
        self._verbose = value

    @property
    def swapaudio(self):
        return self._swapaudio

    @swapaudio.setter
    def swapaudio(self, value):
        self._swapaudio = value

    @property
    def towav(self):
        return self._towav

    @towav.setter
    def towav(self, value):
        self._towav = value

    @property
    def psxtruncate(self):
        return self._psxtruncate

    @psxtruncate.setter
    def psxtruncate(self, value):
        self._psxtruncate = value
        
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help='Verbose')
    parser.add_argument('-r', action='store_true',
                    help='Raw mode for MODE2/2352: write all 2352 bytes from offset 0 (VCD/MPEG)')
    parser.add_argument('-p', action='store_true',
                    help='PSX mode for MODE2/2352: write 2336 bytes from offset 24.\n(default MODE2/2352 mode writes 2048 bytes from offset 24)')
    parser.add_argument('-w', action='store_true',
                    help='Output audio files in WAV format')
    parser.add_argument('-s', action='store_true',
                    help='swapaudio: swap byte order in audio tracks')
    parser.add_argument('image', nargs=1, help='CUE file for the disk')
    parser.add_argument('basename', nargs=1, help='Name of output file(s)')
    args = parser.parse_args()

    bc = bchunk()
    bc.verbose = args.v
    bc.raw = args.r
    bc.psxtruncate = args.p
    bc.towav = args.w
    bc.swapaudio = args.s
    bc.open(args.image[0])
    for i in bc.tracks:
        fn = args.basename[0] + "%02d" % i + ('.wav' if bc.tracks[i]['MODE'] == 'AUDIO' else '.iso')
        bc.writetrack(i, fn)
