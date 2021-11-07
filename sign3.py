#!/usr/bin/env python
# coding: utf-8
#

import sys, os, struct
import hashlib, ecdsa, random
from random import SystemRandom

randrange = SystemRandom().randrange

def calc_sign(data):
        """Function to compute the ISO.BIN.DAT signature"""
        
        curves = [{'p': 1461501637330902918203684832716283019655932542975,
                   'a': 1461501637330902918203684832716283019655932542975,
                   'b': 1461501637330902918203684832716283019655932542975,
                   'n': 1461501637330902918203684832716283019655932542975,
                   'gx': 1461501637330902918203684832716283019655932542975,
                   'gy': 1461501637330902918203684832716283019655932542975},
                  {'p': 1461501637330902918124456670238912170209807695871,
                   'a': 1461501637330902918124456670238912170209807695868,
                   'b': 581275243328273534259255496293561290936658765305,
                   'n': 1461501637330902918124458737530352623637560536463,
                   'gx': 196105516859354170561280076814916289620938717434,
                   'gy': 549564953432973815087283996023303832312926505152},
                  {'p': 1461501637330902918124456670238912170209807695871,
                   'a': 1461501637330902918124456670238912170209807695868,
                   'b': 950812983575425018239712668469910028473725751051,
                   'n': 1461501637330902918124456319238612540852236394791,
                   'gx': 105945626425139563508148418928688246159615974956,
                   'gy': 510070091837085313874263221888064838463259626207}]

        def s2i(s):
	        result = 0
	        for c in s:
		        result = 256 * result + c
	        return result

        def calculate_sha1_hash(data):
	        return hashlib.sha1(data).digest()
        
        k = 0x00bf21224b041f29549db25e9aade19e720a1fe0f1
        c = ecdsa.ellipticcurve.CurveFp(curves[0x02]['p'], curves[0x02]['a'], curves[0x02]['b']) # curve equation
        g = ecdsa.ellipticcurve.Point(c, curves[0x02]['gx'], curves[0x02]['gy'], curves[0x02]['n']) # generator point
        e = s2i(calculate_sha1_hash(data)) 

        public_key = ecdsa.ecdsa.Public_key(g, g * k)
        private_key = ecdsa.ecdsa.Private_key(public_key, k)

        m = randrange(1, curves[0x02]['n'])
        signature = private_key.sign(e, m)
        rr = bytes.fromhex('{0:040X}'.format(signature.r))
        ss = bytes.fromhex('{0:040X}'.format(signature.s))
        return rr + ss

if __name__ == "__main__":
    with open(sys.argv[1], 'rb') as _f:
        _b = calc_sign(_f.read())
    with open(sys.argv[1], 'ab') as _f:
        _f.seek(0, 2)
        _f.write(_b)
