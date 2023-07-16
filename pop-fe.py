#!/usr/bin/env python
# coding: utf-8
#
# A utility to automate building and installing PSX games onto different
# systems.
# The current directory where you run this utility from needs to be writable
# so that we can use it to store temporary files during the conversing process.

try:
    from PIL import Image, ImageDraw, ImageFont
except:
    print('You need to install python module pillow')
import argparse
import datetime
import io
import os
import re
import random
import struct
import sys
have_pycdlib = False
try:
    import pycdlib
    have_pycdlib = True
except:
    True
have_iso9660 = False
try:
    import iso9660      # python-pycdio
    have_iso9660 = True
except:
    True
have_pytube = False
try:
    from pytube import YouTube
    from pytube.contrib.search import Search
    have_pytube = True
except:
    True
try:
    import rarfile
except:
    print('rarfile is not installed.\nYou should install requests by running:\npip3 install rarfile')
try:
    import requests
except:
    print('requests is not installed.\nYou should install requests by running:\npip3 install requests')
import subprocess
import zipfile
try:
    from vmp import encode_vmp
except:
    True
from pathlib import Path
from bchunk import bchunk
from document import create_document
from gamedb import games, libcrypt, themes
try:
    from make_isoedat import pack
except:
    True
from popstation import popstation, GenerateSFO
from ppf import ApplyPPF
from riff import copy_riff, create_riff, parse_riff
try:
    from theme_ascii import create_ascii_pic0, create_ascii_pic1
    from theme_dotpainting import create_dotpainting_pic0, create_dotpainting_pic1
    from theme_opencv import create_oilpainting_pic0, create_oilpainting_pic1, create_watercolor_pic0, create_watercolor_pic1, create_colorsketch_pic0, create_colorsketch_pic1
except:
    print('You need to install python module pillow and opencv-contrib-python')
    
temp_files = []  

