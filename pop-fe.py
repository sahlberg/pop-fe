#!/usr/bin/env python
# coding: utf-8
#
# A utility to automate building and installing PSX games onto different
# systems.
# The current directory where you run this utility from needs to be writable
# so that we can use it to store temporary files during the conversing process.
#
# It supports and can convert games stored in the following types of file
# formats:
#  .cue  : CUE file. The preferred option. The actual image file is extracted
#          from the content of the cue file. If the file-name found inside the
#          cue is a relative path it is assumed that the bin/img file is stored
#          in the same directory as the cue file.
#
# .bin   : BIN/IMG files. In this case a temporary .cue file will be created
# .img     in the local directory and used for the conversion. This cue file
#          will assume that the bin/img file is just one single track of type
#          MODE2/2352
#
# .zip   : ZIP file. The ZIP file will be extracted into the local direcotry
#          and if a .cue file is found it will be used.
#
#
# The utility supports building and installing the games on various different
# target platforms:
#
# --psio-game-dir <path> : This specifies the path to where a PSIO sd card has
#                         been mounted. The games will be be installed as
#                         <path>/<game-title>/<game-title>.bin
# --psp-game-dir <path> : This specifies the path to where a PSP sd card has
#                         been mounted. The games will be converted into
#                         an EBOOT.PBP and will be installed as
#                         <path>/<game-id>/EBOOT.PBP
#                         The EBOOT.PBP will have a cover icon as well as a
#                         background image embedded.
# --retroarch-game-dir  : The directory where retroarch game images are to be
#                         installed.
# --retroarch-thumbnail-dir : Where the coverimage for retroarch should go.
#
#
# Examples:
# Assume I have connected my PSP with USB and it is shows up as :
#    /run/media/sahlberg/disk
#
# ./pop-fe.py --psp-game-dir=/run/media/sahlberg/disk/PSP/GAME/ /psx/Metal\ Gear\ Solid\ VR\ Missions.cue
#
#
# Multidisk games:
# If you specify more than one cue file then it is assumed that this is
# a multidisc game and we will use the first cue file to determine the
# game id and title to be used for the whole set.
# 
#
#
# During the conversion process the img/bin file will be temporarily converted
# into an ISO file as NORMAL01.iso in the current directory.
# This is in order to open the iso9660 image and read the system.cnf file
# to extract the game id.
# You can avoid/skip this step by forcing the game-id from the command line,
# using (example only):
#     --game-id=SLUS00957
#
# Game art and images are fetched from https://psxdatacenter.com/
# If a file ICON0.PNG is found in the game directory it assumed to be the
# cover image and thus we skip pulling it from psxdatacenter.
# Similarly, if PIC1.PNG is found then it is assumed to be a screenshot
# or background image and again we skip pulling this file from the site.
#
# --fetch-metadata
# This argument will download and install ICON0.PNG, PIC1.PNG as well as the
# game id and title in the directory where the game is stored.
# This requires that the game directory is writeable.
#
#
# https://psxdatacenter.com/
# https://www.psdevwiki.com/ps3/Eboot.PBP
# https://www.reddit.com/r/RetroArch/comments/ckqtzd/commandline_programs_to_convert_psx_cd_images_on/

from PIL import Image, ImageDraw, ImageFont
import argparse
import datetime
import io
import os
import re
import random
import struct
import sys
import iso9660      # python-pycdio
import requests
import requests_cache
import subprocess
import zipfile
from pathlib import Path

from gamedb import games
from bchunk import bchunk
from popstation import popstation

PSX_SITE = 'https://psxdatacenter.com/'

def get_gameid_from_iso():
    iso = iso9660.ISO9660.IFS(source='NORMAL01.iso')

    st = iso.stat('system.cnf', True)
    if st is None:
        raise Exception('Could not open system.cnf')

    buf = iso.seek_read(st['LSN'])
    iso.close()

    idx = buf[1].find('cdrom:')
    if idx < 0:
        raise Exception('Could not read system.cnf')

    buf = buf[1][idx:idx+50]
    idx = buf.find(';1')
    buf = buf[idx-11:idx]
    
    game_id = buf
    return game_id[:4] + game_id[5:8] + game_id[9:11]


