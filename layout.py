#!/usr/bin/env python
# coding: utf-8
#
import argparse
import hashlib
import importlib
import io
import requests
from PIL import Image, ImageDraw, ImageFont
from gamedb import games


def get_pic_from_game(pic, game_id, game, filename):
    try:
        image = Image.open(filename)
        print('Use existing', filename, 'as', pic) if verbose else None
        return image
    except:
        True

    if game_id in games and pic in games[game_id]:
        # pic None-ed out in gamedb
        if not games[game_id][pic]:
            return None

        _h = hashlib.md5(games[game_id][pic].encode('utf-8')).hexdigest()
        f = 'https://github.com/sahlberg/pop-fe-assets/raw/master/' + pic + '/' + _h
        ret = requests.get(f, stream=True)
        if ret.status_code == 200:
            print('Found cached prebuilt', pic.upper(), f)
            return Image.open(io.BytesIO(ret.content))
    
        ret = requests.get(games[game_id][pic], stream=True)
        if ret.status_code == 200:
            if ret.apparent_encoding:
                return Image.open(io.BytesIO(ret.content.decode(ret.apparent_encoding)))
            else:
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
    #try:
    if True:
        pic0 = get_pic_from_game('pic0', game_id, game, cue[:-4] + '_pic0.png')
        # If we need to rescale, paste the image into a larger transparent
        # canvas first before we rescale it below
        if 'pic0-scaling' in games[game_id]:
            sc = games[game_id]['pic0-scaling']
        else:
            sc = 0.6
        if 'pic0-offset' in games[game_id]:
            of = games[game_id]['pic0-offset']
        else:
            of = (0.30, 0.30)

        # First, try to scale Y axis to 560 pixels
        syf = 560 / pic0.size[1]
        ns = (int(pic0.size[0] * syf), int(pic0.size[1] * syf))
        if ns[0] > 1000:
            # Fitting by Y size made it too big. Scale X axis to 1000 instead
            sxf = 1000 / pic0.size[0]
            ns = (int(pic0.size[0] * sxf), int(pic0.size[1] * sxf))
        pic0 = pic0.resize((int(ns[0] * sc), int(ns[1] * sc)), Image.Resampling.LANCZOS)
        i = Image.new(pic0.mode, (1000, 560), (0,0,0)).convert('RGBA')
        i.putalpha(0)
        i.paste(pic0, (int(1000 * of[0]), int(560 * of[1])))
        pic0 = i
    #except:
    #    return None

    return pic0

def get_pic1_from_game(game_id, game, cue):
    try:
        return get_pic_from_game('pic1', game_id, game, cue[:-4] + '_pic1.png')
    except:
        return None


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

    p1 = get_pic1_from_game(args.gameid, None, 'nothing')
    print('p1', p1)
    p0 = get_pic0_from_game(args.gameid, None, 'nothing')
    print('p0', p0)

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
    
