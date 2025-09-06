#!/usr/bin/env python
# coding: utf-8
#
# A utility to automate building PSP Document files
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
    print(name)
    for i in range(0x00, len(hdr), 0x10):
        if i < 0x20 or i > len(hdr) - 0x30:
            print('%04x ' % i, hdr[i:i+16].hex())
    print('Decrypted', name)
    for i in range(0x00, len(msg), 0x10):
        if i < 0x50 or i > len(msg) - 0x30:
            print('%04x ' % i, msg[i:i+16].hex())
    print('SHA1 of', name, hashlib.sha1(hdr[:-32]).digest()[:16].hex())
    if hashlib.sha1(hdr[:-32]).digest()[:16] != hdr[-16:]:
        print('SHA1 mismatch')
        os._exit(1)
    return msg


def decrypt_document(data):
    # Offsets in DAT file
    # 0x00000010 | 0x60 | DOC header           | Encrypted, data vary.
    # 0x00000070 | 0x10 | Unknown              | Some kind of hash or key.
    # 0x00000080 | 0x10 | DOC header SHA1 part | First 16 bytes of SHA1 calculated from encrypted DOC header

    #
    # DOC Header
    #
    offset = 0x10
    length = 0x60
    hdr = data[offset:offset + length + 0x20]
    msg = decrypt_blob(hdr, 'DOC Header')
    print('Magic', msg[:4])
    if msg[:4] != b'DOC ':
        print('Magic mismatch')
        os._exit(1)
    print('Unk %08x %08x' % (struct.unpack_from('<I', msg, 0x04)[0], struct.unpack_from('<I', msg, 0x08)[0]))
    if struct.unpack_from('<I', msg, 0x04)[0] != 0x00010000 or struct.unpack_from('<I', msg, 0x08)[0] != 0x00010000:
        print('Unk mismatch')
        os._exit(1)
    print('Gameid', msg[0x0c:0x1c])
    print('Size', struct.unpack_from('<I', msg, 0x1c)[0])
    print()
    
    #
    # INFO Block
    #
    offset = 0x90
    length = 0x31e8
    hdr = data[offset:offset + length + 0x20]
    msg = decrypt_blob(hdr, 'Info block (small)')
    print('Marker %08x' % (struct.unpack_from('<I', msg, 0x00)[0]))
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
        print('%d FP:0x%08x ES:0x%08x FP:0x%08x ES:0x%08x' % (i,
                                         psp_fp, psp_es,
                                         ps3_fp, ps3_es))
        offset = ps3_fp
        length = ps3_es
        hdr = data[offset:offset + length]
        png = decrypt_blob(hdr, 'PNG #%d' % i)
        with open('pages/%03d.dat' % i, 'wb') as f:
            f.write(png)
        png_size = struct.unpack_from('<I', png, 0)[0]
        print('PNG Size %x , file size %x' % (png_size, len(png)))
        if png_size != len(png) + 0x20:
            print('PNG len mismatch')
            os._exit(0)
        if png_size != ps3_es:
            print('PNG entry size mismatch')
            os._exit(0)
    cipher = DES.new(des_key, DES.MODE_CBC, IV=des_iv)
    msg = cipher.decrypt(data[16:])
    return msg


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
    for i in range(0x00, len(msg), 0x10):
        if i < 0x30 or i > len(msg) - 0x30:
            print('%04x ' % i, msg[i:i+16].hex())
    print('SHA1 of header', hashlib.sha1(msg).digest()[:16].hex())

    #
    # Info Block
    # file data starts at 0x3298
    #
    fp = 0x3298
    ib = bytearray(0x31e8)
    struct.pack_into('<I', ib, 0x00, 0xffffffff)
    struct.pack_into('<I', ib, 0x04, len(pages))
    struct.pack_into('<I', ib, 0x3188, len(pages))
    for i, p in enumerate(pages):
        struct.pack_into('<I', ib, 0x08 + i * 0x80 + 0x00, fp)
        struct.pack_into('<I', ib, 0x08 + i * 0x80 + 0x0c, len(p) + 0x20)
        struct.pack_into('<I', ib, 0x08 + i * 0x80 + 0x10, fp)
        struct.pack_into('<I', ib, 0x08 + i * 0x80 + 0x1c, len(p) + 0x20)
        fp += len(p) + 0x20
    cipher = DES.new(des_key, DES.MODE_CBC, IV=des_iv)
    msg = cipher.encrypt(bytes(ib))

    msg = msg + bytes(16) + hashlib.sha1(msg).digest()[:16]
    f.write(msg)
    print('SHA1 of Info Block', hashlib.sha1(msg).digest()[:16].hex())

    #
    # File data
    #
    fp = 0x3298
    for i, p in enumerate(pages):
        print('P', i)
        for i in range(0x00, len(p), 0x10):
            if i < 0x40 or i > len(p) - 0x30:
                print('%04x ' % i, p[i:i+16].hex())
        print('Encode pic', i)
        cipher = DES.new(des_key, DES.MODE_CBC, IV=des_iv)
        msg = cipher.encrypt(bytes(p))
        msg = msg + bytes(16) + hashlib.sha1(msg).digest()[:16]
        for i in range(0x00, len(msg), 0x10):
            if i < 0x30 or i > len(msg) - 0x30:
                print('%04x ' % i, msg[i:i+16].hex())
        f.write(msg)
        fp += len(msg)


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
        g = glob.glob(source + '/*' + f'{i:04d}' + '*')
        if not g: # try a subdirectory
            g = glob.glob(source + '/*/*' + f'{i:04d}' + '*')
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help='Verbose')
    parser.add_argument('--source', nargs=1, help='Directory containing image files')
    parser.add_argument('--gameid', nargs=1, help='Gameid. Example: SLES12345')
    parser.add_argument('--document', nargs=1, help='Filename of the resulting document.dat')
    parser.add_argument('--decrypt', nargs=1, help='Filename to decrypt')
    parser.add_argument('--encrypt', nargs=1, help='Filename to decrypt')
    args = parser.parse_args()

    if args.v:
        verbose = True

    if args.decrypt:
        print('Decrypt', args.decrypt)
        with open(args.decrypt[0], 'rb') as f:
            buf = f.read(4)
            if buf != bytes([0x00, 0x50, 0x47, 0x44]):
                print('Not a PGD document. Can not decrypt.')
                sys.exit()
            f.seek(0)
            buf = decrypt_document(f.read())
        sys.exit()

    if args.encrypt:
        print('Encrypt', args.encrypt)
        pages = []
        p = Path('pages')
        for png in p.iterdir():
            with open(png, 'rb') as f:
                pages.append(f.read())
        with open(args.encrypt[0], 'wb') as f:
            encrypt_document(f, 'SCUS94457', pages)
        sys.exit()
        
    print('Convert', args.source[0], 'to', args.document[0]) if verbose else None
    create_document(args.source[0], args.gameid[0], 480, args.document[0])
