#!/usr/bin/env python
# coding: utf-8
#

import argparse
import os
import struct
import sys

from make_isoedat import pack
import sign3

verbose = False

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help='Verbose')
    parser.add_argument('--iso-bin-dat',
                    help='Input ISO.BIN.DAT file to patch')
    parser.add_argument('--config',
                    help='External config to inject')
    parser.add_argument('--output',
                    help='Output file without .BIN extension')
    args = parser.parse_args()

    if args.v:
        verbose = True

    if not args.iso_bin_dat:
        print('/must specify --iso-bin-dat')
        os._exit(1)
    if not args.config:
        print('/must specify --config')
        os._exit(1)
    if not args.output:
        print('/must specify --output')
        os._exit(1)

    ibd = args.output + '.DAT'
    ibe = args.output + '.EDAT'
    with open(args.iso_bin_dat, 'rb') as f:
        f.seek(0x800)
        buf = f.read(11)
        disc_id = str(buf[1:5] + buf[6:11])[2:-1]

        print('Copying', args.iso_bin_dat, 'to', ibd)
        len = os.stat(args.iso_bin_dat).st_size
        with open(ibd, 'wb') as o:
            f.seek(0)
            o.write(f.read(len - 40))

    with open(ibd, 'rb+') as o:
        print('Patching', ibd, disc_id)
        #clear out old config
        o.seek(0x824)
        o.write(bytes(72))
        # write new config
        with open(args.config, 'rb') as c:
            o.seek(0x824)
            o.write(c.read())

            print('Signing', ibd)
            o.seek(0)
            _b = sign3.calc_sign(o.read())
            o.seek(0,2)
            o.write(_b)

    print('Encrypt', ibe)
    pack(ibd, ibe, 'UP9000-%s_00-0000000000000001' % disc_id)
    print('Finished creating', ibe)
