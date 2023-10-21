#!/usr/bin/env python
# coding: utf-8
#
import argparse
import io
import os
import shutil
import struct
import sys

PSP_OFFSET = 0x20
PSAR_OFFSET = 0x24


def getpsisoimgoffset(eboot):
    with open(eboot, 'rb') as f:
        # read header
        buf = f.read(0x28)
        header = {}
        header['magic'] = buf[0:4]
        if header['magic'] != b'\x00PBP':
            raise Exception('Not a PBP file')
        header['unknown'] = struct.unpack_from('<I', buf, 4)[0]
        header['sfo'] = struct.unpack_from('<I', buf, 8)[0]
        header['icon0'] = struct.unpack_from('<I', buf, 12)[0]
        header['icon1'] = struct.unpack_from('<I', buf, 16)[0]
        header['pic0'] = struct.unpack_from('<I', buf, 20)[0]
        header['pic1'] = struct.unpack_from('<I', buf, 24)[0]
        header['snd0'] = struct.unpack_from('<I', buf, 28)[0]
        header['datapsp'] = struct.unpack_from('<I', buf, PSP_OFFSET)[0]
        header['datapsar'] = struct.unpack_from('<I', buf, PSAR_OFFSET)[0]

        offset = header['datapsar']
        
        #print('PSAR starting at 0x%04x' % offset)
        f.seek(offset)
        buf = f.read(0x16)
        if buf[:10] == b'PSTITLEIMG':
            f.seek(offset + 0x200)
            buf = f.read(4)
            offset = header['datapsar'] + struct.unpack_from('<I', buf, 0)[0]
            #print('PSISOIMG at 0x%04x' % offset)
                
        f.seek(offset)
        buf = f.read(0x16)
        if buf[:8] == b'PSISOIMG':
            return offset

def getaudiotracktable(eboot):
    offset = getpsisoimgoffset(eboot)
    with open(eboot, 'rb') as f:
        f.seek(offset + 0xc00)
        return f.read(0x620)

def gettoc(eboot):
    offset = getpsisoimgoffset(eboot)
    with open(eboot, 'rb') as f:
        f.seek(offset + 0x800)
        return f.read(1020)

def injecttoc(eboot, toc):
    offset = getpsisoimgoffset(eboot)
    with open(eboot, 'rb+') as f:
        f.seek(offset + 0x800)
        f.write(toc)
    
def printhex(name, buf):
    print(name)
    idx = 0
    for c in buf:
        if idx % 16 == 0:
            if idx != 0:
                print('')
            print('%04x  ' % idx, end='')
        print('%02x ' % c, end='')
        if idx % 16 == 7:
            print(' ', end='')
        idx = idx + 1
    print('')

def getdiscmaptableoffset(eboot):
    offset = getpsisoimgoffset(eboot)
    return offset + 0x4000

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help='Verbose')
    parser.add_argument('--game-id',
                        help='GameId to inject.')
    parser.add_argument('--config',
                        help='Config to inject')
    parser.add_argument('--eboot', help='Output EBOOT')
    parser.add_argument('--good-eboot', help='Good EBOOT')
    parser.add_argument('--bad-eboot', help='Bad EBOOT')
    args = parser.parse_args()

    if not args.eboot:
        print('Must specify --eboot')
        os._exit(1)


    print('Copy BAD eboot to test EBOOT')
    shutil.copyfile(args.bad_eboot, args.eboot)
    
    good_offset = getpsisoimgoffset(args.good_eboot)
    print('GOOD EBOOT PSISOIMG starts at %08x' % good_offset)
    bad_offset = getpsisoimgoffset(args.bad_eboot)
    print('BAD  EBOOT PSISOIMG starts at %08x' % bad_offset)

    good_att = getaudiotracktable(args.good_eboot)
    #printhex('GOOD ATT', good_att)
    bad_att = getaudiotracktable(args.bad_eboot)
    #printhex('BAD  ATT', bad_att)

    good_toc = gettoc(args.good_eboot)
    #printhex('GOOD TOC', good_toc)
    bad_toc = gettoc(args.bad_eboot)
    #printhex('BAD  TOC', bad_toc)
    
    print('Write GOOD TOC to test eboot')
    injecttoc(args.eboot, good_toc)

    print('Copy all the disc tracks from GOOD test eboot')
    good_dmt_offset = getdiscmaptableoffset(args.good_eboot)
    print('GOOD DMT at %04x' % good_dmt_offset)
    bad_dmt_offset = getdiscmaptableoffset(args.bad_eboot)
    print('BAD  DMT at %04x' % bad_dmt_offset)
    
    with open(args.good_eboot, 'rb') as i:
        i.seek(good_dmt_offset)
        buf = i.read()
        print('amount of disc data', len(buf))
        with open(args.eboot, 'rb+') as o:
            o.seek(bad_dmt_offset)
            #o.write(buf)
