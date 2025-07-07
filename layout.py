#!/usr/bin/env python
# coding: utf-8
#
import argparse
import importlib
from PIL import Image, ImageDraw, ImageFont
popfe = importlib.import_module("pop-fe")
from gamedb import games

def has_transparency(img):
    if img.info.get("transparency", None) is not None:
        return True
    if img.mode == "P":
        transparent = img.info.get("transparency", -1)
        for _, index in img.getcolors():
            if index == transparent:
                return True
    elif img.mode == "RGBA":
        extrema = img.getextrema()
        if extrema[3][0] < 255:
            return True

        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--gameid', help='Game ID.')
    parser.add_argument('--pic0-scaling', help='Scaing factor to use for PIC0')
    parser.add_argument('--pic0-offset', help='Offset factor to use for PIC0')
    parser.add_argument('files', nargs='*')
    args = parser.parse_args()

    if args.pic0_scaling:
        games[args.gameid]['pic0-scaling'] = float(args.pic0_scaling)
    if args.pic0_offset:
        games[args.gameid]['pic0-offset'] = eval(args.pic0_offset)

    if 'pic0-scaling' in games[args.gameid]:
        print('pic0 scaling:', games[args.gameid]['pic0-scaling'])
    else:
        print('pic0 scaling: DEFAULT 0.6')
        
    if 'pic0-offset' in games[args.gameid]:
        print('pic0 offset:', games[args.gameid]['pic0-offset'])
    else:
        print('pic0 offset: DEFAULT (0.3, 0.3)')
        
    p1 = popfe.get_pic1_from_game(args.gameid, None, 'nothing')
    p0 = popfe.get_pic0_from_game(args.gameid, None, 'nothing')

    # PS3
    pic0 = p0.resize((1000,560), Image.Resampling.LANCZOS)
    pic1 = p1.resize((1920,1080), Image.Resampling.LANCZOS)
    if has_transparency(pic0):
        Image.Image.paste(pic1, pic0,
                          box=(760,425,1760,985), mask=pic0)
    else:
        Image.Image.paste(pic1, pic0,
                          box=(760,425,1760,985))

    pic1 = pic1.convert('RGBA')
    img1 = ImageDraw.Draw(pic1)
    img1.rectangle([(760,425),(1760,985)], outline ="red") 
    pic1.show()

    # PSP
    pic0 = p0.resize((280,170), Image.Resampling.LANCZOS)
    pic1 = p1.resize((480,272), Image.Resampling.LANCZOS)
    if has_transparency(pic0):
        Image.Image.paste(pic1, pic0,
                          box=(190,100,470,270), mask=pic0)
    else:
        Image.Image.paste(pic1, pic0,
                          box=(190,100,470,270))

    img1 = ImageDraw.Draw(pic1)
    img1.rectangle([(190,100),(470,270)], outline ="red") 
    pic1.show()
    
    # PIC0 at  760, 425   1760, 985
    # ICON at  49, 43      66, 60
    # +        'pic0-scaling': 0.6,
    # +        'pic0-offset': (100,100),
    
