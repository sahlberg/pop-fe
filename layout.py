#!/usr/bin/env python
# coding: utf-8
#
import argparse
import importlib
from PIL import Image, ImageDraw, ImageFont
popfe = importlib.import_module("pop-fe")

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
    parser.add_argument('files', nargs='*')
    args = parser.parse_args()

    #pic1 = popfe.get_pic_from_game(None, None, None, 'PIC1.PNG')
    pic1 = popfe.get_pic1_from_game(args.gameid, None, 'nothing')
    pic0 = popfe.get_pic0_from_game(args.gameid, None, 'nothing')
    if has_transparency(pic0):
        Image.Image.paste(pic1, pic0,
                          box=(760,425,1760,985), mask=pic0)
    else:
        Image.Image.paste(pic1, pic0,
                          box=(760,425,1760,985))

    img1 = ImageDraw.Draw(pic1)
    img1.rectangle([(760,425),(1760,985)], outline ="red") 
    pic1.show()
    
    # PIC0 at  760, 425   1760, 985
    # ICON at  49, 43      66, 60
    # +        'pic0-scaling': 0.6,
    # +        'pic0-offset': (100,100),
    