def fetch_cached_file(path):
    ret = requests.get(PSX_SITE + path)
    print('get', PSX_SITE + path)
    if ret.status_code != 200:
        raise Exception('Failed to fetch file ', PSX_SITE + path)

    return ret.content.decode(ret.apparent_encoding)


def fetch_cached_binary(path):
    ret = requests.get(PSX_SITE + path, stream=True)
    if ret.status_code != 200:
        raise Exception('Failed to fetch file ', PSX_SITE + path)

    return ret.content

def get_game_from_gamelist(game_id):
    return fetch_cached_file(games[game_id]['url'])

def get_title_from_game(game_id):
    return games[game_id]['title']

def get_icon0_from_game(game_id, game):
    g = re.findall('images/covers/././%s.jpg' % game_id, game)
    return fetch_cached_binary(g[0])

def get_pic1_from_game(game_id, game):
    # Screenshots might be from a different release of the game
    # so we can not use game_id
    filter = 'images/screens/././.*/ss..jpg'
    return fetch_cached_binary(random.choice(re.findall(filter, game)))

def get_psio_cover(game_id):
    f = 'https://raw.githubusercontent.com/logi-26/psio-assist/main/covers/' + game_id + '.bmp'
    ret = requests.get(f, stream=True)
    if ret.status_code != 200:
        raise Exception('Failed to fetch file ', f)

    return ret.content

def get_first_bin_in_cue(cue):
    with open(cue, "r") as f:
        files = re.findall('".*"', f.read())
        return files[0][1:-1]

def add_image_text(image, title, idx):
    # Add a nice title text to the background image
    # Split it into separate lines
    #   for ' - '
    if idx:
        title = title + ' - (Disc %d of %d)' % idx
    print('Add image text: title:', title)
    strings = title.split(' - ')
    y = 18
    txt = Image.new("RGBA", image.size, (255,255,255,0))
    fnt = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSansMono.ttf", 20)
    d = ImageDraw.Draw(txt)
    
    for t in strings:
        ts = d.textsize(t, font=fnt)
        d.text((image.size[0] - ts[0], y), t, font=fnt,
               fill=(255,255,255,255))
        y = y + ts[1] + 2

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

