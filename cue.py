#!/usr/bin/env python
# coding: utf-8
#
# A utility to automate building PSP Document files
# Based on PSP Docmaker GUI by takedown psp.in.th

import argparse
import io
import glob
import os
import struct

verbose = False

SECTLEN = 2352

def fixup_cue(cue, raw=False, psxtruncate=False):
    file = None
    filesize = None
    _t = -1
    _i = -1

    for track in range(1, len(cue['TRACKS']) +1):
        if file != cue['TRACKS'][track]['FILE']:
            file = cue['TRACKS'][track]['FILE']
            _t = -1
            _i = -1
        filesize = os.stat(file).st_size

        for idx in cue['TRACKS'][track]['INDEX']:
            cue['TRACKS'][track]['INDEX'][idx]['STOPSECT'] = int(filesize / SECTLEN)
            if _t >=0 and _i >= 0:
                cue['TRACKS'][_t]['INDEX'][_i]['STOPSECT'] = cue['TRACKS'][track]['INDEX'][idx]['STARTSECT']
            
            _t = track
            _i = idx

            mode = cue['TRACKS'][track]['MODE']
            if mode == 'MODE1/2352':
                cue['TRACKS'][track]['BSTART'] = 16
                cue['TRACKS'][track]['BSIZE'] = 2048
            if mode == 'MODE2/2352':
                cue['TRACKS'][track]['BSTART'] = 24
                cue['TRACKS'][track]['BSIZE'] = 2048
                if raw:
                    cue['TRACKS'][track]['BSTART'] = 0
                    cue['TRACKS'][track]['BSIZE'] = 2352
                if psxtruncate:
                    cue['TRACKS'][track]['BSIZE'] = 2336
            if mode == 'MODE2/2336':
                cue['TRACKS'][track]['BSTART'] = 16
                cue['TRACKS'][track]['BSIZE'] = 2336
            if mode == 'AUDIO':
                cue['TRACKS'][track]['BSTART'] = 0
                cue['TRACKS'][track]['BSIZE'] = 2352

                
def parse_cue(cuefile, raw=False, psxtruncate=False):

    def strip_line(line):
        # strip leading/trailing whitespace and ignore blank lines
        while line and line[0] and line[0] in [' ', '\t', '\r', '\n', '"']:
            line = line[1:]
        while line and line[-1] and line[-1] in [' ', '\t', '\r', '\n', '"']:
            line = line[:-1]
        return line
    
    section = None
    cue = {}
    file = None
    filesize = 0
    cue['TRACKS'] = {}
    track = None
    with open(cuefile, 'r') as f:
        for line in f.readlines():
            line = strip_line(line)
            if not line:
                continue

            if line.upper()[:5] == 'FILE ':
                file = strip_line(line[5:line.rindex(' ')])
                if file[0] != '/' and cuefile.rindex('/') >= 0:
                    file = cuefile[:cuefile.rindex('/') + 1] + file
                    
            if line.upper()[:6] == 'TRACK ':
                track = int(strip_line(line[6:line.rindex(' ')]))
                mode = strip_line(line[line.rindex(' '):]).upper()
                cue['TRACKS'][track] = {}
                cue['TRACKS'][track]['MODE'] = mode
                cue['TRACKS'][track]['FILE'] = file
                cue['TRACKS'][track]['INDEX'] = {}

            if line.upper()[:6] == 'INDEX ':
                idx = int(strip_line(line[6:line.rindex(' ')]))
                min, sec, frame = strip_line(line[line.rindex(' '):]).split(':')
                min = int(min)
                sec = int(sec)
                frame = int(frame)

                sector = 75 * ( int(min) * 60 + int(sec) ) + int(frame)
                if idx == 1 and cue['TRACKS'][track]['MODE'] == 'AUDIO' and len(cue['TRACKS'][track]['INDEX']) == 0:
                    cue['TRACKS'][track]['INDEX'][0] = {}
                    cue['TRACKS'][track]['INDEX'][0]['STARTSECT'] = sector - 150
                cue['TRACKS'][track]['INDEX'][idx] = {}
                cue['TRACKS'][track]['INDEX'][idx]['STARTSECT'] = sector

                if idx > 1:
                    raise Exception('Can not handle TRACK INDEX > 1 yet')
                
    fixup_cue(cue, raw=raw, psxtruncate=psxtruncate)
    
    return cue

