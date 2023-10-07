#!/usr/bin/env python
# coding: utf-8
#
import argparse
import io
import os
import struct
import sys

PSP_OFFSET = 0x20
PSAR_OFFSET = 0x24

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help='Verbose')
    parser.add_argument('--game-id',
                        help='GameId to inject.')
    parser.add_argument('--config',
                        help='Config to inject')
    parser.add_argument('--eboot', help='EBOOT to modify')
    args = parser.parse_args()

    if not args.eboot:
        print('Must specify --eboot')
        os._exit(1)

    with open(args.eboot, 'rb+') as f:
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
        
        print('PSAR starting at 0x%04x' % offset)
        f.seek(offset)
        buf = f.read(0x16)
        if buf[:10] == b'PSTITLEIMG':
            if args.game_id:
                f.seek(offset + 0x264)
                _b = bytes('_' + args.game_id[:4] + '_' + args.game_id[4:], encoding='utf-8')
                f.write(_b)
                print('Injected new GameId in PSTITLEIMG as', _b)

                f.seek(offset + 0x200)
                buf = f.read(4)
                offset = header['datapsar'] + struct.unpack_from('<I', buf, 0)[0]
                print('PSISOIMG at 0x%04x' % offset)

        f.seek(offset)
        buf = f.read(0x16)
        if buf[:8] == b'PSISOIMG':
            if args.game_id:
                f.seek(offset + 0x400)
                _b = bytes('_' + args.game_id[:4] + '_' + args.game_id[4:], encoding='utf-8')
                f.write(_b)
                print('Injected new GameId in PSISOIMG as', _b)

        print('Clearing old config')
        _b = bytes(72)
        f.seek(offset + 0x424)
        f.write(_b)
        if args.config:
            with open(args.config, 'rb') as c:
                print('Writing new config')
                f.seek(offset + 0x424)
                f.write(c.read())

        
