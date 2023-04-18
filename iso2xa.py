#!/usr/bin/env python
# coding: utf-8
#
# Takes an iso image and converts it to a CD-ROM XA mode 2 form-1 bin/cue
# for PSX
#
# PSX tracks are MODE2/2352, or more sppecifically
# CD-ROM XA mode 2 form-1
# https://github.com/libyal/libodraw/blob/main/documentation/Optical%20disc%20RAW%20format.asciidoc
#
#
# Does not Generates ErrorDetectionCode  CRC-32 by default.
# Use --edc to generate it but beware it is super slow.


import argparse
import crc
import os
import re
import struct
import sys

verbose = False
sync = bytes([0x00, 0xff, 0xff, 0xff, 0xff, 0xff,
              0xff, 0xff, 0xff, 0xff, 0xff, 0x00])
subheader = bytes([0x00, 0x00, 0x08, 0x00,  0x00, 0x00, 0x08, 0x00])

def bcd(i):
    return int(i % 10) + 16 * (int(i / 10) % 10)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help='Verbose')
    parser.add_argument('--edc', action='store_true', help='Generate ErrorCorrectionCode')
    parser.add_argument('iso', help='Iso image')
    parser.add_argument('basename', help='Name of output file(s)')
    args = parser.parse_args()

    verbose = args.v
    adr = bytearray(4)
    m = 0
    s = 2
    f = 0

    with open(args.iso, 'rb') as i:
        with open(args.basename + '.bin', "wb") as o:
            d = i.read(2048)
            while d:
                # write sync word 
                o.write(sync)
                # write address and mode
                struct.pack_into('<B', adr, 0, bcd(m))
                struct.pack_into('<B', adr, 1, bcd(s))
                struct.pack_into('<B', adr, 2, bcd(f))
                struct.pack_into('<B', adr, 3, 2)
                f = f + 1
                if f > 74:
                    f = 0
                    s = s + 1
                    if s > 59:
                        s = 0
                        m = m + 1
                o.write(adr)
                # write subheader
                o.write(subheader)
                # write data
                o.write(d)
                # write error detection
                buf = bytearray(4)
                if args.edc:
                    config = crc.Configuration(
                        width=32,
                        polynomial=0x8001801b,
                        init_value=0x00,
                        final_xor_value=0x00,
                        reverse_input=True,
                        reverse_output=True,
                    )
                    calculator = crc.Calculator(config, optimized=True)
                    c = calculator.checksum(subheader + d)
                    struct.pack_into('<I', buf, 0, c)
                o.write(buf)
                # write error correction
                o.write(bytes(276))
                d = i.read(2048)
        print('Wrote:', args.basename + '.bin')
    with open(args.basename + '.cue', "w") as o:
        o.write('FILE "' + args.basename + '.bin' + '" BINARY\n')
        o.write('  TRACK 01 MODE2/2352\n')
        o.write('    INDEX 01 00:00:00\n')
    print('Wrote:', args.basename + '.cue')
