#!/usr/bin/env python
# coding: utf-8
#
import argparse
import os
import re
import struct
import sys


class bchunk(object):
    SECTLEN         = 2352
    WAV_FORMAT_HLEN = 24
    WAV_DATA_HLEN   = 8
    
    def get_file_name(self, line):
        # strip off leading 'FILE '
        pos = line.lower().index('file ')
        line = line[pos + 5:]
        # strip off leading 'FILE '
        pos = line.lower().index(' binary')
        line = line[:pos+1]
        #strip off leading ' '
        while line[0] == ' ':
            line = line[1:]
        #strip off trailing ' '
        while line[-1] == ' ':
            line = line[:-1]
        # remove double quotes
        if line[0] == '"':
            line = line[1:-1]
        # remove single quotes
        if line[0] == '\'':
            line = line[1:-1]
        return line

    def get_mode(self, track, line):
        if line.lower().find('mode1/2352') >= 0:
            track['extension'] = 'iso'
            track['bstart'] = 16
            track['bsize'] = 2048
            return track
        if line.lower().find('mode2/2352') >= 0:
            track['extension'] = 'iso'
            if self.raw:
                track['bstart'] = 0
                track['bsize'] = 2352
                return track
            if self.psxtruncate:
                track['bstart'] = 0
                track['bsize'] = 2336
                return track
            track['bstart'] = 24
            track['bsize'] = 2048
            return track
        if line.lower().find('mode2/2336') >= 0:
            track['extension'] = 'iso'
            track['bstart'] = 16
            track['bsize'] = 2336
            return track
        if line.lower().find('audio') >= 0:
            track['bstart'] = 0
            track['bsize'] = 2352
            track['audio'] = True
            if self.towav:
                track['extension'] = 'wav'
            else:
                track['extension'] = 'cdr'
            return track
        raise Exception('Can not handle this mode yet, check bchunk docs')

    def parse_cue(self, cue):
        print('Cue:', cue)
        with open(cue, 'r') as c:
            lines = c.readlines()
            tracks = []

            for line in lines:
                # FILE
                if re.search('^\s*FILE', line):
                    f = self.get_file_name(line)
                    s = cue.split('/')
                    if len(s) > 1:
                        f = '/'.join(s[:-1]) + '/' + f
                    if self._file:
                        if len(tracks) >= 1:
                            tracks[-1]['stop'] = os.stat(tracks[-1]['bin']).st_size
                            tracks[-1]['stopsect'] = int(tracks[-1]['stop'] / self.SECTLEN)
                        
                    self._file = f
                    continue
                # TRACK
                pos = line.lower().find('track ')
                if pos >= 0:
                    track = {'audio': False, 'bsize': -1, 'bstart': -1,
                             'startsect': -1, 'stopsect': -1,
                             'bin': self._file}
                    line = line[pos + 6:]
                    while line[0] == ' ':
                        line = line[1:]
                    pos = line.index(' ')
                    track['num'] = int(line[:pos])
                    line = line[pos:]
                    while line[0] == ' ':
                        line = line[1:]
                    track = self.get_mode(track, line)
                    tracks.append(track)
                # INDEX
                pos = line.lower().find('index ')
                if pos >= 0:
                    line = line[pos + 6:]
                    while line[0] == ' ':
                        line = line[1:]
                    pos = line.index(' ')
                    line = line[pos:]
                    while line[0] == ' ':
                        line = line[1:]
                    mins, secs, frames = line.split(':')

                    tracks[-1]['startsect'] = 75 * ( int(mins) * 60 + int(secs) ) + int(frames)
                    tracks[-1]['start'] = int(tracks[-1]['startsect'] * self.SECTLEN)
                    if len(tracks) > 1:
                        if tracks[-2]['stopsect'] < 0:
                            tracks[-2]['stopsect'] = tracks[-1]['startsect']
                            tracks[-2]['stop'] = tracks[-1]['start'] - 1
        if len(tracks) >= 1:
            tracks[-1]['stop'] = os.stat(tracks[-1]['bin']).st_size
            tracks[-1]['stopsect'] = int(tracks[-1]['stop'] / self.SECTLEN)
        self.tracks = tracks
        
    def writetrack(self, idx, fn):
        t = self.tracks[idx]
        fn = fn + "%02d" % t['num'] + '.' + t['extension']
        print('Read bin', idx, self.tracks[idx]['bin'])
        with open(self.tracks[idx]['bin'], "rb") as i:
            i.seek(t['start'])
            with open(fn, "wb") as o:
                print('Write track', fn)
                reallen = int((t['stopsect'] - t['startsect'] + 1) * t['bsize'])

                if t['audio'] and self.towav:
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

                sect = t['startsect']
                while sect <= t['stopsect']:
                    buf = i.read(self.SECTLEN)
                    if len(buf) == 0:
                        break
                    if t['audio']:
                        if self.swapaudio:
                            for pos in range(t['bstart'], t['bstart'] + t['bsize'], 2):
                                buf[pos:pos+2] = struct.pack('>H', struct.unpack('<H', buf[pos:pos+2])[0])

                    o.write(buf[t['bstart']:t['bstart'] + t['bsize']])
                    sect = sect + 1
        
    def __init__(self):
        self._file = None
        self._raw = False
        self._psxtruncate = False
        self._towav = False
        self._swapaudio = False
        
    def open(self, cue):
        self.parse_cue(cue)

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
    bc.raw = args.r
    bc.psxtruncate = args.p
    bc.towav = args.w
    bc.swapaudio = args.s
    bc.open(args.image[0])
    for i in range(len(bc.tracks)):
        bc.writetrack(i, args.basename[0])