def write_cue(cue, file):
    with open(file, 'w') as o:
        file = None
        _t = -1
        _i = -1

        for track in range(1, len(cue['TRACKS']) +1):
            if file != cue['TRACKS'][track]['FILE']:
                file = cue['TRACKS'][track]['FILE']
                _t = -1
                _i = -1
                o.write("FILE \"%s\" BINARY\n" % file)
            o.write("  TRACK %d %s\n" % (track, cue['TRACKS'][track]['MODE']))
            if cue['TRACKS'][track]['MODE'] == 'AUDIO' and 0 not in cue['TRACKS'][track]['INDEX']:
                # add preamble
                sector = cue['TRACKS'][track]['INDEX'][idx]['STARTSECT'] - 150
                frames = int(sector % 75)
                sector = sector - frames
                secs = int((sector / 75) % 60)
                sector = sector - secs * 75
                mins = int(sector / 75 / 60)
                o.write("    INDEX 00 %02d:%02d:%02d\n" % (mins, secs, frames))
            for idx in cue['TRACKS'][track]['INDEX']:
                sector = cue['TRACKS'][track]['INDEX'][idx]['STARTSECT']
                frames = int(sector % 75)
                sector = sector - frames
                secs = int((sector / 75) % 60)
                sector = sector - secs * 75
                mins = int(sector / 75 / 60)
                o.write("    INDEX %02d %02d:%02d:%02d\n" % (idx, mins, secs, frames))

        
def parse_ccd(ccdfile):
    f = open(ccdfile, 'r')

    section = None
    ccd = {}
    ccd['FILE'] = os.path.abspath(ccdfile)[:-4] + '.img'

    for line in f.readlines():
        # strip leading/trailing whitespace and ignore blank lines
        while line and line[0] and line[0] in [' ', '\t', '\r', '\n']:
            line = line[1:]
        while line and line[-1] and line[-1] in [' ', '\t', '\r', '\n']:
            line = line[:-1]
        if not line:
            continue

        if line[0] == '[':
            section = line[1:-1]
            ccd[section] = {}
            continue

        # Read individual entries, we must be in a section by now
        if not section:
            print('ERROR: key=value outside of section')
            return None
        
        kv = line.split('=')
        try:
            ccd[section][kv[0]] = int(kv[1], base=16) if kv[1][:2] == '0x' else int(kv[1])
        except:
            ccd[section][kv[0]] = kv[1]

    # Fixup the TRACKS
    ccd['TRACKS'] = {}
    _r = []
    for k in ccd:
        if k[:6].upper() == 'TRACK ':
            idx = int(k[6:])
            ccd['TRACKS'][idx] = ccd[k]
            _r.append(k)
    for i in _r:
        del ccd[i]
    _r = []
    for track in ccd['TRACKS']:
        ccd['TRACKS'][track]['INDEX'] = {}
        for k in ccd['TRACKS'][track]:
            if k[:6].upper() == 'INDEX ':
                idx = int(k[6:])
                ccd['TRACKS'][track]['INDEX'][idx] = ccd['TRACKS'][track][k]
                _r.append((track,k))
    for i in _r:
        del ccd['TRACKS'][i[0]][i[1]]
        
    # Fixup the ENTRIES
    ccd['ENTRIES'] = {}
    _r = []
    for k in ccd:
        if k[:6].upper() == 'ENTRY ':
            idx = int(k[6:])
            ccd['ENTRIES'][idx] = ccd[k]
            _r.append(k)
    for i in _r:
        del ccd[i]
        
    return ccd


