#!/usr/bin/env python
# coding: utf-8
#
# Utility to convert between signed VMP files and raw memory card dumps
#
# Based on the algorithm in
# https://github.com/dots-tb/vita-mcr2vmp
#
import argparse
import hashlib
import os
import struct
from Crypto.Cipher import AES

def dump_vmp(f):
    if os.stat(f).st_size != 131200:
        print('Not a VMP file. Skipping')
        return

    with open(f, 'rb') as i:
        i.seek(0x80)
        buf = i.read(131072)
        with open(f[:-3] + 'mcr', 'wb') as o:
            o.write(buf)
            print('Dumped MCR as', f[:-3] + 'mcr')


def create_vmp(f):
    SEED_OFFSET = 0xc
    key = bytes([0xAB, 0x5A, 0xBC, 0x9F, 0xC1, 0xF4, 0x9D, 0xE6,
                 0xA0, 0x51, 0xDB, 0xAE, 0xFA, 0x51, 0x88, 0x59])
    iv = bytes([0xB3, 0x0F, 0xFE, 0xED, 0xB7, 0xDC, 0x5E, 0xB7,
                0x13, 0x3D, 0xA6, 0x0D, 0x1B, 0x6B, 0x2C, 0xDC])

    if os.stat(f).st_size != 131072:
        print('Not a raw memory card file. Skipping')
        return
    
    with open(f, 'rb') as input_file:
        buf = bytearray(0x80) + input_file.read(131072)
        struct.pack_into('<I', buf, 0, 0x564D5000)
        struct.pack_into('<I', buf, 4, 0x80)

        salt_seed = buf[0x0c:0x0c + 0x14]
        
        workbuf = bytearray(0x14)
        workbuf[:0x10] = salt_seed[:0x10]
        obj = AES.new(key, AES.MODE_ECB)
        workbuf = bytearray(obj.decrypt(bytes(workbuf[:0x10])))

        salt = bytearray(0x40)
        salt[:0x10] = workbuf[:0x10]

        workbuf[:0x10] = salt_seed[:0x10]
        workbuf = obj.encrypt(bytes(workbuf[:0x10]))
        salt[0x10:0x20] = workbuf[:0x10]
        for i in range(0x10):
            salt[i] = salt[i] ^ iv[i]

        workbuf = bytearray(b'\xff' * 0x14)
        workbuf[:4] = salt_seed[0x10:0x14]
        for i in range(0x10):
            salt[0x10 + i] = salt[0x10 + i] ^ workbuf[i]

        salt[0x14:0x20] = bytes(12)
        for i in range(0x40):
            salt[i] = salt[i] ^ 0x36

        h = hashlib.sha1()
        h.update(salt)
        buf[0x20:0x34] = bytes(b'\x00' * 0x14)
        h.update(buf)
        workbuf = h.digest()

        h = hashlib.sha1()
        for i in range(0x40):
            salt[i] = salt[i] ^ 0x6a
        h.update(salt)
        h.update(workbuf)
        workbuf = h.digest()
        buf[0x20:0x34] = workbuf

        with open(f[:-4] + '.VMP', 'wb') as output_file:
            output_file.write(buf)

            
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('command', nargs=1, 
                        help='create|dump')
    parser.add_argument('files', nargs='*', help='Memory card images')
    args = parser.parse_args()

    if args.command[0] == 'dump':
        for f in args.files:
            dump_vmp(f)
            
    if args.command[0] == 'create':
        for f in args.files:
            create_vmp(f)
        
    