i0 = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\xb0\x00\x00\x00\xb0\x08\x06\x00\x00\x00\xaf\xb7\xe4^\x00\x00\x0fjzTXtRaw profile type exif\x00\x00x\xda\xad\x9aYr\xf30\xae\x85\xdf\xb9\x8a^\x828\x82\\\x0e\xc7\xaa\xbb\x83\xbb\xfc\xfe@\xc9\x8e\xed\xcc\xf9;\xaeX\x8a\x04\x81\x18\x0f\x00*f\xfe\xff\xff-\xf3\x1f~b\x8c\xd9\x84(9\x95\x94\x0e~B\t\xc5UN\xf2q\xfe\xd4\xfdm\x8f\xb0\xbf\xf7O\xbbn\xf1\xf7\xd3us\xbf\xe1\xb8\xe49\xfa\xf3\xcf\x9c.\xfa\xdbu{gp\x1e*g\xf1\x81Q\xee\xd7\x8d\xf6|\xa3\x84\x8b\x7f~a\xe4\xce\x83W\x89\xf4|\\\x8c\xca\xc5\xc8\xbb\xf3\x86\xbd\x18\xd4S\xad#\x95,O\xaa\xcd\xf38n\x9a\xe4\xf3\xd7\xe8W\xc8\xcfb\xbf\xfb[\xb0\xde\x88\xac\xe3\x9d\x9b\xde\xfa\x83o\xef/\x01\xbc\xfez\xe3\xeb>\xd1o\x84\x82(rn!\xab\x17\xa9=\r\xf2\x91\x9d\xee?\x05\x89\x96\x8a\x1a>$z\xf2\xca\xfd\xcc~|\xdd\xbcz+\xb8\x8b\xc4\xbf\x189\xdd\x8f\x1f^76\xbe\xdc\xf0\xf7u\xdc\xe3\xca!_g\xee\xf9z\x92\xd3=\xe6x\xb1\xbe\xfe\xae5\xf2\xda:\xa3E\r\tS\xa7K\xa9\xbb\xd5\xf4\x04:\xc20\xe8\xd2\xd9 Z:\x84\xdf\x08\x0b\xd9\x9f\xc2\'\x13\xd5\x9d\xb5\xc6\xd1\t\xe6\xc6y\xb1\x0ew-\x1b\xec\xb0\xd5.;\xf7\xb1\xdb\x8e\x88\xc1M\xe3\x84\x13\xe7\xba\xf3\xfbb\xf6\xe2\x8a\xeb^\xfd\x17\xf4c\x97\x13_\xfc\xf0\x19\xdf\xf6\xed\xf6\xe0\xdd]\x16\xbb\x97-G7{\xb5\xcc\xca\xc3B\xea,\xcc,\x8f\xfc\xfac~\xfb\xc0Z\x9a\n\xd6\x1e\xf9n+\xe4rN\x8d\x8d\x18\xea9\xfd\x86\x0c\x1f\xd8u\x195n\x03\xdf>\xaf?\xeaW\x8f\x07\xa3ZYS\xa4`\xd8v\xb2h\xd1\xbe!\x81\xdf\x8e\xf6\x10F\x8eg\x0eZ\x19\x17\x03L\xc4\xd2\x11a\xac\xc7\x03x\x8d\xac\xb0\xc9\x1e\xe2\x9cX\x8b!3\x0e\xaa\x88\xee|p\r\x0f\xd8\x18\xdd@H\x17\xbcO\xf8&;]\x9aG\xc4nR\x17\x1d\x97\r\xd7\x013<\x11}\xf2\x82o\x8a\xaf8+\x84H\xfcH\xc8\xc4P\x8d>\x06P0E\x899\x96X\x93O!\xc5\x94\x92$\x05\xc5*^\x82\x91(ID\xb2\x14\xa9\xd9\xe7\x90cNYr\xce%\xd7\xe2\x8a\x074cIEJ.\xa5\xd4\xca\x9a\x15\xce\x95\xa7+\x04\xb56\xd7|\x0b-\x9a\x96\x9a\xb4\xdcJ\xab\x9d\xf0\xe9\xa1\xc7\x9e\xba\xf4\xdcK\xaf\xc3\r?\xc0\x8f\x91\x86\x8c<\xca\xa8\xd3NBi\x86\x19g\x9a2\xf3,\xb3.Bmy\xb3\xc2\x8a+-Yy\x95U\xef^\xbb\xdc\xfa\xee\xf3\x0b\xaf\xd9\xcbkn{J\t\xe5\xee5\xae\x8a\xdcXX\x85\x93\xa8>\xc3a\xce\x04\x8b\xc7E]@@;\xf5\xd9\x91m\x08N=\xa7>;\n\xf0\xe7\xa3C\xc8\xa8>\x1bV=\x86\x07\xc3\xb4..{\xf3\x9dq\xa7G\xd5s\xff\xe47#\xe1\xc9o\xee\xaf\x9e3\xea\xba_z\xee\xbd\xdf>\xf2\xda\xd02\xd4\xb7\xc7\xce,T\xa3\x1e\x9e\xec\x83\xa6\xba\\\xab\x88\xaf)\xb61\x06\xc4c\xf6\xbc\xe4p\xc4Q\xec\xab$\xe7[\x96\x10|\x99\xad\x15x\xc0qm\xef\x89\x1d5S}\xa2E\x821=\x0b\xf6R\x9d\xe4P\x93\xa0R\n\xbe\xe6T\x8fj\xaa\xcd=Rf\x0fT\xf3\xc3\xa2\x1eV\x9aR\xf53\xb0J\xaa\x9e\x88\x93\x1e#vt\xc3\xa52\x12y\\:\x99\x99\xf3\xc0\x8eb\xbb\xf8nJ\x04P\xed\xc2.6.7\x08\'\x14^v\xc0\xa6\xaaTc\x95\xb8\xa5\x83\xe1\xb4RV\x9eM\xed\xb5\xe6\xea\x10d\xaa\xbc\x0c\x1ck\xa2\xf4&P\xb6\xbe\xba\xc4\x89\xdd\xf51\x99Q`\x99\xf5<G\x8c\xea\xeb\x8a\r\x8em\xb9\x06C];\xba\xdb\xda\x18\xd5\x99\x87\xe5\xaf\xc5?^Z\x19^\x8b\xdf\xd6>\x1eW7\xebm\xf1\xa7\xa5\xa1\xfah\xf1O\x157_k\xfes\xc5\xcd\xd7\x9a\xff\\q\xf3\xb5\xe6?W\xdc\xfc\x8b\xcb\x1f\x157\xff\xe2\xf2G\xc5\xcd\xbf\xb8\xfcQq\xf3\x8d\xcb}L\xa5\x91#*Ah\xa9\xf84Gha\xe5\xb4\x1c\x8b\xcf\xda\x0e\xd8\x805\x06\x1ee\x91\xdd=\x86a}\xd7L\x1ct\x05-\x8e\x10\xb2\x0b\xa3\xf5\x1cH%8-\xed%\x82\x90\xa1\xc7\\\x1b\x06\xd2\xd80P\xe3\x1a\x03\x89: rp\xa1vr\xd4\x05`@\x82\x05gZ\x04fkYZ\t\xbc\x1f\xb3N\xf4T\x10\xc02E:h"9RD\xf3T\x143IVR\x1c\xb0%Fr]\x12\xa8\xdd\x8bU#\xd1\xc2`A`\x00\x03u\x9e\x063\x8a\x03GjB\xe81@\x93<\xc78*\x18J\xaeM\x90Y,\x0f\xd0\xc5\xb1D\x92\xee\n8\xd5\x80\xacH\x99\xee\xb1\x95H_)>\xd2\x1fc\xc9<\x82\xab\xd4\xf1Z\xf3\xccZ\xf4\xbb\x0b\x91\xbam\xf0\x98\xa5\xc2D\xc1t\xee\x00\xd6\xe6\x98#I\xa1\xc0S\x0bBj\xa8jK_\xea\x80q\xa44p\x86\x94N\xe7\xcdZ\xfb\x1c\xd0\x07\xf7\xccvi\x89\xa9\xeeX\xf2\xa3\xc0pQ\x90\xd4\xad1\xd6\x1d\x04}\xa5\xb0}:u\xc8\x90\xda&\xde\xc7W<?\xec\xc5\x8f\x11b3\x84\xee\xe2\xf6\x11\xaf\x93\xd3\x0b\x1f\xd6\x9fr\xe7d\xe4\x8d\xd3\xdf%\x83\x9f\xb9\x89\xf6\xaf\x92\x99\xf1\x9e\xd3\x9f$37\xd1\xfeU2\xf3j\xb4\xbfJf^\x8d\xf6W\xc9\xccg\xee\xfc\xadd\xe63w\xfeV2\xf3]\xa0\xddR\xe0;\xc9\xccw)\xe0fz\x93lS} \x1b=\xaaq}\xc4\x0c[\xf2z\x9dW\x0f\xab\xd0C\xbf@\xa3^\xe9xh\t\xe9\x81\x8e\xdc\x878?i\xf7\x0en\x01k+U\x9a\xb5P\x99P\xf86\xf9\xf0\xf4L\xbeE\xed\xd1b\x02=i\x01\x99\x94\xc6\x88\xbd\xe9|\xe8J\x9c \x0c\xf3 P\x04\xa0\x87nS`\x84\xd3V$\xc5Pi\x98\xe11\x8c\xf8i3M\x8f\xa2\xbf\xa7/.\xc1\x83}\xd6\xae4rP\\\x03\x1d{a\x80\x04C\xed\xc8\xd6\x05\xfa\xb5\x12\xc1W\xc9Vf\x9f)\x00Q\xd2Mh\x16\xf8\x8f\x91\x995+\xe2\xab\x15&\x80\xbaZP\x94\xea\xd8\x82\xa6i\xcdPg\x07v\xe3\x1c\x96"\x93}\\\xf1\xba\r\xfeB`n\x14<u\xa3\t:\xe7O\x14],\xeb\xe3\xa4\x17.4g\x14\x80:\xf1\x12R\x06\xdak\xca\x17\x92\xf5\xb1hZg\xeaT\x11\x1en\xc5.0\x173\xa7\x05p\x06E\xf9_\x1e\xcdO\t\xa9\x01\xb8Tu\x8c4\xe3\xaaA\xc0};h\xdcHt\xb5DZ\x88\xe88\xba\x8f\xd9\xce\x83\x0er\xd1OR\x84\xa5\xd3zN\xe2\xa2\xe5\x1d?\x95H\xc1\xa9\x03\xbbw\xb524\xcejt(-}6\xc4\xe2\xa2\xb49.7<\x13<\xdc\xd7\xaa\xb6t\xa8Mg\xfc\xbb\xd6\xa8NCZ\xa0J\x1b\xdd\xb6\xa2\x15\x0f\'\rQ\xaeT\xcf4U\xf7xb)\x91\x88_\xc3\xb52\x16\x83R\xa7\xb6\xcd\xdd\xbb\x08kb\xec&\x958lm\xe1>\xa1R\xe3!\xdf\x86z\xc8\xc9.w\xa2\xa9\xa2\x96\x82\xdb\xe7G\xf3\x1d\xc1WG;\x8bL:\x19\xacZ\x8c\x7f2\xab\xec\x88\n\x0c0\xf4\x05X\xdf\xcf\xa3o\xbav*q\'L\x072{\xe2\xf1\xb4\xfe\xb6\xd1i_\x1d<N\x0b\xeb\x03\xfeC\x1f|N\xb3\xb7}\xbe2\xf2\xdd\x0b\x1fzj;\n\xee\xbd\x8fn2y\x90\x8e\xd4\x92x\x14b\xd9\xd8w\xd48`\xadd\xba)\xf2 \xc7\xca\xc4E\x9e>x\x89Q\x07D\xd0q\x89\xe4\xe7hn\'\xffz|f\x04\x10\xb5\xce\xb0CF\x86\xdd1Vl\xa9\xa1\x03\xf0`V\xb7\xd5\x91\xd4h\xedt\x02{\xa42\x9b\xcc\x1e\x90\xa5\x8b\x0c~5-\xc2\r[\x0674\x9c6\xb1l+u\xe0b\t\x8d\xec\xe1\x9eh\xccGDX\xa8\xcd\xcd\x16|%a\x18z\xcfl\xa3\xb9\xc3\x8a\xc1\xd6\xc5\xf4\xbbI6\xc1\xa1\x13\xe4\xa6\xb9(t\x03\xa6\xea6-\xdd\xe7v\x82\xa27>\xb2ncM.`\rv_4a\x0c\xf9\x8c\x9cL\xf2@}mv\xc7Q\x08m\x9cr\xddr\x02\xbc\xfd5(\x99_= \xf5XL\xf3\x13[\x9fSo\x1c\xd4*D\xefA\xbbZ\xf1\x88\xd2\xb4\xcf\xc4\r\x84\xad\rm\'\x0e\xf8\x85\'\xe2\x11\x80|ZS\xda\xe2\xa1\xf6c~^I\xb0O9\x9a\xa0\xae\x02\xech\xdb\xd8\x9e\x80\x1d+\xb5~|D\xf2@\xa1\x81\xb2\xc8C\x1agJ!\xb5D+$\x1d\xbb\xdb6\xa2Wm\x14\xc0\xcf(\xb8M@\x94F\xcd]\x9d2VG\xe9\x19D\xc2yL\x13E+eg\xb01S\x95 }\xf1G\xafc\x04\x9c\xdd\xe8\xdf]\xd4\xfd\x8c\xe6\n!A\xed\xd4k`\xf3\x8a\x8c\x0bL\x14\x18\x87\x06\xbc1\x98\xd8\x95\xb5n\x92\xb4\x18\xe2\x8fu\xe3\xf9h\xbep\x11\xf8`\x93\xa2Q\xd3-\x9b\xceT\xb3]\x14\xac\xf8\xca\xe0\xe2\x07}H\xedn\xdav\x8cbh\x0c\x06\x1eKh4+\xd5Y+xa\xec\xf1\xbe\x05f\x17T\xa4\x0b\x19\x11\x8d\x12\x86\xea\x14\xa1\x88\xe7\xd6\xce\x84oS\xe45\x8f~\x92F\xe6\'y\xf4A\x1a-\x8a\\\x00h\xfd\xcc\xea\xba(FC\xf3d\x04$\xcc\xe4\xaa\x7f&x\xbdO(pOaG_u\xbc\x1d\xcd\xeb\x85\xbf\x1e7\xa3=\xb4\xf6l/D\xd2\xf1\xbd\x86\xdd\x9a0\xee%-7X\x8b\x1a\x7fN\xbd4R\xd1]j\x12FM\xcb\xd2Xf5\x7f\xb6\xb8\x04\xdd\x89\xd6\xa067V!\xc0\xe9\x92h\xd7\xe2w4Z\xe9\xcc\xcf[\xa9\x8f;\xa9\x19K%\xb7\xba\x91ak\xf1\xb8\xb4\x9ds=\x8c\xf6\x16Bg\xec\x96M\xf2\x05\x85\xbe\x84\x18g\xd55\x7f-\xd7\xaf\xc7w\x8c\xa8\xaa\xbb\x922!kA^\xe7~\x04\x91p\x96Q\x99\x8e\xd6\xf3\xdcP8\xbd#\xd7\x8e\xd6\x83{\xb4\x1cm\x8b|\x89I\x9f\xa0\x96\xf9\x19l}\x8fZf\xc3Vo\xfel\x8c)\t\x9c\xa5\x12\xd7\x99YJ\x87\x1e@S^_S\xec\x80\xec\xeb\x7f]\xb2_\x8f\x0e\xe7\x93\xd9\xf4}T\xb7s\xa0\xd1H\xd0\x84^=\xd6\xac~\xb9\xbc\xb2m\xb4nn\xd9N!I\xb4\xf3\xf9e\xd7d>n\x9b~\xdf5\x99wm\x93\x94\x94\x80x-\x13\x89\xd8\x00\x9a4\xab\xf6bu/\xea)\xd7\xf3\x1d\x85y&! \xcb\xfa_\x83\xff\xeb1\xae\xaf\xe0\xc4\x80\'\xfd\x1dAX\xaf\xe1\xbeCY\x13\xe7\x0cf-\xdc;\xe0\xef\xe1nn\xf1\xfe9\xd1\x17\x01\xff\x10\xee\xe6\xd3\x84x\x0b\xf8\xe7`\xde\x0b\x8d\x9d\xb6\xf7\x80\x87\xc2|J\xf2\xcb\x807\x7f\xc9\x08P\xce\xd92\xec\xd9\x9c\xd6I\'g\x8d\x1a\xbek#4Rq\x83\xc0\xac6\xd0`\xcc\xa2\x83^\x0c\xad*\\\xd7X\x87c4^\xa9h\xe5\xcc\xc9G\x8dwy\x98\xc3\x0c\x91\xcc\xbc\xecH\x89E\x1cU\xb5w{\xc1\xa0YK\xce\xdf\xb5\xa7\xe6\xac\xab\xcc(\xf9\x84yh\xdc\x07u\xb5\xdd\xcb&=\xc1\x14K\x9b4\x93\xeeI\x8eR\xe8s\xe64\xaeHd\xca\x9f\x85p\xaf\xd6\xe6\xe8{t\x87\xf3\xdb\x1c%\xff\x18\xba\xcdoG4\xdd\xb2\xd0\x17pD\xccD\x93u\x1a2\x9c\x9b,j\xcbh\x9b\x97\xe4\x13\x86\xec\xab\xb7\xc6\x14\xa3\xfb\n\x95\xfa\xefN\x1aP\x9fi\x13\xb8\x89\xd5\xce\xaeUs\x80\x0e\xa8\xa8\xce\xabfw+g\xaf\x92\xe9g\xd4+\xeb8\xbd\xe2\xe4i:n1:g\xe7\xd4\xcdi+=\x85\x1dqV\x92n\xe2 \xd1\xdd\xa8\x10\x04\x00\xabSMm\xa6\xfb\xd7\xc2\xb3+\xef\xdae\xd5\x11@A\x8anCc\xf6\xe20)\x91\xd1\xb3\xeeGT/f^WK\xaf-\xe3z.{q\x15\x8bos\xd7\x9c\x7f\x16\xa6\xe6Oq\xddi#\xf5}\xb5\xe4\x91z*I1\xbb\x04\x07~\x04}\x8f\x95t\x7fJ#!\xd2}\xa4\xd3\xc4!\xd7>\x18\xc1\x98\xa7[\x15\xfa?\x02w^\x81\xabI^\xba=-l\x84/\xd2\x93\x8a\xc1\xed\xbar^\xb7\xdb\x83\x0c\xee\xb3\xea\x9a\xde\xd1\xc1\xe2\xec\xa2\xed\xe0\xd1\x0b\xce\xd7\xbd\xb9\xa0\xff\xdc\x91\'#\xc6\xe1L\xb3\xe7?\x0ct`\x0c\xe3\x11\t\xad\x0f\xea\xffA\xde\xe0\x0e\xebf\x16\xcb\x14\x99k\xc5\x80\xcd\xf6\xe6\xb2\x13\xdb\x8ar\x10\x8aI\xa4\x02\xe4t0\x1c\x97\xba\x18\xbe\x08v\x18B\xee]H\xb1\xba\xc4\x1c\xc9T\xd6t\xb8\x1f\x01\xbf\x17w\x84\xee\xb3;\x96\xd4\x0c\xee7rC\xa7\x9c\xe2\xe9\x7f<\xb5?\x05\xb2\x14z\xe4\xf1\x936\x9ci)\xc8\x948\xe8\x01S"\x01\x87\xbef\xa0\x84\x15\x1d\xa1x\x86 r\xce\x17:5K\x02\x0f\x00\xac\x0c\xf0H\xc7\x8d\xd2\x93\xfe\x99+M\x98\xb6yi\x85\xebYF\x99<SB\xd4<\xa5\x0f\x0cpL\xa2_\xf7.s<p\x8f\x87\x1b\xe9\xb3`\x0401\x97\\\x8fo>QOJ\xc9\xb7\x85\x99`\xd2d\xad\xd8a\xd0\x1dAJ\xca\x93\xf1\n\xf0\x82\xf1\xc6dQ\xb3W-\xf2\x8e\xc18\x19\x1ce\xec\xae\x96\x01\xc9\xaeD\xd1;\xad`\xa3\xee0\xf2HW\xcduy\x03\\M&zU\xc0\xcf\xa0\xd0\xe2Co\xfa\x02;\x9f/\x81\xa6\xbeE\x01M\xe5\xb8\xb4:\xafaH\x05K\x87\x9f\xad\xe6\xa7!\xee$!\xa8?\x88\x07\xa6\xb32\x98\xc2\x02#\xc7\x88\xa7%\x1c+\xbb\xc9ls\xe8\xb6\xaa\x0c5\x05\xde\xf13^\xa68O\xccV%(\xe8\xb50\x1a\xf5D\xb3\xbb\x03p\xae(\x83G\x96\xa7\x10\xeb.\xc4>\xe9\xbd\x83\xc7LG^\xdf$\x8dN,\xc5\x93\x81\xcfIw\x1aC"\xcf\xb5+JN\xadBf\x14\xc1\x85\xf7\x13\xf5%~u\xa2\xff\xee\x82\x04F\xa34\xea\x0b\xb5]=\xd4<\xc7\xdb\x958\xc0\xa4D\xd3\x0e\x12\xb7G!\xe4\xe4\x91$\xb4V\x8fp\x8cj.\xbd\x83\xbe\xe8\xee\xd9\xe7\x81%\xb2\xd7b\x05\xb1=\xd5\xc0w\xcfBP\xbeJ\xd3i\xbeopS\x06F\xcd\x95&\xee\xcf\xfe\x12\x82\xfb\xd9m\x03\xde8\xa9\x1d\x98\xadC/\xcd\xee\xbd\xca\xa3\xb2&\xb3j\x92\x9d\xd3\x85\x88B"\xa6\xcb`\x83\xbe\xedv\xcd*\xaeY\xa7\x95\x92`f\xf8&\x9e@"`\xdb\xbb\x16\x00"j}\xe0J \xbe\x82\xf4\xe0\x1dA\x83_\xf4\xff\x8fdj\xc0\xf4\x04f$\x0c\xc4\xf8\xed\xb5\xafY9\x04}[J\xde\xf6\x8ep\xf4\x18va\x14O\xd2{{\xc0\x97\x8e\xcc\xe65R\x033\x865I\xdf\xb1\x971\xf2Yo:\xb0<\x85b9-\xb5|\x11\xa9\x84\xf6J(\x06\xc5\x02B\x8e\x14\xe8\xba\xf4\xc5\xbeT\x101:}K\x8f!L]^\xe8\x82\xb0\xcat\xb5\xa1_q\xbd\xd2\xf34\xd0\x9a9TcL\xcabl`*\xb5\xba\xff\xcclN\x0b\xec\xa7\xbe\x15%XD\xff\x99@w\xb4t{wiY\xb7\xf5\xac\xedo\xf7\xce\xbd\xc7u\xd6|\x1d\x9a\x83\x0e\xb3\x0c\xf4\x89\x88\x18\xe5|%\x8c>\xbb\xb3\xd5\xe1X\xce\x96O\xdbn\xbf_O\xe8\x0b>\r\x8b\xb4\x9bt&\xa4sx\xa0-v\xc8d\xd3q\xb2j\x8f\xact\x93\xe5w\xac\xa2\xb2\n\x1a\x12\xabh\xf1\xb4\xa4W\xde3\xed\xf9R\x85\xb9K\xc7\xc5\xb4_\x7f\xfb\xf6\xa6\xddMq4\xab\xaaY\x06b\n\xfe\xd3\x11Z\xf7\x91\xcf\xd7\xd7\xc9\x0c}\x1b\xa2\xed\x0c\x0c\xce\xb6\x0fa\xe5\xd4\xfbEV|\xa3\xffA\x11I"O\xd2\xa7y\xd9t\xafj\xde\x1b\xd5oqa\xbb^\xa5%\xe5\xac\xbe\x9c\x8dh\xa6\xc9\xdb\xda\x8d\xb4\x11\xd9\xedlC\xdf4\xbb\xad\x92>\xf6\\\xca\xc0h|\x13\xea"6/\x96\xf0ok\xbc,\xf1\x958\xedz\xe3w\x13\xbdl\'hE\xff\x88\xcd\xf1\xc4\xe6|\x11\xf3Fl\xde{l\xbci\xf5\xe01\xf7\xa8\xd15{?\x92\x9awf~\x10\xe8\xc9\xcc\xaf\x02\xbd\xc8n\xde\x99y|j\xe6G\xa1\x08l\x96\x05\xf0rI\xb3\x82|\xa6\x92\xd4\xc1\xa7b\t\xe3x\xd0\x19\x8f\xc3G\xa1Zfr\xce\x16,\x0c\x0e\xb8&\x0c\x89\xe4\xf2\x8e\xb3\xc0\xe5p\xe8\xbf\xf2\x805t*Z\xed\xa7\x19g\xb8Z\xd0\xef\xec\xa4\x8a\xbe\xd3\xd7bJ"\xfe\x17\xbb\xbf\xdf\xb9m<9\xfe\x00\x00\x01\x84iCCPICC profile\x00\x00x\x9c}\x91=H\xc3@\x1c\xc5_S\x8bR*\x0ev\x10q\xc8P\x9d,\x88\x8a\x88\x93V\xa1\x08\x15B\xad\xd0\xaa\x83\xc9\xa5_\xd0\xa4!Iqq\x14\\\x0b\x0e~,V\x1d\\\x9cuup\x15\x04\xc1\x0f\x10W\x17\'E\x17)\xf1\x7fI\xa1E\x8c\x07\xc7\xfdxw\xefq\xf7\x0e\x10\x1a\x15\xa6Y]c\x80\xa6\xdbf:\x99\x10\xb3\xb9U\xb1\xfb\x15\x02\x82\x08!\x8c\x19\x99Y\xc6\x9c$\xa5\xe0;\xbe\xee\x11\xe0\xeb]\x9cg\xf9\x9f\xfbs\xf4\xaay\x8b\x01\x01\x91x\x96\x19\xa6M\xbcA<\xb5i\x1b\x9c\xf7\x89\xa3\xac$\xab\xc4\xe7\xc4\xa3&]\x90\xf8\x91\xeb\x8a\xc7o\x9c\x8b.\x0b<3jf\xd2\xf3\xc4Qb\xb1\xd8\xc1J\x07\xb3\x92\xa9\x11O\x12\xc7TM\xa7|!\xeb\xb1\xcay\x8b\xb3V\xa9\xb1\xd6=\xf9\x0b#y}e\x99\xeb4\x87\x90\xc4"\x96 A\x84\x82\x1a\xca\xa8\xc0F\x9cV\x9d\x14\x0bi\xdaO\xf8\xf8\x07]\xbfD.\x85\\e0r,\xa0\n\r\xb2\xeb\x07\xff\x83\xdf\xddZ\x85\x89q/)\x92\x00B/\x8e\xf31\x0ct\xef\x02\xcd\xba\xe3|\x1f;N\xf3\x04\x08>\x03Wz\xdb_m\x00\xd3\x9f\xa4\xd7\xdbZ\xec\x08\xe8\xdb\x06.\xae\xdb\x9a\xb2\x07\\\xee\x00\x03O\x86l\xca\xae\x14\xa4)\x14\n\xc0\xfb\x19}S\x0e\xe8\xbf\x05\xc2k^o\xad}\x9c>\x00\x19\xea*u\x03\x1c\x1c\x02#E\xca^\xf7ywOgo\xff\x9ei\xf5\xf7\x034\x14r\x8e\xa7\xf8\x11\x8b\x00\x00\r\x1aiTXtXML:com.adobe.xmp\x00\x00\x00\x00\x00<?xpacket begin="\xef\xbb\xbf" id="W5M0MpCehiHzreSzNTczkc9d"?>\n<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="XMP Core 4.4.0-Exiv2">\n <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n  <rdf:Description rdf:about=""\n    xmlns:xmpMM="http://ns.adobe.com/xap/1.0/mm/"\n    xmlns:stEvt="http://ns.adobe.com/xap/1.0/sType/ResourceEvent#"\n    xmlns:dc="http://purl.org/dc/elements/1.1/"\n    xmlns:GIMP="http://www.gimp.org/xmp/"\n    xmlns:tiff="http://ns.adobe.com/tiff/1.0/"\n    xmlns:xmp="http://ns.adobe.com/xap/1.0/"\n   xmpMM:DocumentID="gimp:docid:gimp:3711da64-a25a-4258-a9ef-52016ca0bbd4"\n   xmpMM:InstanceID="xmp.iid:6c03ef4b-d7ff-4ea1-9da3-82497530ebac"\n   xmpMM:OriginalDocumentID="xmp.did:d64957e6-3ff0-434e-a496-45f040e99b67"\n   dc:Format="image/png"\n   GIMP:API="2.0"\n   GIMP:Platform="Linux"\n   GIMP:TimeStamp="1675401212506179"\n   GIMP:Version="2.10.30"\n   tiff:Orientation="1"\n   xmp:CreatorTool="GIMP 2.10">\n   <xmpMM:History>\n    <rdf:Seq>\n     <rdf:li\n      stEvt:action="saved"\n      stEvt:changed="/"\n      stEvt:instanceID="xmp.iid:79b00753-6bb6-40fc-9664-3ad2cba33c9a"\n      stEvt:softwareAgent="Gimp 2.10 (Linux)"\n      stEvt:when="2023-02-03T15:13:32+10:00"/>\n    </rdf:Seq>\n   </xmpMM:History>\n  </rdf:Description>\n </rdf:RDF>\n</x:xmpmeta>\n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                                                                                                    \n                           \n<?xpacket end="w"?>F\x9d\xcd\x96\x00\x00\x00\x06bKGD\x00\xff\x00\xff\x00\xff\xa0\xbd\xa7\x93\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\x07tIME\x07\xe7\x02\x03\x05\r \'\xeb\xe1z\x00\x00\x145IDATx\xda\xed\x9dk\xac\x1c\xe5y\xc7\xff\xef;\x97\xbd\x9c\xf59>\xc7>\xe7`\\S\x1c\x84\n\xae\xd2\xe0P\xa7\xa2jK\x9d\x14\xa9\x95 UJ\x11\x97\xb6\x11\x944RP\x15\x9aP\xa2"$T!\x15E\xb4\xa8M\x1b\xe5\x1bR\x1b)Q\xfb!E\xbd\xa8V?PJ\x04\x82\x00\x15\x92\r\xb6\x89\xed\x831\x9c\x1a\xd7\x97s\xd9={\x99\xcb\xfb\xf4\xc3\xce\xcc\xbe3;\xbb;3\xbb>\x1c\xf0\xf3\xb7F\xbb,\xb33sv~\xfb\xcc\xffy\xdeg\xde\x05X,\x16\x8b\xc5b\xb1rKLrcD$\xf8#e\x8d\x84N\x08\xfa\xc8\x01\x0e`\x15\xdavDb{\x0c3+\x86\x8c\xf6\xd8\xf7\xbc(\xd4\xa2\x00\xb4\xe1\xfbd\xb0$\x9f\x0b\x06\x985\x02^\x02\xa0\x82\x85\xb4G\xca\x0b\xb2\xc8\to\x08\xab\x11<\x9a\xda\xf3$\xc4\x0c0+\r`\xa5-~b\t_\xcf\x1c\x91E\x0exCp\r\x00V\x00o\xf8h\xde{\xef\xbd\x9f!"\xf3\xe8\xd1\xa3\xfb\xa4\x94\x0c/\xabO\xf3\xf3\xf3\xcb\x0b\x0b\x0b\x17o\xbb\xed\xb6\xf7\xee\xbf\xff\xfe\x0b\x00\xbc`q\xb5\xe7!\xc84\x11\xafLD\x92\x88L"*\x11Q\x8d\x88f\x89\xe8\xaa#G\x8e\\w\xd3M7}kvv\xf6\xbf\x84\x10\xad\xc4\xe5\x81\x17^\x86.\xd5j\xf5\xad\xbd{\xf7~\xe7\xf1\xc7\x1f\xffe"\xba\x9a\x88v\x10\xd14\x11U\x88\xc8\n\xb8\x13cE`"\x92\x9aU\xb0\x00\x94\x00\x94\x0f\x1c8p\xd7\x91#G\xfe\xc4q\x9ck\x84\x10\x90RB\x7f\x14\x82\x030+\x95\'\x10\x11\x94R\xd1\x02\xa0\xbdg\xcf\x9e\xef?\xfd\xf4\xd3\x7fw\xf7\xddw\x9f\x07\xd0\x06\xe0h\xd1xh$\x16\x19l\x83\t\xc0\x06P~\xe9\xa5\x97f\xef\xbc\xf3\xceo_\xb8p\xe1KRJX\x96\x05\xdb\xb6a\xdb6,\xcb\x82a\x18\x0c0k(\xc0\xbe\xef\xc3\xf3<\xb8\xae\x0b\xc7q\xe08\x0e<\xcf\x83m\xdbg\x1ez\xe8\xa1\xfb\x9fy\xe6\x99c\x01\xc4\x9d\x10b!\x84\xca\x05p\xc2\xf3\xda\x00*\x87\x0e\x1d\x9a\xbf\xeb\xae\xbb\xfe\xb1\xd5j}\xda\xb6mT\xabU\xd4j5l\xdb\xb6\r\xbbw\xef\xc6\xae]\xbb \xa5\x8c\xbee,V\x1flAp\xf3<\x0fg\xce\x9c\xc1\xf2\xf22\xea\xf5:666\xd0\xe9t\xa0\x94\xaa\xdfq\xc7\x1d\x0f<\xf7\xdcs/\x03h% \xa6<\x00K-Y+\x03\x98\x9a\x9b\x9b\xfb\x87\xf5\xf5\xf5\x83\xa5R\t333\xd8\xb9s\'\xf6\xed\xdb\x87\x1bo\xbc\x11\x95J\x05\xbe\xef\xc7\xe0e\x88YIx\xc3G\xc30`\x9a&Z\xad\x16^}\xf5U\x1c;v\x0c\x97.]\xc2\xc6\xc6\x06\x88\xe8\xd2c\x8f=\xf6\xc5\'\x9f|\xf2D\x02\xe2T+!\x86D\xdf\xd0\xf3N]\x7f\xfd\xf5\xdf\\ZZz\xa4\\.cvv\x16\xd7\\s\rn\xbe\xf9f\xec\xde\xbd;\xba\x04(\xa5b\xd0\xe6\x01\x98a\xff\xf8\x02\x99w\xdd0W\n-\xa8i\x9ax\xf7\xddw\xf1\xe2\x8b/\xe2\xdc\xb9sh4\x1a\xb0m\xfb\xedS\xa7N\xdd\xb1\xb8\xb8\xb8\xa6y\xe2\xd4(l\x0e\xd8g\x14\x81\x9fx\xe2\x89\xbdKKK_\xb7,+\xb2\x0b\xb7\xdez+j\xb5\x1a\x9a\xcd&<\xcf\xeb\x8b\xbe\x0c-\x03=La\xb2\xef\xba.J\xa5\x12\xf6\xee\xdd\x0b\xdb\xb6q\xe8\xd0!x\x9e\x87f\xb3\xf9\xf3\x07\x0f\x1e|\xf0\xe8\xd1\xa3\xdfM\x96\xd6\xb2\x00\x1cK\xde\x9e}\xf6\xd9\xaf\t!\xacr\xb9\x8c\xb9\xb99\xec\xdf\xbf\x1f\xb5Z\r\xadV\x0b\xae\xeb\xc2\xf7\xfd0\x9b\x1c\x0f\xd6\xc4:\x0c\xf8\x16\x87s\x04\xb0\xc3\x80\xf6}?Z\xa7\xd3\xe9\xa0V\xaba\xcf\x9e=\xd8\xb7o_\xc4\xd5\xc9\x93\'\xbfr\xee\xdc\xb9g\x17\x17\x17\x1dt\xeb\xc4\x92\x88\xfal\x84\x99b\x1f\xa2\x04\xee\xe5\x97_\xdev\xee\xdc\xb9\xdb\r\xc3@\xb5Z\xc5\xd5W_\x8d={\xf6\xa0\xd3\xe9\xc0u]x\x9e\x17+\x8d\xf8\xbe\x0f\xc7q2A\x9d\x84\x96q\xfd\x18\x01]\x00f)%L\xd3\x8cU\xab\x88\x08RJ8\x8e\x03\xc30p\xc3\r7\xe0\xc4\x89\x13h4\x1a\xa8\xd7\xeb\x8b\xf7\xdcs\xcf\x17^x\xe1\x85\x7f\r\xdc\x80\x97\xb6ms\x80}\x90\x00\x8c\xa7\x9ez\xea\xb3J\xa9\x99r\xb9\x1c\x01\xec\xfb~\x1f\xbc\x00\xe08\x0e\xd6\xd6\xd6";1\x14\xe00\xd1c\x16>Y0\x07U\x06\xdd\xe7\x86\t[\xf8z\xc8L\x18\xa1\x95RQYmvv\x16;v\xec\xc0\xc5\x8b\x17\xd1l6\xf1\xce;\xef|\x1e\xc0\x7f \xde\xa2@\x99=\xf0\xa9S\xa7\xf6\x0b!`Y\x16*\x95\n\xa6\xa7\xa7\xe1\xfb~t\t\xd0/\xf3\xcdf\x13\xbe\xef\xe3\'\xaf\xfe\x18\xef\x9d\xf9\x90\xcf,\xabO\x95\xdav\xfc\xd1\x1f~\x19\x86a\xc4\xd8\t!VJaqq\x11\xa7O\x9f\x86\x94\x12\xab\xab\xab\xfb\x11\xef\xb3I\x055\xf9\x85\x8alD\xbd^\xbf:4\xdd\xa5R\t\x96eE\xd5\x06=\xc2\x12\x11\xda\xed6|\xdf\xc7/|\xe6\x00\x9f)\xd6\xc0\xe4\xcd0\x8c\xd8xA\xc8R8\xc8a\xdb6L\xd3\x0c\xad\xc5.\xa4w:\x8eL\xe2\x04\x00\xe18\xceLx90\x0c#\xfa\xb6$+\x0e\xfa\xf0 \x8b5H\x1b\xeb\x97"\x80]\xd7M\xe5\'\xf4\xc5A\xb27\x83\x11\x9d\x8dfV\x9f\x1e\xeeH_b\xffO)\x10\x03\xcc\x1a\xa1\xd0\x0f\x0fc+Q\xc5\x18\x9a!\x9aY\xfc\xb9\xbe\xc3\xb4\x04\x8d\x88bm\xf6,\xd60\x80\x93\xf9\xd3\xa0\xa0\x98%\xa8\x9ayv>p\xa4-\xdc9\xd7nY\x19|p\xc8\x0c\xb2\r~\xe4\xb6\x10"\x0f\xc8\xb1\xff\x16\x82!f\x8d\x048-\x87*\xda\x04f\xe6}C_\xb3N`\x1f\x18\\V&\x80\x85\xe8\x8d\t\xa74~\xe5\x85X\x16\x857Z\xc2\xd79\xfa\xb22\x19\x02\xd1ci\x02\xed\x03\x85#p2\xfaR\xa2\x1b\x8d\xc5\x1a\x00P\xd7\xa3\x12\x81\x82\xa07N\x0fy\xee$.\xcd\xafp\x15\x82\x95\x99!\x00J/\x97%\xd8\xba\xec\x11X\xff&\x85\x07\xc4\x15\x08V.n\x12y\xd38W\xeeB\x16B\xf7\xbf\x11\xc4\xf9J#\xac+8\x02\x87AO\x00 \xad\xc1\xa7\x08\xc8\x85\x928\xe8v!\xf0\xbf \x82\xe2(\xcc\xca\x1a\x00\xf5\x96\x841"q\xee\x08\xac\x8fY\xebV\x82\xc5\x1a\x07\xea\xb4\x1e\x9b\x89G\xe04?\x13u\x14\xf1\xdd\xc8\xac\xacW\xf1\xc4\xfc\x10\xe3(W\x04\xd6\xbf%\xd1\x8euC\xce\x00\xb3\xb2\x06\xbd\xe0?\xc5\x98\xc1O\x16=\x88$\xbc\x1c}Yy<\xb0^\x8d\xd0\xa3\xf2\xa6V!B\x88\x95~ ,V\x06~\xc2\x84_\x10\x01cL\x88c\x16\xdd9)\x15\xabD\xb0XEU4\x81+\x14\x81\x87\x19s.\xa3\xb1\xf2^\xc1\t\xdd[\x8e7%\x89K\x1e\x00%}\r\x8b5\x8a\x9f\x90\x17\xa5\xa2\x1b%\x86\xdd\xe93q\x0b\x11\xcb"\xf5\xe1d\xb6\x12\xac\xacU\x88$/cT"\x8aw\xa3%&\xf2\xe3(\xcc\xca\xc3\x8f~\x13\xc48\xfd\xc0\x85\xbb\xd1\x94>\x12\xc7\xa3r\xac\x1c\x118*\xa1%\xda)7\xa7\n\xa1[\x89\xa4\xb5\xe0\xd3\xc3\xca\xea\x81\xc3\xbe`!\xc6\xaaf\x99E\xbeAz\x02\xa7{\x1a\x06\x98\x959\x08&<0}$\x1eX\xbb$pO0+\x8f\rEJ\x15\xab\x08=\x13\xf1\xc0\xfa\xd0 \x8b\x95\xf5*\x8e\x14\x0f|\xf9\xcbhi\x9e\x97o)b\xe5\xf0\xc0}7s\x8e\xb1=\xb3\xc8\x01$=\xb0\x1a\xa3\x19\x83u\xe5E_\xa51#\x00@\xca\xc2W\xef\xfc\x16"\x1c\xb7\xd6{!&\xf0Mb]A\x118\x8c\xc2A\x05B)\xd5\x85\xba@o\xb0Y\xf4\x00\xd8>\xb0\n\xfb_\xcdJ\x08\x1d\xe8\x02\x9aX?0\'q\xac<yT\xf2\xae\xf6\xa2\xed\xb8\xe3\xf7\x03\x03\x91\xa7a\x0f\xcc\xca\x9aC)\xa2n/\xf0fz`\xa5T|r6\x9e\x17\x8dU\xe4\xea\x9d\xf8\x8d\x14\xd2<\xf0e\xbf\xa9S\x0f\xf74\xc8\x17\xb3X\xc3"0\xe2\x93\xe1lj\x19-\xd5\x94ksC\xb0Xy-(6{n4\x9e\x17\x825\xae\xc2F\x9e$\xd4\x97u$.\x8b\xad`\xb1\xb2\\\xb1c\x03\x19fq\x0c\x8b\xcfN\x19\x14\x9dc\r=|zXy\x129m \x83\n\x0ed\xc8"\x00\xebf<\xf9\x9c\xc5\xca\x94\xc4%\xec\xe7\xa6x\xe0\xbe\x9dM`b\n\xd6\x15\x06p\x90\xec\xa7\xddF\xf4\x91Ml\xc2b\xe5\xcb\xe0Dj\x12W\x04\xe2\\\x16B\xffu\xc5\xb4$\x8eafe\xb2\x10aGZ\xca\xe4~\x83\x18\x9bH\x04v\x1c\x07\x96e\xf5\x1b\xee1:\xeaYWZ\xfe\x96\xfe\xe3.!S\x9e\xe7]\xbe\x08\xdch4R\xc3<\x83\xcb*\x12\x85\xd3\x96f\xb3y\xf9\x00^[[K\xddi\xac4\xc2b\r\x0f\xc1C\xf9\xf2}\xff\xf2Y\x88z\xbd\x0e\xc7q\x06z`\xaeB\xb0\xf2D\xdf\xa4\x85\xf8\xf0\xc3\x0fso/W\x04VJayyy`\xf8g|YY}pr\xf1<\x0f\xcb\xcb\xcb\x97\x17`\x00x\xef\xbd\xf7b\xd3a\xf2\x94R\xacq\xe1\x05\x80\xd3\xa7O\xe7N\xe0\n\x01\xdcj\xb5\xb0\xb4\xb4\xc4\xf0\xb2&"\xa5\x14\x1a\x8d\x06N\x9c8Q\xe8\xfd\x85F\xe2N\x9e<\x89\xb9\xb99l\xdb\xb6\x8d\xcf\x00k\xach\xfc\xe6\x9bo\xc2q\x9c\xc2?\xf6R\xe8\x9e8\xcf\xf3\xf0\xc6\x1boD\t\x1dGcV^\x0b\xe1\xfb>\x0e\x1f>\x8c\xb3g\xcfbee\xa5\xf0\xf6\n\xff\xcc\xd6\xc6\xc6\x06^\x7f\xfdu8\x8e\x83f\xb3\xc9\x00\xb32\x03\xec\xba.^{\xed5\xbc\xff\xfe\xfbcoo\xac~\xe0\x95\x95\x15\xbc\xf2\xca+p]\x17\xd7^{-fff\xf8\x0c\xb1\x86juu\x15\xc7\x8e\x1d\xc3\xc5\x8b\x17\'\xb2\xbd\xb1\x1b\xda\xeb\xf5:\x00\xe0\xf8\xf1\xe3\x98\x9f\x9f\xc7\xc2\xc2\x02\x9f%\xd6@\x1d>|8\xf7`\xc5e\xb1\x10i:\x7f\xfe<\x9f!\xd6\xa6J\xf2G\xc0b\x80Y,\x06\x98\xc5b\x80Y\x0c0\x8b\xc5\x00\xb3X\x0c0\x8b\xc5\x00\xb3\x18`\x16\x8b\x01f\xb1\x18`\x16\x8b\x01f1\xc0,\x16\x03\xccb1\xc0,\x06\x98\xc5b\x80Y,\x06\x98\xc5b\x80Y\x0c0\x8b\xc5\x00\xb3X\x0c0\x8b\xc5\x00\xb3\x18`\x16\x8b\x01f\xb1\x18`\x16\x8b\x01f1\xc0,\x16\x03\xccb1\xc0,\x06\x98\xc5b\x80Y,\x06\x98\xc5b\x80Y\x0c0\x8b\xc5\x00\xb3X\x0c0\x8b\xc5\x00\xb3\x18`\x16\x8b\x01f\xb1\x18`\x16\x8b\x01f}"d\xf2G\xc0\xdal\x89`\x19w\x1d\x06\x98\xb5\xf9\xf0\n\x01\x04\x8b\xd0a\x8d^\x16\xb1u\xd8B\xb0\xb6\\\xf4M>\n!\x10\xfec\x0b\xc1\xda\xe2\x11\xb8\x07m\x7f\xf4\x8d\xdb\x07\xb6\x10\xac-\x18\x81E\x0f\xce\x10f\xedU\x1d\xde\x0c\x0e\x82\x01fm\xbe\x87\x10\x02\x90\x1a\x9dQ\xf4\x15=\xb0\xbb\xcf\x05\x03\xcc\xdazI\x9c\x14"\x16]\x85\xfeO\xa4\xaf\xc3\x00\xb3\xb6\x84$\x04\x08"\xf2\xc0z\x04\x16\x1a\xd0Y]0\x03\xcc\xda\xfc*\x84\x0ek`v\x85\x10\x90QE\x82\x938\xd6\x16\xaeB\xc8\xc0"\xc4#\xb0H<r\x12\xc7\xda\x8a\x16B\n(\x85\xb8\x85\x08M\x83\xd0\xcbjq\x9b\xc1\x00\xb3\xb6L\x12\xd7M\xd2\xfa_CJ9\x8d\x01fm)\x19\xd2\x00I\x15\x1b\xc8\x80\x16q\xa3A\x0e\x8e\xc0\xac\xadi!$\x0c)\x13\x1e\xb8\x9b\xc0I\x91\xb4\x11\x1c\x81Y[L\xa6\x94\xa00Q\x0bMBd+D\xac\xa4\xc6\x16\x82\xb5\xf5,\x84!\xa1|\x03R\xab\xa5\x85\x9eX\xf7\xc1Y\x9b{&\x02p4\xfc\xc7b\x8d\xb2\x10BB\xc8\xa0\x8c\xd6\x0b\xc0\x90\x01\xb02\xf4\xc2\x89R\xdb\xc4\x01\x16\x89\xcc\x92\x82\xd7~z\xe1->K\xac\xe1U\x08\xed\x11\xd1@F\xd0\xdb\xabA\x8dq=\xb0\xde\x15\x94\xdap\xac\xad\x13^\x11vTl>K\xac\xc1"\x05(\x15\x94\xd1DT\x81\xe8E\xde.\xc8\xe12^\x04\xd6\xdb\x84bMo\xfd\x118\x84\xf9\xb5\xff>\xc1\'\x895P\xbe\xef\xa3^_\xef\xd9\x03\xd1\xf3\xc02\xb0\x12\x08\x1b\xdc\'a!b\xb0\x8ad\xf3\xb1\xe8q\x1e\x99t\x03\x9e\xa3\xf8L\xb1R\xe5t\xda\xa8\xaf\xaf\xa7X\x08\x11\xf5E\xc8I\x8d\xc4\t$\xbb\xe3\x13\x19\xa2\xd6\x90\x0ctk|\xa6i\x02\x8e\xcbg\x8a\x95\xaa\xb3\x1f|\x00\xdf\xf7\xa3\x08\x1c\xf5\x01\x87\xf0b\x82\xcd<"\xb1\xa5>?\xacE`\x00 Rp\x1d\x87\xcf\x12k\xa0<\xcf\x8d\xaa\r\xba\x05\x95\xe1\xf0\xb2\xd0\xaf\xf4cG\xe0xEN\x00\xb1\xa2s\x9a\x07f\xb1\x86I\xc6X\xe9\x95\x1c\xc2\x0e\xb5\xa8\xa52\xf0\xc4cG`=\xc4\x87\x10K\xcdBt\x0fJ7\x1d,\xd6h\x80c\xc4\xc4F\xe2\xfaB\xe68I\\\xdc\x05\'\xfb5\xf5H\xcd\xfc\xb2\x8a\x00\xdc\x0b\x94\xbd\x9b\xe2\xa4\xb6\x8c\x9d\xc4\x85\x1b\x8a:\xe7\x91n!\x98]V\x16\xa5\xd9\xcd\xdePrX\xfb\x9dT7\x9aH\xc4b\xa1\x03-\xb4oU_,f\xb1\x06D\xe0d\x96\x15<FAQ\x046u\x02w%Gc\xd2\xd0\x1e5\x93-\x86\\\x16X\xac\xec\x16">\x12\'\xf4\xba\xf0\xb8\x16B\xbfS4\x84X\x0e\xa8B\xb0\rfe\xb5\x101V\xc2f\x9e\x18\xc4\x13\xe8\x07\xd6\xebs\xfa]\xa4\xc9:\x1eG`V>\x0b!R\xae\xf4\x83f\xeb\x193\x02\xeb\x85e\x89^}\xae\xb73\xddN0\xc8\xac\x11\x11X\x1b\xc1\x85\xe6\x7f{\x8d<\xbd\tN\xc6\xaeBH\x88h\xd1\xbb\xd1b\x16"9M\x10\x9f#V\x16\x0f\x9c\xbc\xa9Sk\xde\x89Fy\'R\x85\x10\xbam@\xac\xe1X\xa4\x00\xccb\x15\xf2\xc0"\xac<\xf4\xcf\xd4\x93\x17`\xd2\xfd\x8a\x8c\xfa\x7f{\x1b\xd6#p\xac9\x99\xc5\x1a\tp?\x98B\x1f\x81\x13\x13\x9c^U\xdfP\xfcV\x8ft3\xceb\x15\xf3\xc5\xbd\x99 \x84\x88/A@\xa5"\x00\x93@lCQ\tM$n\x8b\x0e\xbd\x04\xe3\xcc\xca\xec\x81\x13\x118\xba\xa5\x9e\x06\xce\x0fLy\x00&@o\xe6\t\x87\xf6$\xa4\x94Q\xcd.V\xa9\xe04\x8e\x951\xda&\x9ft\x83\xa2\x80\x0c(&B\xe6\x9b\xe2\x06y`\x02@v\xa9\xb4\x06\x02H)\x90"H#\x98\x94\xa2ob\n>1\xac\xfcI\x9c\x9eCI\r\xe40\xd8\x9a\x86\xb1\x06@\r\xb3\x10r\x10\xbc\x00\xd4\xb6\xda\xb6\xff\xednO\xc1w\x1d\x18\xa6\x01CJ\x18RD\xb3\xab$o\x83\xe6\x8a\x04kd\x12\xa7\x15\x03\xa2\xe4\xcd\x90\x8155\xa0|\x1fP\n\xb6e\x9d\r\x00V\x83\xbc\xf0 \x0b\xa1\x00\xf8{\xaf\xfb\xd4\x9bKK\'\xe1\xfb>\x1c\xa7\x83\x99\xe9\x19\xd8\x96\x85\xb6i\xc0\xf7\x04H\x11\x90h\xa5\x14\x00\xae\xdb\xb9=\xfd\xd2\x91\xf0\x1bb\xc0\x1f\x98fGL\xd3D\xb5Z\x85a\x98\xd8h4\xe0zN\xca\xfb\xbb>\xbc\\.\xa3T\xae@\x91B}}-\xdaRuj\n\x86aB\xca\xee\xf7\x96\x88 \x85\x84\xaf<476\xa0T\xf7^\xbe\xd9\xd99\xac\xae\\\x1apl\xdd\x0f\xbd:5\x05\xcb\xb2@\xd4;J\xd7u\xd0j6A\xc1\xe7,\x00T\xaaUXV\tB\x00\xbe\xaf\xb0\xd1\xa8\x03D\xb0m\x1b\xa6e\xc1\xb4\xac\xde\xdfL\xf1\xed\x08!a\xd96*\x95J\xf7\xa4\xa8\xee\xfb\x85\x10(W\xab0M\x13\x9dV\x0bN\xa7\x13\x1dc\xa9\\F\xa9T\x8enU\'\xa5\xd0\xe9tb\xeb\xd8\xa5\x12\xca\xe52@\x84\x8d\x8d\x8d.0\x00,\xdbB\xb9R\x814L4\xd6\xd6\xa0\x94B\xb9R\x81a\x98\x10B\xa0\xd9\xec\xad;\xca5f\x19\xd8\x12@\xd7:\x18\x02\x86a\xc0\xb4l\xf8\xca\x83\xe7{P\xa4\xb0}v\xeeM\r`\x95\xd5B\x84+\xfb\x0f?\xf2\xe8\xff\xbc\xf8\xfc\xf3k\xcaS3\xedV\x1b\x0b\x8b\x8b(\x95\xca(Ym(\xd7\x83\x12>\x94R\x05\xe1\x1c\xf2g\xa6\x94Z\x94\xefc\xa3^OM\x06\x92\xebv:mt:\xed\xbe!\xefV\xb39\xf0#\r#\x02\x11au\xe5\xd2\xe0\xfe\x8e 1nm4\xd0J\xd9\xbb~\x8f \x04\xd0n\xb5\xd0n\xb5\xe2?/%\x00\xd7u\xe1\xba\xee\x80<",M\x12<\xa7\x83\xba\xd3\x89\xed\x81\x88\xd0\xde\xd8H\xbd,;\x9d\x0e\xdcNg\xc8g/\xe09\x0e\x1a\xda\xad_\xe1\xfb=\xd7C\xc3\xad\xc7\x8e\xb5\xd3n\r(\x83\x8d\x86s\xd4ja\xf45\x0c\x13\x86i\xc3\xb6m\xb4\x9bM\xb8\x1d\x07J\x11~\xf6\xdaO\xbd\x04\xc0\xcb\x1c\x81\x85\x10DD\x14\x02\xfcK\xb7\xdc\xd2XX\\\xfc\x97\x0b\xe7\xff\xef\xcb\xadV\x13\x8dF\x03\x95Z\r\x8e\xd3\x01)\x0f\x1d\xc7\x81\xf4\x03\x88\xc7\x80\xb3\xaf\x82!F\xa7\x84"eC\xc3\xe0L\xdf\xeb\xc0\xcbD\xea]&\xd9\x8fQ\xa4mr\xf4\xfe\x13\xf7\x18f{O\x9c\x96,\xbf\x809\x89\xc8\x99%_\x1f\x16\xce\xc2\x06vi\x9a0Ke\x94\xaa\x15\x94\xa7\xa6pvy\x19\xae\xd3\x81a\xc8s\x7f\xfb\xec\xdf\x1f\n\x00\xf6\x07\xf9`9 \x89S\xc1\x1b\x9d\xaf?\xf2\xa7\xdf\x11\x02\xcdN\xbb\x85\xd5K\x17Q\xaeTP\x9b\x9eFe\xaa\x86r\xa9\x0c\xcb4aY\x16\x0ciD\xc9\x9d\xd4j\xc5\xba7\x1e\xe4\x99e\xe2v}\xbd\xe3M\xa4\xae\xdf+xKm`e\xe0\xba\xdaPx\xaf\xdb?e}\xf4\x8e\xdb.\x95\x82\xc5F\xa9dk\xc7\xd8\xf3m\x12\xfd\xfb\xd5\xef\xe7\x8a\xcd\xb6\xa8M\x9d\x94v\xbcz}=\xf9SS\xa2o\xf2\x8f\xc4\x12n\x1b\x83&\xa3\xe9\xfd\xedi\xef\xeb\xff\x97\xfe\xfe\xf4[\xcc\x86n%\xb22Bt\'\xb76\x0c\tiHH\xd3\x80U\xb2`\x97\xbb\xf0Vj\xd3\xa8\xaf\xaf\xa3Q_\x87\xebz\xb8\xfe\x86\x1b\xffz\xc7\xfc|K\x8b\xc0J\x08A#\xbf\xd0D\x14\xf6\x13[\x00J\x00\xaa\xbfv\xe0\xb3\xdf8\xfd\xee\xbb\x8fNU\xab\xd8\xb1s\'\x16\xaf\xda\x85\xc6\xfa\x1a\x9a\xf5\x06\x1c\xa7\r\xcfq\xa1\x94\x0f"\x85n\x00\x1f\x1c\x0bDz\x08\x1eb9\xb2F\xcea\xd1:{\xe4$\xed\x8b.\x90~gl\x91\xc89<z~|"\xe7\xe8\xab\xe9\x80\x9a,\xf4Y\x9d$\xa4a\xc24M\xd8\xd5**\xb5i(\xe5\xe3\xc3\xb3g\xb1\xbe\xb6\n\xd34\xdf\xfe\xcfW\xde\xb8}\xe7\xc2\xc2:\x806\x00\x07\x80\x9f\x06\xb0\x99\x12\xdaC\x1b\xe1\x03p\x01t~\xf4\xef\x87\xbew\xf0\x96\xcf\xfdb\xa3\xd18\xb8\xb2\xb2\x02"`aq\x01\xa5R\xa9\xebY\x9c\x0e<\xcf\x07\xa9\xc0\xaa\x10e\xcaF\x8b\xc1)2\xd9\x86\x91k\x8a\x1c\x90\x8d\t\'>\xc1p"\x13\xc0\x14\xd8\xb2\xee\xd4\xaa\xd20`\x98\x16,\xbb\x84J\xad\x86\xe6F\x03\x17\xce\x9fG\xa3\xbe\x0eR\xea\xd2}\x0f|\xe5\xa1\x9d\x0b\x0b\xcd\x80?oP\x027\xf0\xaf\xd0\xa2\xb0\x01\xc0\x06P\xf9\xb7\x7f\xfe\xd1\xe2\xb7\x1e\xfe\xe3\x1fv\x1c\xe7\xd3\xe5R\tS\xdb\xb6a\xfb\xf6\xed\x98\x9e\x9e\x86\x14\x12\xae\xe7\xc1w\\\x10\x85~;;\x9c\x99\x90\xcb\xf8i\x8a\\\xffO\xe4<\xe9\x138\x1e\xb1\x19p\xe68\xc0M\x13\x01B\xc2\x90&\xa4i\xc20M\xb4\xdb-\xac\xad\xac\xa0^_G\xab\xd9\x84\xefy\xcd_\xfd\xfco<\xf0\xbd\xef\xff\xe0\xc7\x00Z\x00:\xa1\x07N\x8b\xbeC\xffJ\rb3\x80\xb8\xfc\xc6O^\x9d\xfb\xea\x1f\xdc\xf7W\xab++\xb7[\x96\x1d\x94l\x02\xafhY0\x0c\x03B\xc8L\x91\xb3@p\xccyJD\xf1H"&\xb3\xda$\x11\xca\x0c\xa7\xd8\xbac\xa1D\x04\xa5T\xb7,\xeb:\xe8\xb4\xdb\xe8\xb4\xdbp\x1d\x07\x86a\x9e\xf9\xdd\xdf\xfb\xfd\x07\x1f\xff\x8bo\xbf\x15\xd8\x06\x1d^U\xe83&"\xa9A\x1cz\xe2\xf2\x17\xbf\xf0\xebw\x1d?v\xf4\x9b\xbe\xe7\xfd\x8c!%\x0c\xd3\xea\x8d\xce\t\xb1\tp\xf6\xce\x94(\x1c9\x05\xc3\xb9\xe91\xb8k&(\x80\xd8\xf7}\x80\xa8\xbdp\xd5\xae\x1f<\xfa\xc4\x9f\xff\xcdo\xfd\xf6\x97\xcek\x9e7\xaa>\x0c\x8a\xbeY\x00\xee\xcde\xd2\xb5\x13V\x10\x8d\xed\x9f\x1e;6\xf5\x8d\xaf}\xf5\xce\xe5\x0f\xde\xff\xcd\xf5\xb5\xb5_!"\xeb\x8a\x84s\x82\x97\xf5+i\x10\xb3\\\xa9\xbc\xbds~\xe1\xf9\xdb\x7f\xe7\xce\x7fz\xf8\xcf\x1e?\x1d@\xebh\xbew$\xbc\x99\xcfU\xc2\x13\x87 \x87Q\xd9<q\xfcx\xe5\xbb\xcf\xfc\xe5>\xdf\xf7JK\'O\xfc\x9c\x14R\x8c\x03\'\x18\xceO\xa4fw\xecX\xde\xb1s\xfe\xe2\xfe\x03\x9f{\xff\xbe\x07\x1e<\x1f\x80\xeaj\xd0\x86\xe0\xaa,\xf0\xe6:\x9f)\xd1X_\xc2\xd7\xfa\'\xb4d\xb1z\x95\xb4p\x8c!\x1a\xedM,\xd1\x90q\x16xs\x07\xa4\x00bh \xcb\x94\xe7b\x8b\xa6\xc1\xac\xad\x010%@&\xed\x91\xb2\x82;v.\xa2Ed\x0c\x88\xba\x0c0k\x18\xc4\xb1\xe7y\xc1\x9d8dZtf\xb1F\xe4\x03\xc5`e\xb1X,\x16\x8b\xc5\x9a\x90\xfe\x1f\xc8\xd4\x9c\x97*\x14\xd0}\x00\x00\x00\x00IEND\xaeB`\x82'

PSX_SITE = 'https://psxdatacenter.com/'
verbose = False
if sys.platform == 'win32':
    font = 'arial.ttf'
else:
    font = 'DejaVuSansMono.ttf'

def get_gameid_from_iso(path='NORMAL01.iso'):
    if not have_pycdlib and not have_iso9660:
        raise Exception('Can not find either pycdlib or pycdio. Try either \'pip3 install pycdio\' or \'pip3 install pycdlib\'.')

    try:
        if have_pycdlib:
            iso = pycdlib.PyCdlib()
            iso.open(path)
            extracted = io.BytesIO()
            iso.get_file_from_iso_fp(extracted, iso_path='/SYSTEM.CNF;1')
            extracted.seek(0)
            buf = str(extracted.read(1024))
            iso.close()
        if have_iso9660:
            iso = iso9660.ISO9660.IFS(source=path)
            st = iso.stat('system.cnf', True)
            if st is None:
                raise Exception('Could not open system.cnf')

            buf = iso.seek_read(st['LSN'])[1][:128]
            iso.close()
    except:
        return 'UNKN00000'

    idx = buf.find('cdrom:')
    if idx < 0:
        raise Exception('Could not read system.cnf')

    buf = buf[idx + 6:idx + 50]
    idx = buf.find('\r')
    if idx > 0:
        buf = buf[:idx]
    idx = buf.find('\n')
    if idx > 0:
        buf = buf[:idx]
    idx = buf.find(';1')
    if idx > 0:
        buf = buf[:idx]
    # Some games are of the form \DIR\SLPS12345, get rid of the path
    buf = buf.split('\\')[-1]
    
    bad_chars = "\\_. -"
    for i in bad_chars:
        buf = buf.replace(i, "")

    game_id = buf.upper()
    return game_id


def fetch_cached_file(path):
    ret = requests.get(PSX_SITE + path)
    print('get', PSX_SITE + path) if verbose else None
    if ret.status_code != 200:
        raise Exception('Failed to fetch file ', PSX_SITE + path)

    return ret.content.decode(ret.apparent_encoding)


def fetch_cached_binary(path):
    try:
        ret = requests.get(PSX_SITE + path, stream=True)
    except:
        print('fetch_cached_binary: Failed to fetch file ', PSX_SITE + path)
        return NULL
    if ret.status_code != 200:
        print('fetch_cached_binary: Failed to fetch file ', PSX_SITE + path)
        return NULL

    return ret.content

def get_game_from_gamelist(game_id):
    return fetch_cached_file(games[game_id]['url']) if game_id in games else None

def get_title_from_game(game_id):
    return games[game_id]['title'] if game_id in games else "Unknown"

def get_snd0_from_theme(theme, game_id, subdir):
    try:
        tmpfile = subdir + '/snd0.theme'
        temp_files.append(tmpfile)
        url = themes[theme]['url'] + '/blob/main/data/' + game_id + '/SND0.WAV' + '?raw=true'
        print('Try URL', url)
        subprocess.run(['wget', '-q', url, '-O', tmpfile], timeout=30, check=True)
        return tmpfile
    except:
        return None
    
def get_image_from_theme(theme, game_id, subdir, image):
    if theme == 'ASCIIART':
        if image[:4] == 'PIC0':
            return create_ascii_pic0(game_id, games[game_id]['title'])
        if image[:4] == 'PIC1':
            game = get_game_from_gamelist(game_id)
            icon0 = get_icon0_from_game(game_id, game, None, subdir + '/ICON0-theme.jpg')

            return create_ascii_pic1(game_id, icon0)
    if theme == 'DOTPAINTING':
        if image[:4] == 'PIC0':
            return create_dotpainting_pic0(game_id, games[game_id]['title'])
        if image[:4] == 'PIC1':
            game = get_game_from_gamelist(game_id)
            icon0 = get_icon0_from_game(game_id, game, None, subdir + '/ICON0-theme.jpg')

            return create_dotpainting_pic1(game_id, icon0)
    if theme == 'OILPAINTING':
        if image[:4] == 'PIC0':
            tmpfile = subdir + '/pic0-tmp.png'
            temp_files.append(tmpfile)
            return create_oilpainting_pic0(game_id, games[game_id]['title'], tmpfile)
        if image[:4] == 'PIC1':
            game = get_game_from_gamelist(game_id)
            icon0 = get_icon0_from_game(game_id, game, None, subdir + '/ICON0-theme.jpg')
            tmpfile = subdir + '/pic1-tmp.png'
            temp_files.append(tmpfile)
            return create_oilpainting_pic1(game_id, icon0, tmpfile)
    if theme == 'WATERCOLOR':
        if image[:4] == 'PIC0':
            tmpfile = subdir + '/pic0-tmp.png'
            temp_files.append(tmpfile)
            return create_watercolor_pic0(game_id, games[game_id]['title'], tmpfile)
        if image[:4] == 'PIC1':
            game = get_game_from_gamelist(game_id)
            icon0 = get_icon0_from_game(game_id, game, None, subdir + '/ICON0-theme.jpg')
            tmpfile = subdir + '/pic1-tmp.png'
            temp_files.append(tmpfile)
            return create_watercolor_pic1(game_id, icon0, tmpfile)
    if theme == 'COLORSKETCH':
        if image[:4] == 'PIC0':
            tmpfile = subdir + '/pic0-tmp.png'
            temp_files.append(tmpfile)
            return create_colorsketch_pic0(game_id, games[game_id]['title'], tmpfile)
        if image[:4] == 'PIC1':
            game = get_game_from_gamelist(game_id)
            icon0 = get_icon0_from_game(game_id, game, None, subdir + '/ICON0-theme.jpg')
            tmpfile = subdir + '/pic1-tmp.png'
            temp_files.append(tmpfile)
            return create_colorsketch_pic1(game_id, icon0, tmpfile)
    if 'auto' in themes[theme]:
        return None
    try:
        url = themes[theme]['url'] + '/raw/main/data/' + game_id + '/' + image
        print('Try URL', url) #if verbose else None
        ret = requests.get(url, stream=True)
        if ret.status_code != 200:
            return None

        d = ret.content
        return Image.open(io.BytesIO(d))
    except:
        return None

def get_icon0_from_game(game_id, game, cue, tmpfile, add_psn_frame=False):
    try:
        image = Image.open(cue[:-4] + '_cover.png')
        print('Use existing file %s as cover' % (cue[:-4] + '_cover.png')) if verbose else None 
        return image
    except:
        True

    if not game or game_id[:4] == 'UNKN':
        return Image.new("RGBA", (80, 80), (255,255,255,0))

    i = None
    g = re.findall('images/covers/./.*/.*.jpg', game)
    if not g:
        return None
    fcb = fetch_cached_binary(g[0])
    if not fcb:
        return None
    i = Image.open(io.BytesIO(fcb))

    if i and add_psn_frame:
        i = i.resize((138,140), Image.Resampling.BILINEAR)
        im0 = Image.open(io.BytesIO(i0))
        Image.Image.paste(im0, i, box=(20,18))
        return im0
    
    return i

def get_pic_from_game(pic, game_id, game, filename):
    try:
        image = Image.open(filename)
        print('Use existing', filename, 'as', pic) if verbose else None
        return image
    except:
        True

    if game_id in games and pic in games[game_id]:
        ret = requests.get(games[game_id][pic], stream=True)
        if ret.status_code == 200:
            return Image.open(io.BytesIO(ret.content))
    if not game or game_id[:4] == 'UNKN':
        return Image.new("RGBA", (80, 80), (255,255,255,0))
    
    # Screenshots might be from a different release of the game
    # so we can not use game_id
    filter = 'images/screens/./.*/.*/ss..jpg'
    fcb = fetch_cached_binary(random.choice(re.findall(filter, game)))
    if not fcb:
        return None
    return Image.open(io.BytesIO(fcb))

def get_pic0_from_game(game_id, game, cue):
    pic0 = get_pic_from_game('pic0', game_id, game, cue[:-4] + '_pic0.png')
    # resize to maximum 1000,560 (ps3 PIC0 size) keeping aspect ratio
    ar = pic0.height / pic0.width
    if pic0.height * ar > 560:
        if int(560 / ar) < 1000:
            pic0 = pic0.resize((int(560 / ar), 560), Image.Resampling.NEAREST)
        else:
            ar = 1000 / pic0.width
            pic0 = pic0.resize((1000, int(pic0.height * ar)), Image.Resampling.NEAREST)
        i = Image.new(pic0.mode, (1000, 560), (0,0,0)).convert('RGBA')
        i.putalpha(0)
        ns = (int((1000 - pic0.size[0]) / 2), 0)
        i.paste(pic0, ns)
        pic0 = i
    else:
        pic0 = pic0.resize((1000, int(1000 * ar)), Image.Resampling.NEAREST)
        i = Image.new(pic0.mode, (1000, 560), (0,0,0)).convert('RGBA')
        i.putalpha(0)
        i.paste(pic0, (0, int((560 - pic0.size[1]) / 2)))
        pic0 = i

    return pic0

def get_pic1_from_game(game_id, game, cue):
    return get_pic_from_game('pic1', game_id, game, cue[:-4] + '_pic1.png')

def get_pic1_from_bc(game_id, game, cue):
    if game_id[:4] == 'UNKN':
        return Image.new("RGBA", (80, 80), (255,255,255,0))
    
    path = games[game_id]['url'][:-5].replace('games', 'images/hires')
    path = path + '/' + path.split('/')[-1] + '-B-ALL.jpg'
    ret = requests.get(PSX_SITE + path, stream=True)
    if ret.status_code != 200:
        return Image.new("RGBA", (80, 80), (255,255,255,0))

    return Image.open(io.BytesIO(ret.content))

def get_icon0_from_disc(game_id, game, cue, filename):
    if game_id[:4] == 'UNKN':
        return Image.new("RGBA", (80, 80), (255,255,255,0))
    
    path = games[game_id]['url'][:-5].replace('games', 'images/hires')
    path = path + '/' + path.split('/')[-1] + '-D-ALL.jpg'
    ret = requests.get(PSX_SITE + path, stream=True)
    if ret.status_code != 200:
        return Image.new("RGBA", (80, 80), (255,255,255,0))

    return Image.open(io.BytesIO(ret.content))

def convert_snd0_to_at3(snd0, at3, duration, max_size, subdir = './'):
    print('Creating SND0.AT3')
    tmp_wav = subdir + 'SND0.WAV'
    tmp_snd0 = subdir + 'SND0.EA3'
    temp_files.append(tmp_wav)
    temp_files.append(tmp_snd0)
    s = parse_riff(snd0)
    if not s:
        print('Not a WAVE file')
        return None

    loop = True
    while loop:
        print('Creating temporary WAV file clamped to %d second duration %s' % (duration, tmp_wav))
        copy_riff(snd0, tmp_wav, max_duration_ms=duration * 1000)
        s = parse_riff(tmp_wav)
        print('Creating temporary ATRAC3 file', tmp_snd0) if verbose else None
        try:
            if os.name == 'posix':
                subprocess.run(['./atracdenc/src/atracdenc', '--encode=atrac3', '-i', tmp_wav, '-o', tmp_snd0], check=True)
            else:
                subprocess.run(['atracdenc/src/atracdenc', '--encode=atrac3', '-i', tmp_wav, '-o', tmp_snd0], check=True)
        except:
            print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\natracdenc not found.\nCan not create SND0.AT3\nPlease see README file for how to install atracdenc\nXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
        print('Converting EA3 to AT3 file') if verbose else None
        temp_files.append(at3)
        create_riff(tmp_snd0, at3, number_of_samples=int(len(s['data']['data'])/4), max_data_size=0, loop=True)
        if os.stat(at3).st_size < max_size:
            break
        # Too big. Clamp duration and try again
        duration = int(duration * 0.95 / (os.stat(at3).st_size / max_size))


# caller adds the wav file to temp_files
def get_snd0_from_link(link, subdir='./'):
    if not have_pytube:
        return None
    try:
        fn = YouTube(link).streams.filter(only_audio=True)[0].download(subdir)
    except:
        print('Failed to download', link)
        return None
    temp_files.append(fn)
    return fn;

# caller adds the wav file to temp_files
def get_snd0_from_game(game_id, subdir='./'):
    if not have_pytube or not game_id in games:
        return None
    if not 'snd0' in games[game_id]:
        return None

    return get_snd0_from_link(games[game_id]['snd0'], subdir=subdir)

def get_psio_cover(game_id):
    f = 'https://raw.githubusercontent.com/logi-26/psio-assist/main/covers/' + game_id + '.bmp'
    ret = requests.get(f, stream=True)
    if ret.status_code != 200:
        raise Exception('Failed to fetch file ', f)

    return ret.content

def generate_magic_word(url):
    print('Compute MagicWord from URL', url)
    
    ret = requests.get(url)
    print('get', url) if verbose else None
    if ret.status_code != 200:
        raise Exception('Failed to fetch file ', url)

    b = ret.content.decode(ret.apparent_encoding)
    idx = b.find('Sectors with LibCrypt protection')
    if idx == -1:
        print('Subchannel data not found at', url)
        return 0
    b = b[idx:]
    idx = b.find('table')
    b = b[:idx]

    mw = 0
    if b.find('<td>14105</td>') > 0 or b.find('<td>14110</td>') > 0:
        mw = mw | 0x8000
    if b.find('<td>14231</td>') > 0 or b.find('<td>14236</td>') > 0:
        mw = mw | 0x4000
    if b.find('<td>14485</td>') > 0 or b.find('<td>14490</td>') > 0:
        mw = mw | 0x2000
    if b.find('<td>14579</td>') > 0 or b.find('<td>14584</td>') > 0:
        mw = mw | 0x1000

    if b.find('<td>14649</td>') > 0 or b.find('<td>14654</td>') > 0:
        mw = mw | 0x0800
    if b.find('<td>14899</td>') > 0 or b.find('<td>14904</td>') > 0:
        mw = mw | 0x0400
    if b.find('<td>15056</td>') > 0 or b.find('<td>15061</td>') > 0:
        mw = mw | 0x0200
    if b.find('<td>15130</td>') > 0 or b.find('<td>15135</td>') > 0:
        mw = mw | 0x0100
        
    if b.find('<td>15242</td>') > 0 or b.find('<td>15247</td>') > 0:
        mw = mw | 0x0080
    if b.find('<td>15312</td>') > 0 or b.find('<td>15317</td>') > 0:
        mw = mw | 0x0040
    if b.find('<td>15378</td>') > 0 or b.find('<td>15383</td>') > 0:
        mw = mw | 0x0020
    if b.find('<td>15628</td>') > 0 or b.find('<td>15633</td>') > 0:
        mw = mw | 0x0010
        
    if b.find('<td>15919</td>') > 0 or b.find('<td>15924</td>') > 0:
        mw = mw | 0x0008
    if b.find('<td>16031</td>') > 0 or b.find('<td>16036</td>') > 0:
        mw = mw | 0x0004
    if b.find('<td>16101</td>') > 0 or b.find('<td>16106/td>') > 0:
        mw = mw | 0x0002
    if b.find('<td>16167</td>') > 0 or b.find('<td>16172</td>') > 0:
        mw = mw | 0x0001

    print('MagicWord %04x' % mw)
    return mw
    
def get_first_bin_in_cue(cue):
    with open(cue, "r") as f:
        files = re.findall('".*"', f.read())
        return files[0][1:-1]

def add_image_text(image, title, game_id):
    # Add a nice title text to the background image
    # Split it into separate lines
    #   for ' - '
    print('Add image text: title:', title) if verbose else None
    strings = title.split(' - ')
    y = 18
    txt = Image.new("RGBA", image.size, (255,255,255,0))
    fnt = ImageFont.truetype(font, 8)
    d = ImageDraw.Draw(txt)

    # Add Title (multiple lines) to upper right
    for t in strings:
        ts = d.textsize(t, font=fnt)
        d.text((image.size[0] - ts[0], y), t, font=fnt,
               fill=(255,255,255,255))
        y = y + ts[1] + 2

    # Add game-id to bottom right
    fnt = ImageFont.truetype(font, 10)
    ts = d.textsize(game_id, font=fnt)
    d.rectangle([(image.size[0] - ts[0] - 1, image.size[1] - ts[1] + 1),
                 (image.size[0] + 1, image.size[1] + 1)],
                fill=(0,0,0,255))
    d.text((image.size[0] - ts[0], image.size[1] - ts[1] - 1),
           game_id, font=fnt, fill=(255,255,255,255))

    image = Image.alpha_composite(image, txt)
    return image

def copy_file(inp, oup):
    with open(inp, "rb") as i:
        with open(oup, "wb") as o:
            while True:
                buf = i.read(1024*1024)
                if len(buf) == 0:
                    break
                o.write(buf)


def create_path(bin, f):
    s = bin.split('/')
    if len(s) > 1:
        f = '/'.join(s[:-1]) + '/' + f
    return f

def create_retroarch_thumbnail(dest, game_title, icon0, pic1):
        try:
            os.stat(dest + '/Named_Boxarts')
        except:
            os.mkdir(dest + '/Named_Boxarts')
    
        image = icon0.resize((256,256), Image.Resampling.BILINEAR)
        #The following characters in playlist titles must be replaced with _ in the corresponding thumbnail filename: &*/:`<>?\|
        f = args.retroarch_thumbnail_dir + '/Named_Boxarts/' + game_title + '.png'
        print('Save cover as', f) if verbose else None
        image.save(f, 'PNG')

        try:
            os.stat(args.retroarch_thumbnail_dir + '/Named_Snaps')
        except:
            os.mkdir(args.retroarch_thumbnail_dir + '/Named_Snaps')
        image = pic1.resize((512,256), Image.Resampling.BILINEAR)
        #The following characters in playlist titles must be replaced with _ in the corresponding thumbnail filename: &*/:`<>?\|
        f = args.retroarch_thumbnail_dir + '/Named_Snaps/' + game_title + '.png'
        print('Save snap as', f) if verbose else None
        image.save(f, 'PNG')


def create_metadata(cue, game_id, game_title, icon0, pic0, pic1, snd0, manual):
    print('fetching metadata for', game_id, 'to directory', cue) if verbose else None

    f = cue.split('/')[-1][:-4]
    with open(create_path(cue, 'GAME_ID'), 'w') as d:
        d.write(game_id)
    with open(create_path(cue, 'GAME_TITLE'), 'w') as d:
        d.write(game_title)
    icon0.save(create_path(cue, f + '_cover.png'))
    pic0.save(create_path(cue, f + '_pic0.png'))
    pic1.save(create_path(cue, f + '_pic1.png'))
    if manual:
        p = create_path(cue, f + '.manual')
        try:
            os.stat(p)
            print('Local manual detected in', p, 'skipping fetch')
        except:
            if p != manual:
                with open(manual, 'rb') as i:
                    d = i.read()
                    with open(p, 'wb') as o:
                        o.write(d)
    if snd0:
        p = create_path(cue, f + '.snd0')
        if p != snd0:
            with open(snd0, 'rb') as i:
                d = i.read()
                with open(p, 'wb') as o:
                    o.write(d)
        
def get_imgs_from_bin(cue):
    def get_file_name(line):
        # strip off leading 'FILE '
        pos = line.lower().index('file ')
        line = line[pos + 5:]
        # strip off leading 'FILE '
        pos = line.lower().index(' binary')
        line = line[:pos+1]
        #strip off leading ' '
        while line[0] == ' ':
            line = line[1:]
        #strip off trailing ' '
        while line[-1] == ' ':
            line = line[:-1]
        # remove double quotes
        if line[0] == '"':
            line = line[1:-1]
        # remove single quotes
        if line[0] == '\'':
            line = line[1:-1]
        return line
    
    print('CUE', cue) if verbose else None

    img_files = []
    with open(cue, 'r') as f:
        lines = f.readlines()
        for line in lines:
            # FILE
            if re.search('^\s*FILE', line):
                f = get_file_name(line)
                if f[0] != '/':
                    s = cue.split('/')
                    if len(s) > 1:
                        f = '/'.join(s[:-1]) + '/' + f
                img_files.append(f)
    return img_files


def create_retroarch_bin(dest, game_title, cue_files, img_files):
    try:
        os.mkdir(dest)
    except:
        True
    with open(dest + '/' + game_title + '.m3u', 'wb') as md:
        for i in range(len(img_files)):
            g = game_title
            g = g + '-%d' % i + '.img'
            md.write(bytes(g + chr(13) + chr(10), encoding='utf-8'))

            f = dest + '/' + g
            print('Installing', f) if verbose else None
            copy_file(img_files[i], f)
            

def create_retroarch_cue(dest, game_title, cue_files, img_files, magic_word):
    try:
        os.mkdir(dest)
    except:
        True
    with open(dest + '/' + 'PSISO.m3u', 'wb') as md:
        for i in range(len(cue_files)):
            p = 'PSISO%d' % i
            with open(dest + '/' + p + '.CD', 'wb') as nc:
                md.write(bytes(p + '.CD' + chr(13) + chr(10), encoding='utf-8'))
                cur_cue = open(cue_files[i], 'r')
                for line in cur_cue:
                    m = re.search('FILE "?(.*?)"? BINARY', line)
                    if m:
                        nc.write(bytes('FILE \"%s.bin\" BINARY' % p + chr(13) + chr(10), encoding='utf-8'))
                    else:
                        nc.write(bytes(line, encoding='utf-8'))
                
                b = dest + '/' + p + '.bin'
                print('Installing', b) if verbose else None
                copy_file(img_files[i], b)
            if i < len(magic_word):
                print('Create magic word for disc', i)
                create_sbi(dest + '/' + p + '.sbi', magic_word[i])
                
def create_psio(dest, game_id, game_title, icon0, cu2_files, img_files):
    f = dest + '/' + game_title
    try:
        os.mkdir(f)
    except:
        True

    with open(f + '/' + game_id[0:4] + '-' + game_id[4:9] + '.bmp', 'wb') as d:
        image = icon0.resize((80,84), Image.Resampling.BILINEAR)
        i = io.BytesIO()
        image.save(i, format='BMP')
        i.seek(0)
        d.write(i.read())
            
    try:
        os.unlink(f + '/MULTIDISC.LST')
    except:
        True
    with open(f + '/MULTIDISC.LST', 'wb') as md:
        for i in range(len(img_files)):
            g = game_title
            g = g + '-%d' % i
            g = g + '.img'
            md.write(bytes(g + chr(13) + chr(10), encoding='utf-8'))

            print('Installing', f + '/' + g) if verbose else None
            copy_file(img_files[i], f + '/' + g)
            copy_file(cu2_files[i], f + '/' + g[:-4] + '.cu2')


def get_toc_from_cu2(cu2):
    def bcd(i):
        return int(i % 10) + 16 * (int(i / 10) % 10)

    _toc_header = bytes([
        0x41, 0x00, 0xa0, 0x00, 0x00, 0x00, 0x00, 0x01, 0x20, 0x00,
        0x01, 0x00, 0xa1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x01, 0x00, 0xa2, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ])
    
    toc = bytearray(_toc_header)

    with open(cu2, 'r') as f:
        lines = f.readlines()

        # Find the number of tracks and trk_end
        num_tracks = None
        trk_end = None
        data = None
        for line in lines:
            if re.search('data', line):
                data = line[10:10 + 8]
            if re.search('^ntracks', line):
                num_tracks = int(line[7:])
            if re.search('^trk end', line):
                trk_end = line[10:]
        # number of tracks
        toc[17] = bcd(num_tracks)
        # size of image
        toc[27] = bcd(int(trk_end[:2]))
        toc[28] = bcd(int(trk_end[3:5]) - 2)
        toc[29] = bcd(int(trk_end[6:8]))

        track = 1
        for line in lines:
            if not re.search('^data', line) and not re.search('^track', line):
                continue
            
            msf = line[10:]
            buf = bytearray(10)
            if track == 1:
                buf[0] = 0x41
                buf[2] = bcd(track)
                buf[3] = bcd(int(data[:2]))
                buf[4] = bcd(int(data[3:5]))
                buf[5] = 1
                buf[7] = int(data[:2])
                buf[8] = int(data[3:5])
                buf[9] = int(data[6:8])
            else:
                buf[0] = 0x01
                buf[2] = bcd(track)
                buf[3] = bcd(int(msf[:2])  - 2*int(data[:2]))
                buf[4] = bcd(int(msf[3:5]) - 2*int(data[3:5]))
                buf[5] = bcd(int(msf[6:8]) - 2*int(data[6:8]))
                buf[7] = bcd(int(msf[:2])  - int(data[:2]))
                buf[8] = bcd(int(msf[3:5]) - int(data[3:5]))
                buf[9] = bcd(int(msf[6:8]) - int(data[6:8]))
            
            track = track + 1
            toc = toc + buf

        return toc


def generate_pbp(dest_file, disc_ids, game_title, icon0, pic0, pic1, cue_files, cu2_files, img_files, aea_files, snd0=None, whole_disk=True, subchannels=[]):
    print('Create PBP file for', game_title) if verbose else None

    p = popstation()
    p.verbose = verbose
    p.disc_ids = disc_ids
    p.game_title = game_title
    p.subchannels = subchannels
    if icon0:
        p.icon0 = icon0
    if pic0:
        p.pic0 = pic0
    if pic1:
        p.pic1 = pic1
    if len(aea_files):
        p.aea = aea_files
    if snd0:
        p.snd0 = snd0
    for i in range(len(img_files)):
        f = img_files[i]
        print('Need to create a TOC') if verbose else None
        toc = get_toc_from_cu2(cu2_files[i])

        print('Add image', f) if verbose else None
        p.add_img((f, toc))
        
        if not whole_disk:
            bc = bchunk()
            bc.towav = True
            bc.open(cue_files[i])
            # store how big the data track is
            p.add_track0_size(bc.tracks[0]['stop'])
            p.striptracks = True

    p.eboot = dest_file
    print('Create PBP file at', p.eboot)
    p.create_pbp()
    try:
        os.sync()
    except:
        True

    
def create_psp(dest, disc_ids, game_title, icon0, pic0, pic1, cue_files, cu2_files, img_files, mem_cards, aea_files, subdir = './', snd0=None, watermark=False, subchannels=[], manual=None):
    # Convert ICON0 to a file object
    if icon0.size[0] / icon0.size[1] < 1.4 and icon0.size[0] / icon0.size[1] > 0.75:
        image = icon0.resize((80, 80), Image.Resampling.BILINEAR)
    else:
        image = icon0.resize((144, 80), Image.Resampling.BILINEAR)
    i = io.BytesIO()
    image.save(i, format='PNG')
    i.seek(0)
    icon0 = i.read()

    # Convert PIC0 to a file object
    pic0 = pic0.resize((310, 180), Image.Resampling.BILINEAR).convert("RGBA")
    i = io.BytesIO()
    pic0.save(i, format='PNG')
    i.seek(0)
    pic0 = i.read()
    
    # Convert PIC1 to a file object
    pic1 = pic1.resize((480, 272), Image.Resampling.BILINEAR).convert("RGBA")
    if watermark:
        pic1 = add_image_text(pic1, game_title, disc_ids[0])
    i = io.BytesIO()
    pic1.save(i, format='PNG')
    i.seek(0)
    pic1 = i.read()
    
    f = dest + '/PSP/GAME/' + disc_ids[0]
    print('Install EBOOT in', f) if verbose else None
    try:
        os.mkdir(f)
    except:
        True

    snd0_data = None
    if snd0:
        try:
            temp_files.append(subdir + 'snd0_tmp.wav')
            if os.name == 'posix':
                subprocess.call(['ffmpeg', '-y', '-i', snd0, '-filter:a', 'atempo=0.91', '-ar', '44100', '-ac', '2', subdir + 'snd0_tmp.wav'])
            else:
                subprocess.call(['ffmpeg.exe', '-y', '-i', snd0, '-filter:a', 'atempo=0.91', '-ar', '44100', '-ac', '2', subdir + 'snd0_tmp.wav'])
            snd0 = subdir + 'snd0_tmp.wav'
        except:
            snd0 = None
    if snd0:
        convert_snd0_to_at3(snd0, subdir + '/SND0.AT3', 59, 500000)
        with open(subdir + 'SND0.AT3', 'rb') as i:
            snd0_data = i.read()

    dest_file = f + '/EBOOT.PBP'
    generate_pbp(dest_file, disc_ids, game_title, icon0, pic0, pic1, cue_files, cu2_files, img_files, aea_files, snd0=snd0_data, whole_disk=False, subchannels=subchannels)

    if manual:
        print('Installing manual as', f + '/DOCUMENT.DAT')
        copy_file(manual, f + '/DOCUMENT.DAT')

    idx = 0
    for mc in mem_cards:
        mf = f + ('/SCEVMC%d.VMP' % idx)
        with open(mf, 'wb') as of:
            print('Installing MemoryCard in temporary location as', mf)
            of.write(encode_vmp(mc))
        idx = idx + 1 
    if idx > 0:
        print('###################################################')
        print('###################################################')
        print('Memory card images temporarily written to the game directory.')
        print('1, Remove the PSP/VITA')
        print('2, Start the game to create the SAVEDATA directory')
        print('   and then quit the game.')
        print('3, Reconnect the PSP/VITA')
        print('4, Run this command to finish installing the memory cards:')
        print('')
        print('./pop-fe.py --psp-dir=%s --disc_id=%s --psp-install-memory-card' % (dest, disc_ids[0]))
        print('###################################################')
        print('###################################################')
        try:
            os.sync()
        except:
            True


def create_psc(dest, disc_ids, game_title, icon0, pic1, cue_files, cu2_files, img_files, watermark=True):
    print('Create PS Classics/AutoBleem EBOOT.PBP for', game_title) if verbose else None

    # Convert ICON0 to a file object
    image = icon0.resize((80,80), Image.Resampling.BILINEAR)
    i = io.BytesIO()
    image.save(i, format='PNG')
    i.seek(0)
    icon0 = i.read()

    # Convert PIC1 to a file object
    pic1 = pic1.resize((480, 272), Image.Resampling.BILINEAR).convert("RGBA")
    if watermark:
        pic1 = add_image_text(pic1, game_title, disc_ids[0])
    i = io.BytesIO()
    pic1.save(i, format='PNG')
    i.seek(0)
    pic1 = i.read()
    
    dest_file = dest + '/Games/' + game_title + '.PBP'
    print('Install EBOOT as', dest_file) if verbose else None
    generate_pbp(dest_file, disc_ids, game_title, icon0, None, pic1, cue_files, cu2_files, img_files, [])

    try:
        os.sync()

    except:
        True

            
def create_ps3(dest, disc_ids, game_title, icon0, pic0, pic1, cue_files, cu2_files, img_files, mem_cards, aea_files, magic_word, resolution, subdir = './', snd0=None, whole_disk=True, subchannels=[]):
    print('Create PS3 PKG for', game_title) if verbose else None

    p = popstation()
    p.verbose = verbose
    p.disc_ids = disc_ids
    p.game_title = game_title
    p.subchannels = subchannels
    #p.icon0 = icon0
    #p.pic1 = pic1
    if not whole_disk:
        p.striptracks = True
    p.complevel = 0
    p.magic_word = magic_word
    if len(aea_files):
        p.aea = aea_files
    
    for i in range(len(img_files)):
        f = img_files[i]
        print('Need to create a TOC') if verbose else None
        toc = get_toc_from_cu2(cu2_files[i])
        p.add_img((f, toc))
        
        if not whole_disk:
            bc = bchunk()
            bc.towav = True
            bc.open(cue_files[i])
            # store how big the data track is
            p.add_track0_size(bc.tracks[0]['stop'])

    # create directory structure
    f = subdir + disc_ids[0]
    print('GameID', f)
    try:
        os.mkdir(f)
    except:
        True

    sfo = {
        'ANALOG_MODE': {
            'data_fmt': 1028,
            'data': 1},
        'ATTRIBUTE': {
            'data_fmt': 1028,
            'data': 2},
        'BOOTABLE': {
            'data_fmt': 1028,
            'data': 1},
        'CATEGORY': {
            'data_fmt': 516,
            'data_max_len': 4,
            'data': '1P'},
        'PARENTAL_LEVEL': {
            'data_fmt': 1028,
            'data': 3},
        'PS3_SYSTEM_VER': {
            'data_fmt': 516,
            'data_max_len': 8,
            'data': '01.7000'},
        'RESOLUTION': {
            'data_fmt': 1028,
            'data': resolution},
        'SOUND_FORMAT': {
            'data_fmt': 1028,
            'data': 1},
        'TITLE': {
            'data_fmt': 516,
            'data_max_len': 128,
            'data': game_title},
        'TITLE_ID': {
            'data_fmt': 516,
            'data_max_len': 16,
            'data': disc_ids[0]},
        'VERSION': {
            'data_fmt': 516,
            'data_max_len': 8,
            'data': '01.00'}
        }
    with open(f + '/PARAM.SFO', 'wb') as of:
        of.write(GenerateSFO(sfo))
        temp_files.append(f + '/PARAM.SFO')
    if snd0:
        subprocess.call(['ffmpeg', '-y', '-i', snd0, '-filter:a', 'atempo=0.91', '-ar', '44100', '-ac', '2', subdir + 'snd0_tmp.wav'])
        try:
            temp_files.append(subdir + 'snd0_tmp.wav')
            if os.name == 'posix':
                subprocess.call(['ffmpeg', '-y', '-i', snd0, '-filter:a', 'atempo=0.91', '-ar', '44100', '-ac', '2', subdir + 'snd0_tmp.wav'])
            else:
                subprocess.call(['ffmpeg.exe', '-y', '-i', snd0, '-filter:a', 'atempo=0.91', '-ar', '44100', '-ac', '2', subdir + 'snd0_tmp.wav'])
            snd0 = subdir + 'snd0_tmp.wav'
        except:
            snd0 = None
        convert_snd0_to_at3(snd0, f + '/SND0.AT3', 299, 2500000)

    image = None
    if icon0.size[0] / icon0.size[1] < 1.4 and icon0.size[0] / icon0.size[1] > 0.75:
        img = icon0.resize((176, 176), Image.Resampling.BILINEAR)
        image = Image.new(img.mode, (320, 176), (0,0,0)).convert('RGBA')
        image.putalpha(0)
        image.paste(img, (72,0))
    else:
        image = icon0.resize((320, 176), Image.Resampling.BILINEAR)
    image.save(f + '/ICON0.PNG', format='PNG')
    temp_files.append(f + '/ICON0.PNG')

    if pic0:
        # 4:3 == 1.333   16:9 == 1.7777
        aspect = pic0.size[0] / pic0.size[1]
        pp = pic0
        if aspect < 1.555:
            # Looks like pic0 is 4:3. We need to add some transparent
            # columns on each side to turn this into 16:9 aspect ratio
            # which is what PS3 expects for PIC0.PNG
            pp = Image.new(pic0.mode, (int(pic0.size[1] * 1.777), pic0.size[1]), (0,0,0)).convert('RGBA')
            pp.putalpha(0)
            pp.paste(pic0, (int((pic0.size[1] * 1.777 - pic0.size[0]) / 2),0))

        image = pp.resize((1000, 560), Image.Resampling.NEAREST)
        image.save(f + '/PIC0.PNG', format='PNG')
        temp_files.append(f + '/PIC0.PNG')
    
    image = pic1.resize((1920, 1080), Image.Resampling.NEAREST)
    image.save(f + '/PIC1.PNG', format='PNG')
    temp_files.append(f + '/PIC1.PNG')
    
    if pic0:
        # 4:3 == 1.333   16:9 == 1.7777
        aspect = pic0.size[0] / pic0.size[1]
        pp = pic0
        if aspect > 1.555:
            # Looks like pic0 is 16:9. We need to add some transparent
            # areas above and below the image to turn this into 4:3 aspect ratio
            # which is what PS3 expects for PIC2.PNG
            pp = Image.new(pic0.mode, (pic0.size[0], int(pic0.size[0] / 1.333)), (0,0,0)).convert('RGBA')
            pp.putalpha(0)
            pp.paste(pic0, (0, int((pic0.size[0] / 1.333 - pic0.size[1]) / 2)))

        image = pp.resize((310, 250), Image.Resampling.NEAREST)
        image.save(f + '/PIC2.PNG', format='PNG')
        temp_files.append(f + '/PIC2.PNG')
    
    with open('PS3LOGO.DAT', 'rb') as i:
        with open(f + '/PS3LOGO.DAT', 'wb') as o:
            o.write(i.read())
            temp_files.append(f + '/PS3LOGO.DAT')

    f = subdir + disc_ids[0] + '/USRDIR'
    try:
        os.mkdir(f)
    except:
        True

    _cfg = bytes([
        0x1c, 0x00, 0x00, 0x00, 0x50, 0x53, 0x31, 0x45,
        0x6d, 0x75, 0x43, 0x6f, 0x6e, 0x66, 0x69, 0x67,
        0x46, 0x69, 0x6c, 0x65, 0x00, 0xe3, 0xb7, 0xeb,
        0x04, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00,
        0xbb, 0xfa, 0xe2, 0x1b, 0x10, 0x00, 0x00, 0x00,
        0x64, 0x69, 0x73, 0x63, 0x5f, 0x6e, 0x6f, 0x00,
        0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x93, 0xd1, 0x5b, 0xf8
    ])
    with open(f + '/CONFIG', 'wb') as o:
        o.write(_cfg)
        temp_files.append(f + '/CONFIG')

        
    f = subdir + disc_ids[0] + '/USRDIR/CONTENT'
    try:
        os.mkdir(f)
    except:
        True

    p.eboot = subdir + disc_ids[0] + '/USRDIR/CONTENT/EBOOT.PBP'
    p.iso_bin_dat = subdir + disc_ids[0] + '/USRDIR/ISO.BIN.DAT'
    try:
        os.unlink(p.iso_bin_dat)
    except:
        True
    print('Create EBOOT.PBP at', p.eboot)
    p.create_pbp()
    temp_files.append(p.eboot)
    temp_files.append(p.iso_bin_dat)
    try:
        os.sync()
    except:
        True

    # sign the ISO.BIN.DAT
    print('Signing', p.iso_bin_dat)
    if os.name == 'posix':
        subprocess.call(['python3', './sign3.py', p.iso_bin_dat])
    else:
        subprocess.call(['sign3.exe', p.iso_bin_dat])

    #
    # USRDIR/SAVEDATA
    #
    f = subdir + disc_ids[0] + '/USRDIR/SAVEDATA'
    try:
        os.mkdir(f)
    except:
        True
    image = icon0.resize((80,80), Image.Resampling.BILINEAR)
    i = io.BytesIO()
    image.save(f + '/ICON0.PNG', format='PNG')
    temp_files.append(f + '/ICON0.PNG')    

    if len(mem_cards) < 1:
        create_blank_mc(f + '/SCEVMC0.VMP')
    if len(mem_cards) < 2:
        create_blank_mc(f + '/SCEVMC1.VMP')
    idx = 0
    for mc in mem_cards:
        mf = f + ('/SCEVMC%d.VMP' % idx)
        with open(mf, 'wb') as of:
            print('Installing MemoryCard as', mf)
            of.write(encode_vmp(mc))
        idx = idx + 1 
    temp_files.append(f + '/SCEVMC0.VMP')
    temp_files.append(f + '/SCEVMC1.VMP')

    sfo = {
        'CATEGORY': {
            'data_fmt': 516,
            'data_max_len': 4,
            'data': 'MS'},
        'PARENTAL_LEVEL': {
            'data_fmt': 1028,
            'data': 1},
        'SAVEDATA_DETAIL': {
            'data_fmt': 516,
            'data_max_len': 4,
            'data': ''},
        'SAVEDATA_DIRECTORY': {
            'data_fmt': 516,
            'data_max_len': 4,
            'data': disc_ids[0]},
        'SAVEDATA_FILE_LIST': {
            'data_fmt': 4,
            'data_max_len': 3168,
            'data': str(bytes(3168))},
        'SAVEDATA_TITLE': {
            'data_fmt': 516,
            'data_max_len': 128,
            'data': ''},
        'TITLE': {
            'data_fmt': 516,
            'data_max_len': 128,
            'data': game_title},
        'SAVEDATA_PARAMS': {
            'data_fmt': 4,
            'data_max_len': 128,
            'data': str(b"A\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\xda\xdaC4\x1br\xc2\xede\xa1/k'D\xc6\x11(\xcf\xc8\xb7(\xb8tG+*f\x85L\nm\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x8a\xfa,\xa1\xe7+mA\xc5m.\x9a\xba\xbct\xb0")}
    }
    with open(f + '/PARAM.SFO', 'wb') as of:
        of.write(GenerateSFO(sfo))
        temp_files.append(f + '/PARAM.SFO')

    #
    # Create ISO.BIN.EDAT
    #
    print('Create ISO.BIN.EDAT')
    pack(subdir + '%s/USRDIR/ISO.BIN.DAT' % disc_ids[0],
         subdir + '%s/USRDIR/ISO.BIN.EDAT' % disc_ids[0],
         'UP9000-%s_00-0000000000000001' % disc_ids[0])
    temp_files.append(subdir + '%s/USRDIR/ISO.BIN.EDAT' % disc_ids[0])

    #
    # Create PS3 PKG
    #
    print('Create PKG')
    if os.name == 'posix':
        subprocess.call(['python3','PSL1GHT/tools/ps3py/pkg.py','-c', 'UP9000-%s_00-0000000000000001' % disc_ids[0],subdir + disc_ids[0], dest])
    else:
        subprocess.call(['pkg.exe','-c', 'UP9000-%s_00-0000000000000001' % disc_ids[0],subdir + disc_ids[0], dest])
    temp_files.append(subdir + disc_ids[0] + '/USRDIR/CONTENT')
    temp_files.append(subdir + disc_ids[0] + '/USRDIR/SAVEDATA')
    temp_files.append(subdir + disc_ids[0] + '/USRDIR')
    temp_files.append(subdir + disc_ids[0])
    print('Finished.', dest, 'created')
    for f in temp_files:
        print('Deleting temp file', f) if verbose else None
        try:
            os.unlink(f)
        except:
            try:
                os.rmdir(f)
            except:
                True

    
def install_psp_mc(dest, game_id, mem_cards):
    if mem_cards and len(mem_cards) >= 1:
        try:
            with open(dest + '/PSP/SAVEDATA/' + game_id + '/SCEVMC0.VMP', 'wb') as f:
                f.write(encode_vmp(mem_cards[0]))
                print('Installed', dest + '/PSP/SAVEDATA/' + game_id + '/SCEVMC0.VMP')
        except:
            raise Exception('Can not install memory card file.', dest + '/PSP/SAVEDATA/' + game_id, 'does not exist')
    if mem_cards and len(mem_cards) >= 2:
        try:
            with open(dest + '/PSP/SAVEDATA/' + game_id + '/SCEVMC1.VMP', 'wb') as f:
                f.write(encode_vmp(mem_cards[1]))
                print('Installed', dest + '/PSP/SAVEDATA/' + game_id + '/SCEVMC1.VMP')
        except:
            raise Exception('Can not install memory card file.', dest + '/PSP/SAVEDATA/' + game_id, 'does not exist')
            
    try:
        os.stat(dest + '/PSP/GAME/' + game_id + '/SCEVMC0.VMP')
        try:
            copy_file(dest + '/PSP/GAME/' + game_id + '/SCEVMC0.VMP',
                      dest + '/PSP/SAVEDATA/' + game_id + '/SCEVMC0.VMP')
            print('Installed', dest + '/PSP/SAVEDATA/' + game_id + '/SCEVMC0.VMP')
            os.unlink(dest + '/PSP/GAME/' + game_id + '/SCEVMC0.VMP')
        except:
            print('Could not install /PSP/SAVEDATA/' + game_id + '/SCEVMC0.VMP')
    except:
        True
        
    try:
        os.stat(dest + '/PSP/GAME/' + game_id + '/SCEVMC1.VMP')
        try:
            copy_file(dest + '/PSP/GAME/' + game_id + '/SCEVMC1.VMP',
                      dest + '/PSP/SAVEDATA/' + game_id + '/SCEVMC1.VMP')
            print('Installed', dest + '/PSP/SAVEDATA/' + game_id + '/SCEVMC1.VMP')
            os.unlink(dest + '/PSP/GAME/' + game_id + '/SCEVMC1.VMP')
        except:
            print('Could not install /PSP/SAVEDATA/' + game_id + '/SCEVMC1.VMP')
    except:
        True
    try:
        os.sync()
    except:
        True

def check_memory_card(f):
    if os.stat(f).st_size == 131072:
        with open(f, 'rb') as mc:
            return [mc.read(131072)]
    if os.stat(f).st_size == 131200:
        with open(f, 'rb') as mc:
            mc.seek(0x80)
            return [mc.read(131072)]
    if os.stat(f).st_size == 131136:
        with open(f, 'rb') as mc:
            mc.seek(0x40)
            return [mc.read(131072)]
    if os.stat(f).st_size == 262144:
        with open(f, 'rb') as mc:
            return [mc.read(131072), mc.read(131072)]
    if os.stat(f).st_size == 134976:
        with open(f, 'rb') as mc:
            mc.seek(0xf40)
            return [mc.read(131072)]
    

def find_psp_mount():
    candidates = ['/d', '/e', '/f', '/g']
    if os.name == 'posix':
        with open('/proc/self/mounts', 'r') as f:
            lines = f.readlines()
            for line in lines:
                strings = line.split(' ')
                if strings[1][:11] == '/run/media/' or strings[1][:7] == '/media/':
                    candidates.append(strings[1])
    for c in candidates:
        try:
            os.stat(c + '/PSP/GAME')
            return c
        except:
            True
        try:
            os.stat(c + '/pspemu/PSP/GAME')
            return c + '/pspemu'
        except:
            True
    raise Exception('Could not find any PSP or VITA memory cards')


def find_psc_mount():
    candidates = ['/d', '/e', '/f', '/g']
    if os.name == 'posix':
        with open('/proc/self/mounts', 'r') as f:
            lines = f.readlines()
            for line in lines:
                strings = line.split(' ')
                if strings[1][:11] == '/run/media/' or strings[1][:7] == '/media/':
                    candidates.append(strings[1])
    for c in candidates:
        try:
            os.stat(c + '/Games')
            return c
        except:
            True
    raise Exception('Could not find any PS Classic/AutoBleem devices')


def create_blank_mc(mc):
    with open(mc, "wb") as f:
        f.seek(131071)
        f.write(bytes(1))
        f.seek(0)
        
        buf = bytearray(2)
        buf[0] = 0x4d
        buf[1] = 0x43
        f.write(buf)

        buf = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x0e,
                         0xa0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        f.seek(0x70)
        f.write(buf)

        buf = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xa0,
                         0xa0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        for i in range(0xf0, 0x780, 0x80):
            f.seek(i)
            f.write(buf)

        buf = bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xa0,
                         0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x00,
                         0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        f.seek(0x7f0)
        f.write(buf)

        buf = bytearray([0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x00,
                         0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
        for i in range(0x880, 0x1190, 0x80):
            f.seek(i)
            f.write(buf)

            
def create_ps2(dest, disc_ids, game_title, icon0, pic1, cue_files, cu2_files, img_files):
    print('Create PS2 VCD for', game_title) if verbose else None
    print('Install VCD in', dest + '/POPS')

    try:
        os.stat(dest + '/POPS')
    except:
        raise Exception('No POPS directory found')
    try:
        os.stat(dest + '/ART')
    except:
        raise Exception('No ART directory found')
        
    p = popstation()
    p.verbose = verbose
    p.disc_ids = disc_ids
    p.game_title = game_title

    discs_txt = None
    vmcdir_txt = None
    game_id = disc_ids[0]
    if len(img_files) > 1:
        for i in range(4):
            pp = game_id[:4] + '_' + game_id[4:7] + '.' + game_id[7:9] + '.' + game_title
            pp = pp + '_CD%d.VCD\n' % (i + 1)
            if not vmcdir_txt:
                vmcdir_txt = pp[:-5] + '\n'
            if i >= len(img_files):
                pp = '\n'
            if not discs_txt:
                discs_txt = pp
            else:
                discs_txt = discs_txt + pp

    for i in range(len(img_files)):
        f = img_files[i]
        print('Need to create a TOC') if verbose else None
        toc = get_toc_from_cu2(cu2_files[i])

        print('Add image', f) if verbose else None
        p.add_img((f, toc))

        print('GameID', game_id, game_title) if verbose else None
        pp = dest + '/POPS/' + game_id[:4] + '_' + game_id[4:7] + '.' + game_id[7:9] + '.' + game_title
        if len(img_files) > 1:
            pp = pp + '_CD%d' % (i + 1)
        try:
            os.mkdir(pp)
        except:
            True
        p.vcd = pp + '.VCD'
        print('Create VCD at', p.vcd) if verbose else None
        p.create_vcd()
        try:
            os.sync()
        except:
            True

        if discs_txt:
            with open(pp + '/DISCS.TXT', 'w') as f:
                f.write(discs_txt)
        if vmcdir_txt:
            with open(pp + '/VMCDIR.TXT', 'w') as f:
                f.write(vmcdir_txt)


        if i == 0:
            create_blank_mc(pp + '/SLOT0.VMC')
            create_blank_mc(pp + '/SLOT1.VMC')
            
    pp = dest + '/ART/'
    f = pp + game_id[0:4] + '_' + game_id[4:7] + '.' + game_id[7:9] + '_COV.jpg'
    image = icon0.resize((200, 200))
    image = image.convert('RGB')
    image.save(f, format='JPEG', quality=100, subsampling=0)
    f = pp + game_id[0:4] + '_' + game_id[4:7] + '.' + game_id[7:9] + '_BG.jpg'
    image = pic1.resize((640, 480))
    image = image.convert('RGB')
    image.save(f, format='JPEG', quality=100, subsampling=0)


def get_disc_ids(cue_files, subdir='./'):
    disc_ids = []
    for idx in range(len(cue_files)):
        print('Convert CUE to a normal style ISO') if verbose else None
        bc = bchunk()
        bc.verbose = args.v
        bc.open(cue_files[idx])
        bc.writetrack(0, subdir + 'ISO%02x' % idx)
        temp_files.append(subdir + 'ISO%02x01.iso' % idx)
        gid = get_gameid_from_iso(subdir + 'ISO%02x01.iso' % idx)
        disc_ids.append(gid)

    return disc_ids


def apply_ppf(img, disc_id, magic_word, auto_libcrypt):
    if auto_libcrypt:
        # https://red-j.github.io/Libcrypt-PS1-Protection-bible/index.htm
        print('Try to automatically generate libcrypt patch for', img)
        with open(img, 'rb+') as f:
            while True:
                off = f.tell()
                buf = bytearray(f.read(0x9300))
                if not buf:
                    break
                pos = buf.find(bytes([0x25, 0x30, 0x86, 0x00]))
                if pos > 0:
                    print('Found libcrypt signature. Patching it')
                    struct.pack_into('<H', buf, pos, magic_word)
                    struct.pack_into('<H', buf, pos + 2, 0x34c6)
                    f.seek(off)
                    f.write(buf)
        return
    if 'credit' in libcrypt[disc_id]:
        print(libcrypt[disc_id]['credit'])
    if 'ppf' in libcrypt[disc_id]:
        print('Patching ', disc_id, 'to remove libcrypt')
        ApplyPPF(img, libcrypt[disc_id]['ppf'])
        return
    if not 'ppfzip' in libcrypt[disc_id]:
        print('##################################')
        print('WARNING! No PPF found for', disc_id, 'the game might not work unless you have already patched the image file')
        print('##################################')
        return
    print('Fetching PPF for', disc_id)  if verbose else None
    ret = requests.get(libcrypt[disc_id]['ppfzip'][0])
    if ret.status_code != 200:
        print('##################################')
        print('WARNING! PPF to remove libcrypt was not found for %s. Game might not work.')
        print('##################################')
        return

    z = zipfile.ZipFile(io.BytesIO(ret.content))
    print('Extracting PPF ', libcrypt[disc_id]['ppfzip'][1]) if verbose else None
    z.extract(libcrypt[disc_id]['ppfzip'][1])
    temp_files.append(libcrypt[disc_id]['ppfzip'][1])

    print('Patching ', disc_id, 'to remove libcrypt')
    ApplyPPF(img, libcrypt[disc_id]['ppfzip'][1])

def install_deps():
    print(os.name)
    # requests
    try:
        import requests
        print('requests is already installed')
    except:
        print('Installing python requests')
        subprocess.call(['pip', 'install', 'requests'])
        import requests
    # pycdlib
    try:
        import pycdlib
        print('pycdlib is already installed')
    except:
        print('Installing python pycdlib.  This will fail on some platforms')
        subprocess.call(['pip', 'install', 'pycdlib'])
    # iso9660
    try:
        import iso9660
        print('iso9660 is already installed')
    except:
        print('Installing python iso9660.  This will fail on some platforms')
        subprocess.call(['pip', 'install', 'iso9660'])
    # rarfile
    try:
        import rarfile
        print('rarfile is already installed')
    except:
        print('Installing python rarfile.  This will fail on some platforms')
        subprocess.call(['pip', 'install', 'rarfile'])
    # ecdsa
    try:
        import ecdsa
        print('ecdsa is already installed')
    except:
        print('Installing python ecdsa')
        subprocess.call(['pip', 'install', 'ecdsa'])
    # PIL / pillow
    try:
        import pillow
        print('pillow is already installed')
    except:
        print('Installing python pillow')
        subprocess.call(['pip', 'install', 'pillow']) 
    # tkinterdnd2
    try:
        import tkinterdnd2
        print('tkinterdnd2 is already installed')
    except:
        print('Installing python tkinterdnd2')
        subprocess.call(['pip', 'install', 'tkinterdnd2']) 
    # pycryptodome
    try:
        import Cryptodome
        print('Crypto/pycryptodome is already installed')
    except:
        print('Trying to install python pycryptodome(Crypto)')
        subprocess.call(['pip', 'install', 'pycryptodome'])
    # Crypto
    try:
        import Crypto
        print('Crypto is already installed')
    except:
        print('Installing python Crypto')
        subprocess.call(['pip', 'install', 'Crypto'])
    # pytube
    try:
        from pytube import YouTube
        print('Pytube is already installed')
    except:
        print('Installing python pytube')
        subprocess.call(['pip', 'install', 'git+https://github.com/nficano/pytube'])
    # opencv-contrib-python
    try:
        import cv2
        print('opencv is already installed')
    except:
        print('Installing python opencv')
        subprocess.call(['pip', 'install', 'opencv-contrib-python'])
    # opencv-contrib-python
    try:
        import scipy
        print('scipy is already installed')
    except:
        print('Installing python scipy scikit-learn')
        subprocess.call(['pip', 'install', 'scipy', 'scikit-learn'])
    # cue2cu2
    try:
        if os.name == 'posix':
            os.stat('cue2cu2.py')
            print('cue2cu2.py is already installed')
        else:
            os.stat('cue2cu2.exe')
            print('cue2cu2.py is already installed')
    except:
        print('Downloading cue2cu2.py')
        ret = requests.get('https://raw.githubusercontent.com/NRGDEAD/Cue2cu2/master/cue2cu2.py')
        if ret.status_code != 200:
            print('Failed to download cue2cu2. Aborting install.')
            exit(1)
        if os.name == 'posix':
            with open('cue2cu2.py', 'wb') as f:
                f.write(bytes(ret.content.decode(ret.apparent_encoding), encoding='utf-8'))
        else:
            with open('cue2cu2.exe', 'wb') as f:
                f.write(bytes(ret.content.decode(ret.apparent_encoding), encoding='utf-8'))
    # binmerge
    try:
        os.stat('binmerge')
        print('binmerge is already installed')
    except:
        print('Downloading binmerge')
        ret = requests.get('https://raw.githubusercontent.com/putnam/binmerge/master/binmerge')
        if ret.status_code != 200:
            print('Failed to download binmerge. Aborting install.')
            exit(1)
        with open('binmerge', 'wb') as f:
            f.write(bytes(ret.content.decode(ret.apparent_encoding), encoding='utf-8'))
    if os.name == 'posix':
        # atracdenc
        try:
            os.stat('atracdenc/src/atracdenc')
            print('atracdenc is already installed')
        except:
            print('Cloning atracdenc')
            subprocess.call(['git', 'clone', 'https://github.com/dcherednik/atracdenc.git'])
            os.chdir('atracdenc/src')
            subprocess.call(['cmake', '.'])
            subprocess.call(['make'])
            os.chdir('../..')
        # PSL1GHT
        try:
            os.stat('PSL1GHT')
            print('PSL1GHT is already installed')
        except:
            print('Cloning PSL1GHT')
            subprocess.call(['git', 'clone', 'http://github.com/sahlberg/PSL1GHT'])
            os.chdir('PSL1GHT/tools/ps3py')
            subprocess.call(['git', 'checkout', 'origin/use-python3'])
            subprocess.call(['make'])
            os.chdir('../../..')
            
def generate_subchannels(magic_word):
    def generate_subchannel(sector, is_corrupt):
        def bcd(i):
            return int(i % 10) + 16 * (int(i / 10) % 10)

        sc = bytearray(12)
        s = sector - 150
        struct.pack_into('<I', sc, 0, s)
        struct.pack_into('<B', sc, 4, 1)
        struct.pack_into('<B', sc, 5, 1)
        if is_corrupt:
            s = s - 1
        struct.pack_into('<B', sc, 8, bcd(s % 75))
        s = s - (s % 75)
        s = int(s / 75)
        struct.pack_into('<B', sc, 7, bcd(s % 60))
        struct.pack_into('<B', sc, 6, bcd(int(s / 60)))

        s = sector
        if is_corrupt:
            s = s - 1
        struct.pack_into('<B', sc, 11, bcd(s % 75))
        s = s - (s % 75)
        s = int(s / 75)
        struct.pack_into('<B', sc, 10, bcd(s % 60))
        struct.pack_into('<B', sc, 9, bcd(int(s / 60)))

        return sc

    sector_pairs = {
        15: [14105,14110],
        14: [14231,14236],
        13: [14485,14490],
        12: [14579,14584],
        11: [14649,14654],
        10: [14899,14904],
         9: [15056,15061],
         8: [15130,15135],
         7: [15242,15247],
         6: [15312,15317],
         5: [15378,15383],
         4: [15628,15633],
         3: [15919,15924],
         2: [16031,16036],
         1: [16101,16106],
         0: [16167,16172]
        }
    scd = bytes(0)
    scd = scd + bytes([0xff,0xff,0xff,0xff,0x00,0x00,0x00,0x00,0xff,0xff,0xff,0xff])
    for i in range(15, -1, -1):
        scd = scd + generate_subchannel(sector_pairs[i][0], magic_word & (1<<i))
        scd = scd + generate_subchannel(sector_pairs[i][1], magic_word & (1<<i))
    scd = scd + bytes([0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff,0xff])

    return scd

def create_sbi(sbi, magic_word):
    def generate_sbi(sector):
        def bcd(i):
            return int(i % 10) + 16 * (int(i / 10) % 10)

        sc = bytearray(4)
        s = sector
        struct.pack_into('<B', sc, 2, bcd(s % 75))
        s = s - (s % 75)
        s = int(s / 75)
        struct.pack_into('<B', sc, 1, bcd(s % 60))
        struct.pack_into('<B', sc, 0, bcd(int(s / 60)))
        struct.pack_into('<B', sc, 3, 1)

        sc = sc + bytes([0xff, 0xff, 0xff, 0xff,
                         0xff, 0xff, 0xff, 0xff,
                         0xff, 0xff])
        return sc

    sector_pairs = {
        15: [14105,14110],
        14: [14231,14236],
        13: [14485,14490],
        12: [14579,14584],
        11: [14649,14654],
        10: [14899,14904],
         9: [15056,15061],
         8: [15130,15135],
         7: [15242,15247],
         6: [15312,15317],
         5: [15378,15383],
         4: [15628,15633],
         3: [15919,15924],
         2: [16031,16036],
         1: [16101,16106],
         0: [16167,16172]
        }
    with open(sbi, 'wb') as f:
        f.write(bytes([0x53, 0x42, 0x49, 0x00]))
        for i in range(15, -1, -1):
            if magic_word & (1<<i):
                f.write(generate_sbi(sector_pairs[i][0]))
                f.write(generate_sbi(sector_pairs[i][1]))

# Convert scans of the manual into a DOCUMENT.DAT for PSP
def create_manual(source, gameid, subdir='./pop-fe-work/'):
    print('Create manual', source)
    if source[:8] != 'https://':
        with open(source, 'rb') as f:
            buf = f.read(4)
            signature = struct.unpack_from('<I', buf, 0)[0]
            if signature == 0x20434F44: # a PSP DOCUMENT.DAT file?
                return source
            if signature == 0x04034b50: # a ZIP file?
                print('Is a zip file')
                tmpfile = subdir + '/DOCUMENT.zip'
                temp_files.append(tmpfile)
                copy_file(source, tmpfile)
                source = tmpfile

    print('Create DOCUMENT.DAT from', source)
    if source[:8] == 'https://':
            print('Download manual from', source)
            try:
                tmpfile = subdir + '/DOCUMENT-' + source.split('/')[-1]
                temp_files.append(tmpfile)
                subprocess.run(['wget', source, '-O', tmpfile], timeout=120, check=True)
                print('Downloaded manual as', tmpfile)
                source = tmpfile
            except:
                print('Failed to download manual from', source)
                return None
    if source[-4:] == '.zip':
            print('Unzip manual', source, 'from ZIP')
            subdir = subdir + '/DOCUMENT-tmp'
            try:
                os.stat(subdir)
            except:
                os.mkdir(subdir)
            temp_files.append(subdir)
                
            z = zipfile.ZipFile(source)
            for f in z.namelist():
                f = z.extract(f, path=subdir)
                temp_files.append(f)
            source = subdir
    if source[-4:] == '.cbr':
            print('Unzip manual', source, 'from CBR')
            subdir = subdir + '/DOCUMENT-tmp'
            try:
                os.stat(subdir)
            except:
                os.mkdir(subdir)
            temp_files.append(subdir)

            try:
                r = rarfile.RarFile(source)
                for f in r.namelist():
                    f = r.extract(f, path=subdir)
                    temp_files.append(f)
                source = subdir
            except:
                print('Failed to create SOFTWARE MANUAL. Could not extract images from CBR file. Make sure that UNRAR is installed.')
                return None
                
    if not os.path.isdir(source):
        print('Can not create manual.', source, 'is not a directory')
        return None

    tmpfile = subdir + '/DOCUMENT.DAT'
    temp_files.append(tmpfile)
    print('Create manual from directory [%s]' % (source))
    tmpfile = create_document(source, gameid, 480, tmpfile)
    if not tmpfile:
        print('Failed to create DOCUMENT.DAT')
    return tmpfile


# ICON0 is the game cover
# PIC0 is logo
# PIC1 is background image/poster
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help='Verbose')
    parser.add_argument('--retroarch-thumbnail-dir',
                    help='Where to store retroarch thumbnails')
    parser.add_argument('--retroarch-bin-dir',
                    help='Where to store retroarch games as (m3u/img)')
    parser.add_argument('--retroarch-cue-dir',
                    help='Where to store retroarch games as (m3u/cue)')
    parser.add_argument('--retroarch-pbp-dir',
                    help='Where to store retroarch games as (pbp)')
    parser.add_argument('--psio-dir',
                    help='Where to store images for PSIO')
    parser.add_argument('--psp-dir',
                    help='Where the PSP memory card is mounted')
    parser.add_argument('--psp-install-memory-card', action='store_true',
                        help='Finish installing a PSX memory card after '
                        'running the game at least once')
    parser.add_argument('--ps2-dir',
                    help='Where the PS2 USB-stick is mounted')
    parser.add_argument('--ps3-pkg',
                    help='Name of the PS3 pckage to create')
    parser.add_argument('--psc-dir',
                    help='Where the PS Classic/AutoBleem memory card is mounted')
    parser.add_argument('--fetch-metadata', action='store_true',
                    help='Just fetch metadata for the game')
    parser.add_argument('--game_id',
                        help='Force game_id for this iso.')
    parser.add_argument('--manual',
                        help='Directory/Zip/HTTP-link containing images for themanual')
    parser.add_argument('--title',
                    help='Force title for this iso')
    parser.add_argument('--ps3-libcrypt', action='store_true', help='Apply libcrypt patches also for PS3 Packages')
    parser.add_argument('--auto-libcrypt', action='store_true', help='Apply automatically generated libcrypt patches')
    parser.add_argument('--resolution',
                        help='Force setting resolution to 1: NTSC 2: PAL')
    parser.add_argument('--install', action='store_true', help='Install/Build all required dependencies')
    parser.add_argument('--whole-disk', action='store_true', help='Encode the entire disk and not just the first track. (Only applies to PS3)')
    parser.add_argument('--snd0',
                        help='WAV file to inject in PS3 PKG')
    parser.add_argument('--cover',
                        help='Cover image to use')
    parser.add_argument('--pic0',
                        help='PIC0/screenshot image to use')
    parser.add_argument('--pic1',
                        help='PIC1/screenshot image to use')
    parser.add_argument('--watermark', action='store_true',
                    help='Add a disc-id/game-title watermark for PSP/PSC')
    parser.add_argument('--list-themes', action='store_true',
                    help='List available themes')
    parser.add_argument('--theme',
                        help='Theme to use')
    parser.add_argument('files', nargs='*')
    args = parser.parse_args()

    if args.v:
        verbose = True

    if args.list_themes:
        for theme in themes:
            print(theme, ':', themes[theme]['description'], 'AUTO' if 'url' not in themes[theme] else themes[theme]['url'])
        exit(0)

    if args.theme:
        if args.theme[:4] == 'http':
            themes['http'] = {'url': args.theme,
                              'description': 'direct link to theme'}
            args.theme = 'http'
        if args.theme not in themes:
            print('No such theme:', args.theme)
            exit(1)

    if args.install:
        print('Install/Update required dependencies')
        install_deps()
        exit(0)

    if args.psp_dir and args.psp_dir.upper() == 'AUTO':
        args.psp_dir = find_psp_mount()

    if args.psc_dir and args.psc_dir.upper() == 'AUTO':
        args.psc_dir = find_psc_mount()

    if not args.files and not args.psp_install_memory_card:
        print('You must specify at least one file to fetch images for')
        exit(1)

    subdir = './pop-fe-work/'
    try:
        os.stat(subdir)
    except:
        os.mkdir(subdir)
        
    try:
        if os.name == 'posix':
            os.stat('./cue2cu2.py')
        else:
            os.stat('cue2cu2.exe')
    except:
        raise Exception('PSIO prefers CU2 files but cue2cu2.pu is not installed. See README file for instructions on how to install cue2cu2.')

    try:
        os.unlink('NORMAL01.iso')
    except:
        True

    idx = None
    cue_files = []
    cu2_files = []
    img_files = []
    mem_cards = []
    aea_files = {}
    if len(args.files) > 1:
        idx = (1, len(args.files))
    for cue_file in args.files:
        # Try to find which ones are memory cards
        if os.stat(cue_file).st_size <= 262144:
            mc = check_memory_card(cue_file)
            if mc:
                for i in mc:
                    mem_cards.append(i)
                continue
        
        zip = None
        print('Processing', cue_file, '...')

        if cue_file[-3:] == 'zip':
            print('This is a ZIP file. Uncompress the file.') if verbose else None
            zip = cue_file
            with zipfile.ZipFile(zip, 'r') as zf:
                for f in zf.namelist():
                    print('Extracting', f) if verbose else None
                    temp_files.append(f)
                    zf.extract(f)
                    if re.search('.cue$', f):
                        print('Found CUE file', f) if verbose else None
                        cue_file = f

        tmpcue = None
        if cue_file[-3:] == 'img' or cue_file[-3:] == 'bin':
            tmpcue = subdir + 'TMP%d.cue' % (0 if not idx else idx[0])
            print('IMG or BIN file. Create a temporary cue file for it', tmpcue) if verbose else None
            temp_files.append(tmpcue)
            with open(tmpcue, "w") as f:
                f.write('FILE "%s" BINARY\n' % cue_file)
                f.write('  TRACK 01 MODE2/2352\n')
                f.write('    INDEX 01 00:00:00\n')

            cue_file = tmpcue

        if cue_file[-3:] != 'cue':
            print('%s is not a CUE file. Skipping' % cue_file) if verbose else None
            continue

        i = get_imgs_from_bin(cue_file)
        img_file = i[0]
        if len(i) > 1:
            try:
                if os.name == 'posix':
                    os.stat('./binmerge')
                else:
                    os.stat('binmerge.exe')
            except:
                raise Exception('binmerge is required in order to support multi-bin disks. See README file for instructions on how to install binmerge.')
            mb = 'MB%d' % (0 if not idx else idx[0])
            if os.name == 'posix':
                subprocess.call(['python3', './binmerge', '-o', '.', cue_file, mb])
            else:
                subprocess.call(['binmerge.exe', '-o', '.', cue_file, mb])
            cue_file = mb + '.cue'
            temp_files.append(cue_file)
            img_file = mb + '.bin'
            temp_files.append(img_file)

        cu2_file = cue_file[:-4] + '.cu2'
        try:
            os.stat(cu2_file).st_size
            print('Using existing CU2 file: %s' % cu2_file) if verbose else None
        except:
            cu2_file = subdir + 'TMP%d.cu2' % (0 if not idx else idx[0])
            print('Creating temporary CU2 file: %s' % cu2_file) if verbose else None
            if os.name == 'posix':
                subprocess.call(['python3', './cue2cu2.py', '-n', cu2_file, '--size', str(os.stat(img_file).st_size), cue_file])
            else:
                subprocess.call(['cue2cu2.exe', '-n', cu2_file, '--size', str(os.stat(img_file).st_size), cue_file])
            temp_files.append(cu2_file)

        img_files.append(img_file)
        cue_files.append(cue_file)
        cu2_files.append(cu2_file)

        if args.psp_dir or args.ps3_pkg or args.retroarch_pbp_dir:
            bc = bchunk()
            bc.towav = True
            bc.open(cue_file)
            aea_files[0 if not idx else idx[0] - 1] = []
            for i in range(1, len(bc.cue)):
                if not bc.cue[i]['audio']:
                    print('WARNING disc contains multiple data tracks. Forcing --whole-disk')
                    args.whole_disk = True
                    continue
                f = subdir + 'TRACK_%d_' % (0 if not idx else idx[0])
                bc.writetrack(i, f)
                wav_file = f + '%02d.wav' % (bc.cue[i]['num'])
                temp_files.append(wav_file)
                aea_file = wav_file[:-3] + 'aea'
                temp_files.append(aea_file)
                print('Converting', wav_file, 'to', aea_file)
                try:
                    if os.name == 'posix':
                        subprocess.run(['./atracdenc/src/atracdenc', '--encode=atrac3', '-i', wav_file, '-o', aea_file], check=True)
                    else:
                        subprocess.run(['atracdenc/src/atracdenc', '--encode=atrac3', '-i', wav_file, '-o', aea_file], check=True)
                except:
                    print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\natracdenc not found.\nCan not convert CDDA tracks.\nCreating EBOOT.PBP without support for CDDA audio.\nPlease see README file for how to install atracdenc\nXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                    break
                aea_files[0 if not idx else idx[0] - 1].append(aea_file)

        if idx:
            idx = (idx[0] + 1, idx[1])

    # We need to convert the first track of every ISO so we can open the
    # disk and read system.cnf
    disc_ids = get_disc_ids(cue_files, subdir=subdir)
    real_disc_ids = disc_ids[:]

    if args.game_id:
        args.game_id = args.game_id.split(',')
    if args.psp_install_memory_card:
        if not args.game_id:
            raise Exception('Must specify --game_id when using --psp-install-memory-card')
        install_psp_mc(args.psp_dir, args.game_id[0], mem_cards)
        quit()
            
    _gids = None
    if args.game_id:
        _gids = args.game_id
    if not _gids:
        try:
            with open(create_path(args.files[0], 'GAME_ID'), 'r') as d:
                _gids = re.sub(r'[^A-Z0-9\,]+', '', d.read()).split(',')
        except:
            True

    if _gids:
        # override the disc_ids with the content of 'GAME_ID' or --game_id
        for idx in range(len(_gids)):
            if idx < len(disc_ids):
                disc_ids[idx] = _gids[idx]
    
    resolution = 1
    if args.ps3_pkg and (real_disc_ids[0][:4] == 'SLES' or real_disc_ids[0][:4] == 'SCES'):
        print('SLES/SCES PAL game. Default resolution set to 2 (640x512)') if verbose else None
        resolution = 2
    if args.resolution:
        print('Resolution set to', args.resolution) if verbose else None
        resolution = int(args.resolution)
    
    game_title = None
    if args.title:
        game_title = args.title
    if not game_title:
        try:
            with open(create_path(args.files[0], 'GAME_TITLE'), 'r') as d:
                game_title = d.read()
        except:
            True
    if not game_title:
        game_title = get_title_from_game(disc_ids[0])

    game = get_game_from_gamelist(disc_ids[0])

    # ICON0.PNG
    icon0 = None
    if args.cover:
        print('Get cover from', args.cover)
        icon0 = Image.open(args.cover)
    if args.theme:
        icon0 = get_image_from_theme(args.theme, disc_ids[0], subdir, 'ICON0.PNG')
        if not icon0:
            icon0 = get_image_from_theme(args.theme, disc_ids[0], subdir, 'ICON0.png')
    if not icon0:
        print('Fetch ICON0 for', game_title) if verbose else None
        temp_files.append(subdir + 'ICON0.jpg')
        icon0 = get_icon0_from_game(disc_ids[0], game, args.files[0], subdir + 'ICON0.jpg', add_psn_frame=True if args.ps3_pkg or args.psp_dir or args.fetch_metadata else False)

    # PIC0.PNG
    pic0 = None
    if args.pic0:
        print('Get PIC0/Screenshot from', args.pic0)
        pic0 = Image.open(args.pic0)
    if args.theme:
        pic0 = get_image_from_theme(args.theme, disc_ids[0], subdir, 'PIC0.PNG')
        if not pic0:
            pic0 = get_image_from_theme(args.theme, disc_ids[0], subdir, 'PIC0.png')
    if not pic0:
        print('Fetch PIC0 for', game_title) if verbose else None
        pic0 = get_pic0_from_game(disc_ids[0], game, args.files[0])
        
    # PIC1.PNG
    pic1 = None
    if args.pic1:
        print('Get PIC1/Screenshot from', args.pic1)
        pic1 = Image.open(args.pic1)
    if args.theme:
        pic1 = get_image_from_theme(args.theme, disc_ids[0], subdir, 'PIC1.PNG')
        if not pic1:
            pic1 = get_image_from_theme(args.theme, disc_ids[0], subdir, 'PIC1.png')
    if not pic1:
        print('Fetch PIC1 for', game_title) if verbose else None
        pic1 = get_pic1_from_game(disc_ids[0], game, args.files[0])

    manual = None
    if args.psp_dir:
        if args.manual:
            manual = args.manual
        if not manual:
            try:
                os.stat(args.files[0][:-4] + '.manual')
                manual = args.files[0][:-4] + '.manual'
                print('Use locally stored manual from', manual)
            except:
                True
        if not manual and 'manual' in games[disc_ids[0]]:
            manual = games[disc_ids[0]]['manual']
        if manual:
            manual = create_manual(manual, disc_ids[0])
        
    print('Id:', disc_ids[0])
    print('Title:', game_title)
    print('Cue Files', cue_files) if verbose else None
    print('Imb Files', img_files) if verbose else None
    print('Disc IDs', disc_ids) if verbose else None

    subchannels = []
    magic_word = []
    if real_disc_ids[0] in libcrypt:
        for idx in range(len(real_disc_ids)):
            magic_word.append(libcrypt[real_disc_ids[idx]]['magic_word'])
            subchannels.append(generate_subchannels(libcrypt[real_disc_ids[idx]]['magic_word']))
        patch_libcrypt = False
        if args.auto_libcrypt:
            patch_libcrypt = True
        if args.ps3_pkg and args.ps3_libcrypt:
            patch_libcrypt = True
        if args.ps2_dir or args.psio_dir:
            print('#####################################')
            print('WARNING! This disc is protected with libcrypt.')
            print('Will attempt to apply libcrypt PPF patch')
            print('#####################################')
            patch_libcrypt = True
        if args.ps3_pkg:
            print('#####################################')
            print('WARNING! This disc is protected with libcrypt.')
            print('Will attempt to inject MagicWord and Subchannel data')
            print('into ISO.BIN.DAT')
            print('This should work for most games. If not then try')
            print('creating the package again with --ps3-libcrypt')
            print('#####################################')
        if patch_libcrypt:
            #
            # Copy the CUE and BIN locally so we can patch them
            for idx in range(len(cue_files)):
                i = get_imgs_from_bin(cue_files[idx])
                print('Copy %s to LCP%02x.bin so we can patch libcrypt' % (i[0], idx)) if verbose else None
                copy_file(i[0], 'LCP%02x.bin' % idx) 
                temp_files.append('LCP%02x.bin' % idx)
                with open(cue_files[idx], 'r') as fi:
                    l = fi.readlines()
                    l[0] = 'FILE "%s" BINARY\n' % ('LCP%02x.bin' % idx)
                    with open('LCP%02x.cue' % idx, 'w') as fo:
                        fo.writelines(l)
                    temp_files.append('LCP%02x.cue' % idx)
                cue_files[idx] = 'LCP%02x.cue' % idx
                img_files[idx] = 'LCP%02x.bin' % idx
                apply_ppf(img_files[idx], real_disc_ids[idx], magic_word[idx], args.auto_libcrypt)

    snd0 = args.snd0
    # if we did not get an --snd0 argument see if can find one in the gamedb
    if args.theme:
        snd0 = get_snd0_from_theme(args.theme, disc_ids[0], subdir)
    if not snd0:
        try:
            os.stat(args.files[0][:-4] + '.snd0')
            snd0 = args.files[0][:-4] + '.snd0'
            print('Use locally stored SND0 from', snd0)
        except:
            True
    if not snd0:
        snd0 = get_snd0_from_game(disc_ids[0], subdir=subdir)
        if snd0:
            temp_files.append(snd0)
    if snd0 and snd0 == 'auto':
        a = Search(game_title + ' ps1 ost')
        snd0 = 'https://www.youtube.com/watch?v=' + a.results[0].video_id
        print('Found Youtube link', 'https://www.youtube.com/watch?v=' + a.results[0].video_id)
    if snd0 and snd0[:24] == 'https://www.youtube.com/':
        snd0 = get_snd0_from_link(snd0)
        if snd0:
            temp_files.append(snd0)

    if args.psp_dir:
        create_psp(args.psp_dir, disc_ids, game_title, icon0, pic0, pic1, cue_files, cu2_files, img_files, mem_cards, aea_files, snd0=snd0, watermark=args.watermark, subchannels=subchannels, manual=manual)
    if args.ps2_dir:
        create_ps2(args.ps2_dir, disc_ids, game_title, icon0, pic1, cue_files, cu2_files, img_files)
    if args.ps3_pkg:
        create_ps3(args.ps3_pkg, disc_ids, game_title, icon0, pic0, pic1, cue_files, cu2_files, img_files, mem_cards, aea_files, magic_word, resolution, snd0=snd0, subdir=subdir, whole_disk=args.whole_disk, subchannels=subchannels)
    if args.psc_dir:
        create_psc(args.psc_dir, disc_ids, game_title, icon0, pic1, cue_files, cu2_files, img_files, watermark=True if args.watermark else False)
    if args.fetch_metadata:
        create_metadata(args.files[0], disc_ids[0], game_title, icon0, pic0, pic1, snd0, manual)
    if args.psio_dir:
        create_psio(args.psio_dir, disc_ids[0], game_title, icon0, cu2_files, img_files)
    if args.retroarch_bin_dir:
        new_path = args.retroarch_bin_dir + '/' + game_title
        create_retroarch_bin(new_path, game_title, cue_files, img_files)
    if args.retroarch_cue_dir:
        new_path = args.retroarch_cue_dir + '/' + game_title
        create_retroarch_cue(new_path, game_title, cue_files, img_files, magic_word)
    if args.retroarch_pbp_dir:
        new_path = args.retroarch_pbp_dir + '/' + game_title + '.pbp'
        if icon0:
            image = icon0.resize((80,80), Image.Resampling.BILINEAR)
            i = io.BytesIO()
            image.save(i, format='PNG')
            i.seek(0)
            icon0 = i.read()

        if pic1:
            image = pic1
            i = io.BytesIO()
            image.save(i, format='PNG')
            i.seek(0)
            pic1 = i.read()
        
        generate_pbp(new_path, disc_ids, game_title, icon0, None, pic1, cue_files, cu2_files, img_files, aea_files)
    if args.retroarch_thumbnail_dir:
        create_retroarch_thumbnail(args.retroarch_thumbnail_dir, game_title, icon0, pic1)

    for f in temp_files:
        print('Deleting temp file', f) if verbose else None
        try:
            os.unlink(f)
        except:
            try:
                os.rmdir(f)
            except:
                True