def main(cue_file, cue, idx, p):
    bin = cue[0]['bin']
    s = cue_file.split('/')
    if len(s) > 1 and len(cue[0]['bin'].split('/')) == 1:
        bin = '/'.join(s[:-1]) + '/' + bin

    print('BIN:', bin)

    game = None
    game_id = None
    if args.game_id:
        game_id = args.game_id
    if not game_id:
        try:
            with open(create_path(bin, 'GAME_ID'), 'r') as d:
                game_id = d.read()
        except:
            True
    if not game_id:
        game_id = get_gameid_from_iso()
    print('Id:', game_id)

    game_title = None
    if args.title:
        game_title = args.title
    if not game_title:
        try:
            with open(create_path(bin, 'GAME_TITLE'), 'r') as d:
                game_title = d.read()
        except:
            True
    if not game_title:
        game_title = get_title_from_game(game_id[0:4].upper() + '-' + game_id[4:9])
    print('Title:', game_title)

    if args.fetch_metadata:
        print('fetching metadata')

        with open(create_path(bin, 'GAME_ID'), 'w') as d:
            d.write(game_id)
        with open(create_path(bin, 'GAME_TITLE'), 'w') as d:
            d.write(game_title)

        try:
            os.stat(create_path(bin, 'ICON0.PNG'))
            print('Already have ICON0.PNG')
        except:
            print('Fetching cover as ICON0.PNG')
            if not game:
                game = get_game_from_gamelist(game_id[0:4].upper() + '-' + game_id[4:9])
            icon0 = get_icon0_from_game(game_id[0:4].upper() + '-' + game_id[4:9], game)
            image = Image.open(io.BytesIO(icon0))
            image.save(create_path(bin, 'ICON0.PNG'), format='PNG')

        try:
            os.stat(create_path(bin, 'PIC1.PNG'))
            print('Already have PIC1.PNG')
        except:
            print('Fetching screenshot as PIC1.PNG')
            if not game:
                game = get_game_from_gamelist(game_id[0:4].upper() + '-' + game_id[4:9])
            pic1 = get_pic1_from_game(game_id[0:4] + '-' + game_id[4:9], game)
            image = Image.open(io.BytesIO(pic1))
            image.save(create_path(bin, 'PIC1.PNG'), format='PNG')

    if args.psio_game_dir:
        f = args.psio_game_dir + '/' + game_title
        try:
            os.mkdir(f)
        except:
            True

        g = game_title
        if idx:
            g = g + '-%d' % idx[0]
        g = g + '.bin'

        if idx:
            if idx[0] == 1:
                try:
                    os.unlink(f + '/MULTIDISC.LST')
                except:
                    True
            with open(f + '/MULTIDISC.LST', 'a+b') as d:
                d.write(bytes(g + chr(13) + chr(10), encoding='utf-8'))

        if not idx or idx[0] == 1:
            ifn = f + '/' + game_id[0:4] + '-' + game_id[4:9] + '.bmp'
            try:
                image = Image.open(create_path(bin, 'ICON0.PNG'))
                image = image.resize((80,84), Image.BILINEAR)
                image.save(ifn, format='BMP')
                print('Use existing ICON0.PNG as cover')
            except:
                print('Fetch cover for', game_title)
                image = get_psio_cover(game_id[0:4] + '-' + game_id[4:9])
                with open(ifn, 'wb') as d:
                    d.write(image)
            
        print('Installing', f + '/' + g)
        copy_file(bin, f + '/' + g)

        try:
            subprocess.call(['./cue2cu2.py', '--size', str(os.stat(bin).st_size), cue_file])
            cu2 = cue_file.split('/')[-1][:-4] + '.cu2'
            print('Created CU2:', cu2)
            copy_file(cu2, f + '/' + g[:-4] + '.cu2')
            os.unlink(cu2)
        except:
            True

    if args.psp_game_dir:
        if not idx or idx[0] == 1:
            p.game_id = game_id
            p.game_title = game_title
            print('game_id', p.game_id)
            print('game_title', p.game_title)
            try:
                image = Image.open(create_path(bin, 'ICON0.PNG'))
                print('Use existing ICON0.PNG as cover')
            except:
                print('Fetch cover for', p.game_title)
                if not game:
                    game = get_game_from_gamelist(p.game_id[0:4].upper() + '-' + p.game_id[4:9])
                icon0 = get_icon0_from_game(p.game_id[0:4].upper() + '-' + p.game_id[4:9], game)
                image = Image.open(io.BytesIO(icon0))

            image = image.resize((80,80), Image.BILINEAR)
            i = io.BytesIO()
            image.save(i, format='PNG')
            i.seek(0)
            p.icon0 = i.read()

            try:
                image = Image.open(create_path(bin, 'PIC1.PNG'))
                print('Use existing PIC1.PNG as background')
            except:
                print('Fetch screenshot for', p.game_title)
                if not game:
                    game = get_game_from_gamelist(p.game_id[0:4].upper() + '-' + p.game_id[4:9])
                pic1 = get_pic1_from_game(p.game_id[0:4] + '-' + p.game_id[4:9], game)
                image = Image.open(io.BytesIO(pic1))
            image = image.resize((480, 272), Image.BILINEAR).convert("RGBA")
            image = add_image_text(image, p.game_title, idx)

            i = io.BytesIO()
            image.save(i, format='PNG')
            i.seek(0)
            p.pic1 = i.read()

        print('Add image', bin)
        p.add_img(bin)

        if idx and idx[0] != idx[1]:
            return

        f = args.psp_game_dir + '/' + p.game_id
        print('Install EBOOT in', f)
        try:
            os.mkdir(f)
        except:
            True
            
        p.eboot = f + '/EBOOT.PBP'
        print('Create EBOOT at', p.eboot)
        p.create()
        
        return
    
    if args.retroarch_thumbnail_dir:
        g = game_title
        if idx:
            g = g + '-%d' % idx[0]
        if not game:
            game = get_game_from_gamelist(game_id[0:4].upper() + '-' + game_id[4:9])
        icon0 = get_icon0_from_game(game_id[0:4] + '-' + game_id[4:9], game)
        image = Image.open(io.BytesIO(icon0))
        try:
            os.stat(args.retroarch_thumbnail_dir + '/Named_Boxarts')
        except:
            os.mkdir(args.retroarch_thumbnail_dir + '/Named_Boxarts')
        image = image.resize((256,256), Image.BILINEAR)
        #The following characters in playlist titles must be replaced with _ in the corresponding thumbnail filename: &*/:`<>?\|
        f = args.retroarch_thumbnail_dir + '/Named_Boxarts/' + g + '.png'
        print('Save cover as', f)
        image.save(f, 'PNG')

        if not game:
            game = get_game_from_gamelist(game_id[0:4].upper() + '-' + game_id[4:9])
        pic1 = get_pic1_from_game(game_id[0:4] + '-' + game_id[4:9], game)
        image = Image.open(io.BytesIO(pic1))
        try:
            os.stat(args.retroarch_thumbnail_dir + '/Named_Snaps')
        except:
            os.mkdir(args.retroarch_thumbnail_dir + '/Named_Snaps')
        image = image.resize((512,256), Image.BILINEAR)
        #The following characters in playlist titles must be replaced with _ in the corresponding thumbnail filename: &*/:`<>?\|
        f = args.retroarch_thumbnail_dir + '/Named_Snaps/' + g + '.png'
        print('Save snap as', f)
        image.save(f, 'PNG')

    if args.retroarch_game_dir:
        g = game_title
        if idx:
            g = g + '-%d' % idx[0]
        f = args.retroarch_rom_dir + '/' + g + '.img'
        print('Installing', f)
        copy_file(bin, f)
        
                     
