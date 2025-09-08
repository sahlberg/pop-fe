#!/usr/bin/env python
# coding: utf-8
#
# A utility to automate building PS3 and PSP Document files
# Based on PSP Docmaker GUI by takedown psp.in.th

try:
    from Crypto.Cipher import DES
except:
    print('Crypto is not installed.\nYou should install Crypto by running:\npip3 install Crypto')
try:
    from PIL import Image, ImageDraw, ImageFont
except:
    print('You need to install python module pillow')
import argparse
import hashlib
import io
import glob
import os
import struct
import sys
import zipfile

from pathlib import Path

verbose = False

des_key = bytes([0x39, 0xF7, 0xEF, 0xA1, 0x6C, 0xCE, 0x5F, 0x4C])
des_iv  = bytes([0xA8, 0x19, 0xC4, 0xF5, 0xE1, 0x54, 0xE3, 0x0B])
pgd_hdr = bytes([0x00, 0x50, 0x47, 0x44, 0x01, 0x00, 0x00, 0x00,
                 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
def decrypt_blob(hdr, name):
    cipher = DES.new(des_key, DES.MODE_CBC, IV=des_iv)
    msg = cipher.decrypt(hdr[:-32])
    if hashlib.sha1(hdr[:-32]).digest()[:16] != hdr[-16:]:
        print('SHA1 mismatch')
        os._exit(1)
    return msg


def decrypt_document(data, directory):
    #
    # DOC Header
    #
    offset = 0x10
    length = 0x60
    hdr = data[offset:offset + length + 0x20]
    msg = decrypt_blob(hdr, 'DOC Header')
    if msg[:4] != b'DOC ':
        print('Magic mismatch')
        os._exit(1)
    if struct.unpack_from('<I', msg, 0x04)[0] != 0x00010000 or struct.unpack_from('<I', msg, 0x08)[0] != 0x00010000:
        print('Unk mismatch')
        os._exit(1)
    print('Gameid', msg[0x0c:0x1c])
    info_block_size = 0x1f3e8 if struct.unpack_from('<I', msg, 0x1c)[0] else 0x31e8
          
    #
    # INFO Block
    #
    offset = 0x90
    length = info_block_size
    hdr = data[offset:offset + length + 0x20]
    msg = decrypt_blob(hdr, 'Info block (small)')
    if struct.unpack_from('<I', msg, 0x00)[0] != 0xffffffff:
        print('Marker mismatch')
        os._exit(1)
    psp_image_count = struct.unpack_from('<I', msg, 0x04)[0]
    print('Image count 0x%08x PSP?' % (psp_image_count))
    ps3_image_count = struct.unpack_from('<I', msg, 0x3188)[0]
    print('Image count 0x%08x PS3' % (ps3_image_count))
    
    for i in range(ps3_image_count):
        psp_fp = struct.unpack_from('<I', msg, 0x08 + i * 0x80)[0]
        psp_es = struct.unpack_from('<I', msg, 0x08 + i * 0x80 + 0x0c)[0]
        ps3_fp = struct.unpack_from('<I', msg, 0x08 + i * 0x80 + 0x10)[0]
        ps3_es = struct.unpack_from('<I', msg, 0x08 + i * 0x80 + 0x1c)[0]
        offset = ps3_fp
        length = ps3_es
        hdr = data[offset:offset + length]

        if hashlib.sha1(hdr[:-32]).digest()[:16] != hdr[-16:]:
            print('PNG SHA1 mismatch')
            os._exit(1)

        cipher = DES.new(des_key, DES.MODE_CBC, IV=des_iv)
        png_info_head = cipher.decrypt(hdr[:0x20])
        
        enc_chunks = struct.unpack_from('<I', png_info_head, 0x08)[0]
        png_size = struct.unpack_from('<I', png_info_head, 0x00)[0]
        write_size = png_size - (8 * enc_chunks) - 0x40;

        cipher = DES.new(des_key, DES.MODE_CBC, IV=des_iv)
        png_head = cipher.decrypt(hdr[0x20:0x20 + 8 * enc_chunks])

        png = hdr[0x20 + 8 * enc_chunks:][:write_size]
        for k in range(enc_chunks):
                dec_size = struct.unpack_from('<I', png_head, k * 8 + 4)[0]
                dec_offset = struct.unpack_from('<I', png_head, k * 8 + 0)[0]

                cipher = DES.new(des_key, DES.MODE_CBC, IV=des_iv)
                _b = cipher.decrypt(png[dec_offset:dec_offset + dec_size])
                png = png[:dec_offset] + _b + png[dec_offset + dec_size:]

        print('Extracting %s/%03d.png' % (directory, i))
        with open('%s/%03d.png' % (directory, i), 'wb') as f:
            f.write(png)


def encrypt_document(f, gameid, pages):
    def create_header(gameid):
        buf = bytearray(0x60)
        struct.pack_into('<I', buf, 0x00, 0x20434F44)
        struct.pack_into('<I', buf, 0x04, 0x10000)
        struct.pack_into('<I', buf, 0x08, 0x10000)
        buf[12:21] = bytes(gameid, encoding='utf-8')
        struct.pack_into('<I', buf, 0x1c, 0)
        struct.pack_into('<I', buf, 0x1c, 0 if len(pages) < 100 else 1)
        return buf
    
    print('Encrypt', gameid)
    info_block_size = 0x1f3e8 if len(pages) >= 100 else 0x31e8

    #
    # PGD header
    #
    f.write(pgd_hdr)

    #
    # DOC Header
    #
    hdr = create_header(gameid)
    cipher = DES.new(des_key, DES.MODE_CBC, IV=des_iv)
    msg = cipher.encrypt(bytes(hdr))

    msg = msg + bytes(16) + hashlib.sha1(msg).digest()[:16]
    f.write(msg)

    #
    # Info Block
    # file data starts at 0x3298 / 0x1f498
    #
    fp = info_block_size + 0x20 + 0x90 
    ib = bytearray(info_block_size)
    struct.pack_into('<I', ib, 0x00, 0xffffffff)
    struct.pack_into('<I', ib, 0x04, len(pages))
    struct.pack_into('<I', ib, 0x3188, len(pages))
    for i, p in enumerate(pages):
        png_len = len(p) + 0x20
        struct.pack_into('<I', ib, 0x08 + i * 0x80 + 0x00, fp)
        struct.pack_into('<I', ib, 0x08 + i * 0x80 + 0x0c, png_len + 0x20)
        struct.pack_into('<I', ib, 0x08 + i * 0x80 + 0x10, fp)
        struct.pack_into('<I', ib, 0x08 + i * 0x80 + 0x1c, png_len + 0x20)
        fp += png_len + 0x20
    cipher = DES.new(des_key, DES.MODE_CBC, IV=des_iv)
    msg = cipher.encrypt(bytes(ib))

    msg = msg + bytes(16) + hashlib.sha1(msg).digest()[:16]
    f.write(msg)

    #
    # File data
    #
    fp = info_block_size + 0x20 + 0x90 
    for i, p in enumerate(pages):
        print('Encrypting and writing pic', i)
        png_len = len(p) + 0x20
        
        png_info_head = bytearray(0x20)
        struct.pack_into('<I', png_info_head, 0, png_len + 0x20)
        cipher = DES.new(des_key, DES.MODE_CBC, IV=des_iv)
        png_info_head = cipher.encrypt(bytes(png_info_head))

        p = png_info_head + p
        p = p + bytes(16) + hashlib.sha1(p).digest()[:16]

        f.write(p)
        fp += len(p)



def create_document(files, gameid, maxysize, output):
    def create_header(gameid, imgs):
        buf = bytearray(136)
        struct.pack_into('<I', buf, 0, 0x20434F44)
        struct.pack_into('<I', buf, 4, 0x10000)
        struct.pack_into('<I', buf, 8, 0x10000)
        buf[12:21] = bytes(gameid, encoding='utf-8')
        struct.pack_into('<I', buf, 28, 1 if len(imgs) <= 100 else 1)
        struct.pack_into('<I', buf, 128, 0xffffffff)
        struct.pack_into('<I', buf, 132, len(imgs))
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

    files.sort()
    imgs = []
    for file in files:
        try:
            pic = Image.open(file)
        except:
            continue

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

    if not imgs:
        print('No images found. Can not create DOCUMENT.DAT')
        return

    with open(output, 'wb') as o:
        o.write(create_header(gameid, imgs)) # size 0x88
        for i in range(len(imgs)):
            o.write(bytes(128))              # size 0x80
        o.write(bytes(8))                    # size 0x08, padding
        
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


def extract_document(document, output):
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
    parser.add_argument('command', nargs=1, choices=['create', 'view', 'extract', 'decrypt', 'encrypt'], help='Command')
    parser.add_argument('--document', help='Name of DOCUMENT.DAT')
    parser.add_argument('--page', help='Page number')
    parser.add_argument('--output', help='Output file/directory')
    parser.add_argument('--directory', help='Directory containing the source PNGs')
    parser.add_argument('--gameid', help='GameID')
    args = parser.parse_args()

    if args.v:
        verbose = True

    if args.command[0] == 'decrypt':
        if not args.directory:
            print('Must specify --directory')
            os._exit(1)
        if not args.document:
            print('Must specify --document')
            os._exit(1)
    if args.command[0] == 'encrypt':
        if not args.directory:
            print('Must specify --directory')
            os._exit(1)
        if not args.document:
            print('Must specify --document')
            os._exit(1)
    if args.command[0] == 'create':
        if not args.directory:
            print('Must specify --directory')
            os._exit(1)
        if not args.document:
            print('Must specify --document')
            os._exit(1)
        if not args.gameid:
            print('Must specify --gameid')
            os._exit(1)
        print('Convert', args.directory, 'to', args.document) if verbose else None
        if not create_document(args.directory, args.gameid, 480, args.document):
            print('Failed to create DOCUMENT')

    if args.command[0] == 'view':
        if not args.document:
            print('Must specify --document')
            os._exit(1)
        if not args.page:
            print('Must specify --page')
            os._exit(1)
        view_document(args.document, int(args.page))

    if args.command[0] == 'extract':
        if not args.document:
            print('Must specify --document')
            os._exit(1)
        if not args.output:
            print('Must specify --output')
            os._exit(1)
        extract_document(args.document, args.output)
        
    if args.command[0] == 'decrypt':
        print('Decrypt', args.document)
        with open(args.document, 'rb') as f:
            buf = f.read(4)
            if buf != bytes([0x00, 0x50, 0x47, 0x44]):
                print('Not a PGD document. Can not decrypt.')
                sys.exit()
            f.seek(0)
            decrypt_document(f.read(), args.directory)
        sys.exit()

    if args.command[0] == 'encrypt':
        print('Encrypt', args.document)
        pages = []
        p = Path(args.directory)
        for png in p.iterdir():
            with open(png, 'rb') as f:
                pages.append(f.read())
        with open(args.document, 'wb') as f:
            encrypt_document(f, args.gameid if args.gameid else 'UNKN00000', pages)
        sys.exit()
