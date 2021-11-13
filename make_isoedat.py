#!/usr/bin/env python
# coding: utf-8
#
# Quick hack to convert https://github.com/Sorvigolova/make_npdata.git
# to python 3. This is not a full conversion of that really nice tool
# but only the parts that are used when creating a PSX classics
# ISO.BIN.EDAT for PS3 packages
#
import hashlib
import os
import struct
from Crypto.Cipher import AES

NPDRM_PSX_KEY = bytes([
    0x52, 0xC0, 0xB5, 0xCA,  0x76, 0xD6, 0x13, 0x4B,
    0xB4, 0x5F, 0xC6, 0x6C,  0xA6, 0x37, 0xF2, 0xC1
])
NPDRM_OMAC_KEY_2 = bytes([
    0x6B, 0xA5, 0x29, 0x76,  0xEF, 0xDA, 0x16, 0xEF,
    0x3C, 0x33, 0x9F, 0xB2,  0x97, 0x1E, 0x25, 0x6B
])
NPDRM_OMAC_KEY_3 = bytes([
    0x9B, 0x51, 0x5F, 0xEA,  0xCF, 0x75, 0x06, 0x49,
    0x81, 0xAA, 0x60, 0x4D,  0x91, 0xA5, 0x4E, 0x97
])
EDAT_FOOTER_V1 = bytes([
    0x45, 0x44, 0x41, 0x54,  0x41, 0x20, 0x70, 0x61,
    0x63, 0x6B, 0x61, 0x67,  0x65, 0x72, 0x00, 0x00
])

def xor(x, y):
    out = bytearray(x)
    for i in range(len(out)):
        out[i] ^= y[i]
    return out