# ICON0 is the game cover
# PIC1 is background image/poster
#
if __name__ == "__main__":
    expire_after = datetime.timedelta(days=100)
    requests_cache.install_cache(str(Path.home()) + '/.pop-fe', expire_after=expire_after)

    parser = argparse.ArgumentParser()
    parser.add_argument('--retroarch-thumbnail-dir',
                    help='Where to store retroarch thumbnails')
    parser.add_argument('--retroarch-game-dir',
                    help='Where to store retroarch games')
    parser.add_argument('--psio-game-dir',
                    help='Where to store images for PSIO')
    parser.add_argument('--psp-game-dir',
                    help='Where to store PSP EBOOT.PBP')
    parser.add_argument('--fetch-metadata', action='store_true',
                    help='Just fetch metadata for the game')
    parser.add_argument('--game_id',
                        help='Force game_id for this iso.')
    parser.add_argument('--title',
                    help='Force title for this iso')
    parser.add_argument('files', nargs='*')
    args = parser.parse_args()
    
    if not args.files:
        print('You must specify at least one file to fetch images for')
        exit(1)

    try:
        os.unlink('NORMAL01.iso')
    except:
        True

    p = popstation()

    idx = None
    if len(args.files) > 1:
        idx = (1, len(args.files))
    for cue_file in args.files:
        zip = None
        print('Processing', cue_file, '...')

        if cue_file[-3:] == 'zip':
            print('This is a ZIP file. Uncompress the file.')
            zip = cue_file
            with zipfile.ZipFile(zip, 'r') as zf:
                for f in zf.namelist():
                    print('Extracting', f)
                    zf.extract(f)
                    if re.search('.cue$', f):
                        print('Found CUE file', f)
                        cue_file = f

        tmpcue = None
        if cue_file[-3:] == 'img' or cue_file[-3:] == 'bin':
            print('IMG or IMG file. Create a temporary cue file for it')
            tmpcue = 'TMP.cue'
            with open(tmpcue, "w") as f:
                f.write('FILE "%s" BINARY\n' % cue_file)
                f.write('  TRACK 01 MODE2/2352\n')
                f.write('    INDEX 01 00:00:00\n')

            cue_file = tmpcue

        if cue_file[-3:] != 'cue':
            print('%s is not a CUE file. Skipping' % cue_file)
            continue
        
        # We need to convert the first track to an ISO so we can open the
        # disk and read system.cnf
        # We only do this for the first disk of a multi-disk set.
        print('Convert CUE to a normal style ISO')
        bc = bchunk()
        bc.open(cue_file)
        bc.writetrack(0, 'NORMAL')

        main(cue_file, bc.cue, idx, p)
        if idx:
            idx = (idx[0] + 1, idx[1])
        if tmpcue:
            os.unlink(tmpcue)

        if zip:
            with zipfile.ZipFile(zip, 'r') as zf:
                for f in zf.namelist():
                    print('Remove temporary file', f)
                    os.unlink(f)

    try:
        os.unlink('NORMAL01.iso')
    except:
        True

