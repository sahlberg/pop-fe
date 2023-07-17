#!/usr/bin/env python
# coding: utf-8
#
# A utility to automate building PSP Document files
# Based on PSP Docmaker GUI by takedown psp.in.th

try:
    from PIL import Image, ImageDraw, ImageFont
except:
    print('You need to install python module pillow')
import argparse
import io
import glob
import os
import struct
import zipfile

verbose = False


def create_document(source, gameid, maxysize, output):
    def create_header(gameid):
        buf = bytearray(136)
        struct.pack_into('<I', buf, 0, 0x20434F44)
        struct.pack_into('<I', buf, 4, 0x10000)
        struct.pack_into('<I', buf, 8, 0x10000)
        buf[12:21] = bytes(gameid, encoding='utf-8')
        struct.pack_into('<I', buf, 28, 1 if len(docs) <= 100 else 1)
        struct.pack_into('<I', buf, 128, 0xffffffff)
        struct.pack_into('<I', buf, 132, len(docs))
        return buf
    
    def generate_document_entry(f, pos):
        buf = bytearray(128)
        struct.pack_into('<I', buf, 0, pos) # offset low
        struct.pack_into('<I', buf, 12, f.tell()) # size low

        return buf

    def generate_png(pic, maxysize):
        sf = 480 / pic.size[0]
        ns = (480, int(sf * pic.size[1]))
        if ns[1] > maxysize:
            ns = (480, maxysize)
        image = pic.resize(ns, Image.Resampling.BILINEAR)
        f = io.BytesIO()
        image.save(f, 'PNG')
        return f

    docs = []
    imgs = []
    for i in range(100):
        # Look for ...0001...
        g = glob.glob(source + '/*' + f'{i:04d}' + '*')
        if not g: # try a subdirectory
            g = glob.glob(source + '/*/*' + f'{i:04d}' + '*')
        if not g:
            # Look for ...pag01...
            g = glob.glob(source + '/*pag' + f'{i:02d}' + '*')
            if not g: # try a subdirectory
                g = glob.glob(source + '/*/*pag' + f'{i:02d}' + '*')
        # Some archives start page numbers at 1 instead of 0
        if not g and i == 0:
            print('No page 0 found, skip and try page 1')
            continue
        if not g:
            break
        docs.append(g[0])

        pic = Image.open(g[0])

        # images are supposed to be ~square but some scans contain two pages
        # side by side. Split them.
        if pic.size[0] > pic.size[1] * 1.75:
            box = (0, 0, int(pic.size[0] / 2), pic.size[1])
            imgs.append(generate_png(pic.crop(box), maxysize))
            
            box = (int(pic.size[0] / 2), 0, pic.size[0], pic.size[1])
            imgs.append(generate_png(pic.crop(box), maxysize))
        else:
            f = generate_png(pic, maxysize)
            imgs.append(f)

    if not docs:
        print('No images found. Can not create DOCUMENT.DAT')
        return

    with open(output, 'wb') as o:
        o.write(create_header(gameid)) # size 0x88
        for i in range(len(imgs)):
            o.write(bytes(128))        # size 0x80
        o.write(bytes(8))              # size 0x08, padding
        
        for idx, f in enumerate(imgs):
            b = generate_document_entry(f, o.tell())
            o.seek(0x88 + 0x80 * idx)
            o.write(b)
            o.seek(0, 2)
            f.seek(0)
            o.write(f.read())

    return output


def view_document(document, page):
    with open(document, 'rb') as i:
        buf = i.read(136)

        if struct.unpack_from('<I', buf, 0)[0] != 0x20434F44:
            print('Not a DOCUMENT.DAT file')
            exit
    
        num_pages = struct.unpack_from('<I', buf, 132)[0]
        print('Num pages:', num_pages)

        i.seek(136 + 128 * page)
        buf = i.read(128)
        offset_low = struct.unpack_from('<I', buf, 0)[0]
        size_low = struct.unpack_from('<I', buf, 12)[0]
        print('offset:', offset_low)
        print('size:', size_low)
        i.seek(offset_low)

        image = Image.open(io.BytesIO(i.read(size_low)))
        image.show()


def unpack_document(document, output):
    with open(document, 'rb') as i:
        buf = i.read(136)

        if struct.unpack_from('<I', buf, 0)[0] != 0x20434F44:
            print('Not a DOCUMENT.DAT file')
            exit
    
        num_pages = struct.unpack_from('<I', buf, 132)[0]
        print('Num pages:', num_pages)

        for page in range(num_pages):
            print('Extracting', page, 'to', output + '/%04d.png' % page)

            i.seek(136 + 128 * page)
            buf = i.read(128)
            offset_low = struct.unpack_from('<I', buf, 0)[0]
            size_low = struct.unpack_from('<I', buf, 12)[0]
            i.seek(offset_low)

            with open(output + '/%04d.png' % page, 'wb') as o:
                o.write(i.read(size_low))

        
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help='Verbose')
    parser.add_argument('command', nargs=1, choices=['create', 'view', 'unpack'], help='Command')
    #parser.add_argument('source', nargs=1, help='Directory containing image files')
    #parser.add_argument('gameid', nargs=1, help='Gameid. Example: SLES12345')
    #parser.add_argument('document', nargs=1, help='Filename of the resulting document.dat')
    parser.add_argument('--document', help='Name of DOCUMENT.DAT')
    parser.add_argument('--page', help='Page number')
    parser.add_argument('--output', help='Output file/directory')
    args = parser.parse_args()

    if args.v:
        verbose = True

    if args.command[0] == 'create':
        print('Convert', args.source[0], 'to', args.document[0]) if verbose else None
        if not create_document(args.source[0], args.gameid[0], 480, args.document[0]):
            print('Failed to create DOCUMENT')
    if args.command[0] == 'view':
        if not args.document:
            print('Must specify --document')
            os._exit(1)
        if not args.page:
            print('Must specify --page')
            os._exit(1)
        view_document(args.document, int(args.page))

    if args.command[0] == 'unpack':
        if not args.document:
            print('Must specify --document')
            os._exit(1)
        if not args.output:
            print('Must specify --output')
            os._exit(1)
        unpack_document(args.document, args.output)
        