def aes_cmac(K, M):
    def generate_subkeys(KEY):
        def ls(data):
            out = bytearray(len(data))
            for i in range(len(data)):
                out[i] = (data[i] << 1) & 0xff
                if i > 0 and data[i] & 0x80:
                    out[i - 1] |= 0x01
            return out

        obj = AES.new(KEY, AES.MODE_ECB)
        L = obj.encrypt(bytes(16))
        K1 = ls(L)
        if L[0] & 0x80:
            K1[15] ^= 0x87
        K2 = ls(K1)
        if K1[0] & 0x80:
            K2[15] ^= 0x87
        return (K1, K2)

    K1, K2 = generate_subkeys(K)
    n = int((len(M) + 15) / 16)
    if n == 0:
        n = 1
        flag = False
    else:
        if (len(M) % 16) == 0:
            flag = True
        else:
            flag = False

    if flag:
        M_last = xor(M[(n - 1) * 16:n * 16], K1)
    else:
        _m = M[(n - 1) * 16:] + bytes([0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                                       0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        _m = _m[:16]
        M_last = xor( _m[:16], K2)
    X = bytearray(16)
    for i in range(1, n):
        Y = xor(X, M[(i - 1) * 16:i * 16])
        obj = AES.new(K, AES.MODE_ECB)
        X = obj.encrypt(bytes(Y))
    Y = xor(M_last, X)
    obj = AES.new(K, AES.MODE_ECB)
    T = obj.encrypt(bytes(Y))
    return T

        
def pack(ifn, ofn, cid):
    def get_block_key(npd, i):
        b = bytearray(16)
        if npd['version'] > 1:
            b = npd['dev_hash']
        struct.pack_into('>I', b, 12, i)
        return b
    
    i = open(ifn, 'rb')
    o = open(ofn, 'wb', buffering=0)
    
    i.seek(0, 2)
    fs = i.tell()
    i.seek(0)

    npd = {}
    npd['magic'] = bytes([0x4E, 0x50, 0x44, 0x00])
    # qqq random number
    npd['digest'] = bytes(0x10)
    npd['version'] = 1
    npd['license'] = 3
    npd['type'] = 0
    npd['content_id'] = cid

    b = bytearray(0x30)
    b[:len(npd['content_id'])] = npd['content_id'].encode()
    b = b + ofn.split('/')[-1].encode()
    
    _key = bytes([0x2b, 0x7e, 0x15, 0x16,  0x28, 0xae, 0xd2, 0xa6,
                 0xab, 0xf7, 0x15, 0x88,  0x09, 0xcf, 0x4f, 0x3c,])
    _b = bytes([0x6b, 0xc1, 0xbe, 0xe2,  0x2e, 0x40, 0x9f, 0x96,
               0xe9, 0x3d, 0x7e, 0x11,  0x73, 0x93, 0x17, 0x2a,
               0xae, 0x2d, 0x8a, 0x57,  0x1e, 0x03, 0xac, 0x9c,
               0x9e, 0xb7, 0x6f, 0xac,  0x45, 0xaf, 0x8e, 0x51,
               0x30, 0xc8, 0x1c, 0x46,  0xa3, 0x5c, 0xe4, 0x11
               ])
    _b = bytes([0x6b, 0xc1, 0xbe, 0xe2,  0x2e, 0x40, 0x9f, 0x96,
               0xe9, 0x3d, 0x7e, 0x11,  0x73, 0x93, 0x17, 0x2a])

    key = NPDRM_OMAC_KEY_3
    npd['title_hash'] = aes_cmac(key, b)


    b = bytearray(0x60)
    b[0:4] = npd['magic']
    struct.pack_into('>I', b, 4, npd['version'])
    struct.pack_into('>I', b, 8, npd['license'])
    struct.pack_into('>I', b, 12, npd['type'])
    b[16:16 + len(npd['content_id'])] = bytes(npd['content_id'], encoding='utf-8')
    b[0x40:0x50] = npd['digest']
    b[0x50:0x60] = npd['title_hash']
    npd_buf = b
    
    k = xor(NPDRM_PSX_KEY, NPDRM_OMAC_KEY_2)
    npd['dev_hash'] = aes_cmac(bytes(k), b)
    npd['unk1'] = 0
    npd['unk2'] = 0
    npd_buf = npd_buf + npd['dev_hash'] + bytes(0x10)

    o.write(npd_buf)
    b = bytearray(16)
    struct.pack_into('>I', b, 0, 0)
    struct.pack_into('>I', b, 4, 0x4000)
    struct.pack_into('>Q', b, 8, fs)
    o.write(b)

    # encrypt data
    block_num = (fs + 0x4000 - 1) >> 14
    for idx in range(block_num):
        length = 0x4000
        if idx == (block_num - 1) and (fs & 0x3fff):
            length = fs & 0x3fff
        length = (length + 0x0f) & 0xfffff0

        b_key = get_block_key(npd, idx)
        
        obj = AES.new(NPDRM_PSX_KEY, AES.MODE_ECB)
        key_result = obj.encrypt(bytes(b_key))
        hash = key_result

        i.seek(idx * 0x4000)
        dec_data = bytes(i.read(length))
        orig_len = (len(dec_data) + 0x0f) & 0xfffff0
        if len(dec_data) % 0x4000:
            dec_data = (dec_data + bytes(0x4000))[:0x4000]

        iv = bytearray(16)
        obj = AES.new(key_result, AES.MODE_CBC, IV=bytes(iv))
        enc_data = obj.encrypt(bytes(dec_data))[:orig_len]
        
        # hash_result
        # hash is key to generate hash_result
        kr = aes_cmac(hash, enc_data)

        metadata_offset = 0x100
        data_offset = metadata_offset + idx * 0x4000 + block_num * 0x10;
        o.seek(metadata_offset + idx * 0x10)
        o.write(kr)
        o.seek(data_offset)
        o.write(enc_data)
        
    o.write(EDAT_FOOTER_V1)

    # forge_data with NPDRM_PSX_KEY
    metadata_section_size = 0x10
    metadata_size = metadata_section_size * block_num
    metadata = None
    with open(ofn, 'rb') as oo:
        oo.seek(metadata_offset)
        metadata = oo.read(metadata_size)
    out = metadata
    test_hash = aes_cmac(NPDRM_PSX_KEY, out)
    o.seek(0x90)
    o.write(test_hash)

    header = None
    with open(ofn, 'rb') as oo:
        header = oo.read(0xa0)

    header_hash = aes_cmac(NPDRM_PSX_KEY, header)
    o.seek(0xA0)
    o.write(header_hash)
    # qqq random number
    o.seek(0xb0)
    o.write(bytes(0x28))
    # qqq random number
    o.seek(0xd8)
    o.write(bytes(0x28))
