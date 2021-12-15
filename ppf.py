#!/usr/bin/env python
# coding: utf-8
#

import argparse
import os
import struct
import sys


def ApplyPPF2(img, buf):
    f = open(img, 'rb+')
    print('Patchfile is a PPF2.0 patch')
    print('Description:', buf[6:56].decode())
    if buf[-8:-4] == b'.DIZ':
        idlen = struct.unpack_from('<I', buf[-4:], 0)[0]
        print(buf[-(4 + 16 + idlen):-20].decode())
        buf = buf[:-(idlen + 38)]
    f.seek(0, 2)
    if f.tell() != struct.unpack_from('<I', buf[56:60], 0)[0]:
        raise Exception('Size of image file is not correct. Can not apply PPF')
    f.seek(0x9320)
    if buf[60:60 + 1024] != f.read(1024):
        raise Exception('Patch-validation failed. Can not apply PPF')

    buf = buf[1084:]
    while buf:
        pos = struct.unpack_from('<I', buf[:4], 0)[0]
        count = struct.unpack_from('<B', buf[4:5], 0)[0]
        f.seek(pos)
        f.write(buf[5:5 + count])
        buf = buf[5 + count:]

# Very incomplete, only enough to apply krHACKen's patches
def ApplyPPF3(img, buf):
    f = open(img, 'rb+')
    print('Patchfile is a PPF3.0 patch')
    method = buf[5]
    if method != 2:
        raise Exception('Can only handle PPF3 Method 2 for now')
    print('Description:', buf[6:56].decode())
    imagetype = buf[56]
    if imagetype != 0:
        raise Exception('Can only handle imagetype 0 for now')
    blockcheck = buf[57]
    undo = buf[58]

    if buf[-6:-4] == b'.DIZ':
        idlen = struct.unpack_from('<I', buf[-2:], 0)[0]
        print(buf[-(2 + 16 + idlen):-20].decode())
        buf = buf[:-(idlen + 38)]
        raise Exception('Can not handle PPF with DIZ data yet')
    
    if blockcheck:
        f.seek(0x9320)
        if buf[60:60 + 1024] != f.read(1024):
            raise Exception('Patch-validation failed. Can not apply PPF')
        buf = buf[1084:]
    else:
        buf = buf[60:]
        
    while buf:
        pos = struct.unpack_from('<Q', buf[:8], 0)[0]
        count = struct.unpack_from('<B', buf[8:9], 0)[0]
        f.seek(pos)
        f.write(buf[9:9 + count])
        buf = buf[9 + count:]
        if undo:
            buf = buf[count:]

        
def ApplyPPF(img, ppf):
    with open(ppf, 'rb') as f:
        p = f.read()
        if p[:4] == b'PPF1':
            raise Exception('PPF1 not yet implemented')
        if p[:4] == b'PPF2':
            return ApplyPPF2(img, p)
        if p[:4] == b'PPF3':
            return ApplyPPF3(img, p)
        raise Exception('Not a PPF file')

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('image', nargs=1, help='Image file')
    parser.add_argument('ppf', nargs=1, help='Patch file')
    args = parser.parse_args()
    
    ApplyPPF(args.image[0], args.ppf[0])
    
