#!/usr/bin/env python
# coding: utf-8
#
# A utility to automate building PS3 and PSP Document files
# Based on PSP Docmaker GUI by takedown psp.in.th

try:
    from Crypto.Cipher import DES
    from Crypto.Cipher import AES
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

from dataclasses import dataclass
from typing import Optional, Dict, Tuple

from pathlib import Path

verbose = False

des_key = bytes([0x39, 0xF7, 0xEF, 0xA1, 0x6C, 0xCE, 0x5F, 0x4C])
des_iv  = bytes([0xA8, 0x19, 0xC4, 0xF5, 0xE1, 0x54, 0xE3, 0x0B])
pgd_hdr = bytes([0x00, 0x50, 0x47, 0x44, 0x01, 0x00, 0x00, 0x00,
                 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

### BBOX minimal implementation for encrypted PS1 DOCUMENT.DAT ###

class BBoxException(Exception):
    def __init__(self, code: int, message: str = ''):
        super().__init__(message or f'BBox Error')

def _raise(code: int, msg: str) -> None:
    raise BBoxException(msg)

KEY_VAULT = {
    0x03: bytes([0xE3, 0x50, 0xED, 0x1D, 0x91, 0x0A, 0x1F, 0xD0, 0x29, 0xBB, 0x1C, 0x3E, 0xF3, 0x40, 0x77, 0xFB]),
    0x38: bytes([0x12, 0x46, 0x8D, 0x7E, 0x1C, 0x42, 0x20, 0x9B, 0xBA, 0x54, 0x26, 0x83, 0x5E, 0xB0, 0x33, 0x03]),
    0x63: bytes([0x9C, 0x9B, 0x13, 0x72, 0xF8, 0xC6, 0x40, 0xCF, 0x1C, 0x62, 0xF5, 0xD5, 0x92, 0xDD, 0xB5, 0x82]),
}

def _encrypt_iv0(data: bytes, keyseed: int) -> bytes:
    return AES.new(KEY_VAULT[keyseed], AES.MODE_CBC, b'\x00' * 16).encrypt(data)

def _decrypt_iv0(data: bytes, keyseed: int) -> bytes:
    return AES.new(KEY_VAULT[keyseed], AES.MODE_CBC, b'\x00' * 16).decrypt(data)

def gen_pad(buf: bytes, block_size: int = 16) -> bytes:
    return buf + b'\x00' * (-len(buf) % block_size)

@dataclass
class MACKey:
    key: bytearray
    pad: bytearray
    pad_size: int

def BBMacInit(mkey: MACKey) -> int:
    mkey.pad_size = 0
    mkey.key[:] = b'\x00' * 0x10
    mkey.pad[:] = b'\x00' * 0x10

def _sub_158_encrypt_block(block: bytes, key: bytearray, key_type: int) -> Tuple[bytes, bytes]:
    if len(block) % 0x10 != 0:
        _raise('Encrypt block size must be multiple of 16')
    b = bytearray(block)
    for i in range(0x10):
        b[i] ^= key[i]
    ct = _encrypt_iv0(bytes(b), key_type)
    key_next = ct[-0x10:] if len(ct) >= 0x10 else (b'\x00' * 0x10)
    return ct, key_next

def BBMacUpdate(mkey: MACKey, buf: bytes) -> int:
    if mkey.pad_size > 16:
        _raise('MAC Key padding size must be do not exceed 16 bytes')
    size = len(buf)
    data = memoryview(buf)
    if mkey.pad_size + size <= 16:
        mkey.pad[mkey.pad_size:mkey.pad_size + size] = data.tobytes()
        mkey.pad_size += size
        return 0
    stream = bytes(mkey.pad[:mkey.pad_size]) + data.tobytes()
    rem = (mkey.pad_size + size) & 0x0F
    if rem == 0:
        rem = 16
    full_len = len(stream) - rem
    tail = stream[full_len:]
    mkey.pad[:rem] = tail
    mkey.pad_size = rem
    p = 0
    while p < full_len:
        chunk = stream[p:p + min(0x0800, full_len - p)]
        ct, key_next = _sub_158_encrypt_block(chunk, mkey.key, 0x38)
        mkey.key[:] = key_next
        p += len(chunk)

def left_shift_1(block16: bytes) -> bytes:
    b = bytearray(16)
    carry = 0
    for i in reversed(range(16)):
        v = block16[i]
        b[i] = ((v << 1) & 0xFF) | carry
        carry = 1 if (v & 0x80) else 0
    if carry:
        b[15] ^= 0x87
    return bytes(b)

def BBMacFinal(mkey: MACKey, out16: bytearray, vkey: Optional[bytes]) -> int:
    if mkey.pad_size > 16:
        _raise('MAC Key padding size must be do not exceed 16 bytes')
    L = _encrypt_iv0(b'\x00' * 16, 0x38)
    K1 = left_shift_1(L)
    K2 = left_shift_1(K1)
    # padding
    pad = bytearray(mkey.pad)
    if mkey.pad_size < 16:
        pad[mkey.pad_size] = 0x80
        for j in range(mkey.pad_size + 1, 16):
            pad[j] = 0x00
        subkey = K2
    else:
        subkey = K1
    for i in range(16):
        pad[i] ^= subkey[i]
    final_block = bytes(pad)
    ct, key_next = _sub_158_encrypt_block(final_block, mkey.key, 0x38)
    tmp1 = bytearray(ct[-16:])
    for i in range(16):
        tmp1[i] ^= KEY_VAULT[0x03][i]
    if vkey is not None:
        if len(vkey) != 16:
            _raise('Version Key must be 16 bytes')
        for i in range(16):
            tmp1[i] ^= vkey[i]
        tmp1 = bytearray(_encrypt_iv0(bytes(tmp1), 0x38))
    out16[:16] = tmp1[:16]
    mkey.key[:] = b'\x00' * 16
    mkey.pad[:] = b'\x00' * 16
    mkey.pad_size = 0

def bbmac_getkey(mkey: MACKey, bbmac: bytes) -> int:
    if len(bbmac) != 16:
        _raise('BB MAC must be exactly 16 bytes')
    tmp = bytearray(16)
    vkey_out = bytearray(16)
    BBMacFinal(mkey, tmp, None)
    mac_working = bytearray(bbmac)
    mac_working[:] = _decrypt_iv0(bytes(mac_working), 0x63)
    decrypted = _decrypt_iv0(bytes(mac_working), 0x38)
    for i in range(16):
        vkey_out[i] = tmp[i] ^ decrypted[i]
    return vkey_out

def pops_get_secure_install_id(buf: bytes) -> bytes:
    if len(buf) != 0x70:
        _raise('buf must be 0x70 bytes')
    
    mkey = MACKey(key=bytearray(16), pad=bytearray(16), pad_size=0)
    BBMacInit(mkey)
    BBMacUpdate(mkey, buf[:0x60])
    id_out = bbmac_getkey(mkey, buf[0x60:0x70])
    return id_out

def boxbb_mac_gen(buf: bytes, vkey: bytes) -> bytes:
    if len(vkey) != 16:
        _raise('version_key must be 16 bytes')
    
    buf = bytes(buf)
    tmp = bytearray(16)
    mkey = MACKey(key=bytearray(16), pad=bytearray(16), pad_size=0)
    BBMacInit(mkey)
    BBMacUpdate(mkey, buf)
    BBMacFinal(mkey, tmp, vkey)
    return bytes(tmp)

def boxbb_mac_gen_enc(buf: bytes, vkey: bytes) -> bytes:
    get_bb_mac =  boxbb_mac_gen(buf, vkey)
    return _encrypt_iv0(get_bb_mac, 0x63)

###################

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

    ins_id = bytes(0x10) # Secure Install ID can be any for custom PS1 PBP
    
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

    msg = msg + boxbb_mac_gen_enc(msg, ins_id) + hashlib.sha1(msg).digest()[:16]
    f.write(msg)

    #
    # Info Block
    # file data starts at 0x3298 / 0x1f498
    #
    fp = info_block_size + 0x20 + 0x90 
    ib = bytearray(info_block_size)
    struct.pack_into('<I', ib, 0x00, 0xffffffff)
    struct.pack_into('<I', ib, 0x04, len(pages))
    struct.pack_into('<I', ib, 0x3188 if len(pages) < 100 else 0x1f388, len(pages))
    for i, p in enumerate(pages):
        png_len = len(p) + 0x20
        struct.pack_into('<I', ib, 0x08 + i * 0x80 + 0x00, fp)
        struct.pack_into('<I', ib, 0x08 + i * 0x80 + 0x0c, png_len + 0x20)
        struct.pack_into('<I', ib, 0x08 + i * 0x80 + 0x10, fp)
        struct.pack_into('<I', ib, 0x08 + i * 0x80 + 0x1c, png_len + 0x20)
        fp += png_len + 0x20
    cipher = DES.new(des_key, DES.MODE_CBC, IV=des_iv)
    msg = cipher.encrypt(bytes(ib))

    msg = msg + boxbb_mac_gen_enc(msg, ins_id) + hashlib.sha1(msg).digest()[:16]
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
        p = p + boxbb_mac_gen_enc(p, ins_id) + hashlib.sha1(p).digest()[:16]

        f.write(p)
        fp += len(p)



def create_document(f, gameid, pages):
    def create_header(gameid, pages):
        buf = bytearray(136)
        struct.pack_into('<I', buf, 0, 0x20434F44)
        struct.pack_into('<I', buf, 4, 0x10000)
        struct.pack_into('<I', buf, 8, 0x10000)
        buf[12:21] = bytes(gameid, encoding='utf-8')
        struct.pack_into('<I', buf, 28, 0 if len(pages) < 100 else 1)
        struct.pack_into('<I', buf, 128, 0xffffffff)
        struct.pack_into('<I', buf, 132, len(pages))
        return buf
    
    def generate_document_entry(p, pos):
        buf = bytearray(128)
        struct.pack_into('<I', buf, 0, pos) # offset low
        struct.pack_into('<I', buf, 12, len(p)) # size low

        return buf

    f.write(create_header(gameid, pages)) # size 0x88
    for i in range(len(pages)):
        f.write(bytes(128))              # size 0x80
        f.write(bytes(8))                # size 0x08, padding
        
    for idx, p in enumerate(pages):
            b = generate_document_entry(p, f.tell())
            f.seek(0x88 + 0x80 * idx)
            f.write(b)
            f.seek(0, 2)
            f.write(p)

            
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

def create_document_from_dir(gameid, dir, doc):
        pages = []
        for png in sorted(Path(dir).iterdir()):
            image = Image.open(png)
            maxysize = 480
            sf = 480 / image.size[0]
            ns = (480, int(sf * image.size[1]))
            if ns[1] > maxysize:
                ns = (480, maxysize)
            image = image.resize(ns, Image.Resampling.LANCZOS)
            f = io.BytesIO()
            image.save(f, 'PNG')
            f.seek(0)
            pages.append(f.read())
        with open(doc, 'wb') as f:
            create_document(f, gameid if gameid else 'UNKN00000', pages)
        
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
        print('Create', args.document)
        create_document_from_dir(args.gameid, args.directory, args.document)
        sys.exit()

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
        for png in sorted(Path(args.directory).iterdir()):
            image = Image.open(png)
            maxysize = 480
            sf = 480 / image.size[0]
            ns = (480, int(sf * image.size[1]))
            if ns[1] > maxysize:
                ns = (480, maxysize)
            image = image.resize(ns, Image.Resampling.LANCZOS)
            f = io.BytesIO()
            image.save(f, 'PNG')
            f.seek(0)
            pages.append(gen_pad(f.read()))
        with open(args.document, 'wb') as f:
            encrypt_document(f, args.gameid if args.gameid else 'UNKN00000', pages)
        sys.exit()