def ccd2cue(ccd):
    cue = {}

    if 'CATALOG' in ccd:
        cue['CATALOG'] = ccd['CATALOG']

    cue['TRACKS'] = {}
    for track in ccd['TRACKS']:
        cue['TRACKS'][track] = {}
        cue['TRACKS'][track]['FILE'] = ccd['FILE']
        if ccd['TRACKS'][track]['MODE'] == 0:
            cue['TRACKS'][track]['MODE'] = 'AUDIO'
        if ccd['TRACKS'][track]['MODE'] == 1:
            cue['TRACKS'][track]['MODE'] = 'MODE1/2352'
        if ccd['TRACKS'][track]['MODE'] == 2:
            cue['TRACKS'][track]['MODE'] = 'MODE2/2352'
        if 'MODE' not in cue['TRACKS'][track]:
            raise Exception('Can not handle MODE %d yet' % ccd['TRACKS'][track]['MODE'])

        if 'FLAGS' in ccd['TRACKS'][track]:
            cue['TRACKS'][track]['FLAGS'] = ccd['TRACKS'][track]['FLAGS']
            
        if 'ISRC' in ccd['TRACKS'][track]:
            cue['TRACKS'][track]['ISRC'] = ccd['TRACKS'][track]['ISRC']

        cue['TRACKS'][track]['INDEX'] = {}
        for idx in ccd['TRACKS'][track]['INDEX']:
            cue['TRACKS'][track]['INDEX'][idx] = {}
            cue['TRACKS'][track]['INDEX'][idx]['STARTSECT'] = ccd['TRACKS'][track]['INDEX'][idx]
            
        #print(track, cue['TRACKS'][track])

    fixup_cue(cue)
    return cue


#CUE {
# CUE
#  'TRACKS': {1: {'MODE': 'MODE2/2352', 'FILE': 'tmp/PSX ...',
#                 'INDEX': {1: {'STARTSECT': 0, 'STOPSECT': 127658}},
#                 'BSTART': 24, 'BSIZE': 2048},
#             2: {'MODE': 'AUDIO', 'FILE': 'tmp/PSX ...',
#                 'INDEX': {0: {'STARTSECT': 127658, 'STOPSECT': 127808},
#                           1: {'STARTSECT': 127808, 'STOPSECT': 139329}},
#                 'BSTART': 0, 'BSIZE': 2352},
#
# CCD
# 'FILE': 'tmp/PSX ...',
# 'CloneCD': {'Version': 3},
# 'Disc': {'TocEntries': 21, 'Sessions': 1,
#          'DataTracksScrambled': 0, 'CDTextLength': 0},
# 'Session 1': {'PreGapMode': 2, 'PreGapSubC': 0},
# 'TRACKS': {1: {'MODE': 2, 'INDEX': {1: 0}},
#            2: {'MODE': 0, 'INDEX': {1: 127808}},
#            3: {'MODE': 0, 'INDEX': {1: 139479}},
#            ...
# 'ENTRIES': {0: {'Session': 1, 'Point': 160, 'ADR': 1, 'Control': 4,
#                 'TrackNo': 0, 'AMin': 0, 'ASec': 0, 'AFrame': 0,
#                 'ALBA': -150, 'Zero': 0, 'PMin': 1, 'PSec': 32,
#                 'PFrame': 0, 'PLBA': 6750},
#             1: {'Session': 1, 'Point': 161, 'ADR': 1, 'Control': 0,
#                 'TrackNo': 0, 'AMin': 0, 'ASec': 0, 'AFrame': 0,
#                 'ALBA': -150, 'Zero': 0, 'PMin': 18, 'PSec': 0,
#                 'PFrame': 0, 'PLBA': 80850},
#             ...
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help='Verbose')
    parser.add_argument('ccd', help='CCD file')
    parser.add_argument('cue', help='CUE file')
    args = parser.parse_args()

    if args.v:
        verbose = True

    ccd = parse_ccd(args.ccd)
    cue = ccd2cue(ccd)
    write_cue(cue, args.cue)
    print('Wrote', args.cue)
    
