#!/usr/bin/env python
# coding: utf-8
#
# A utility to automate building and installing PSX games onto different
# systems.
# The current directory where you run this utility from needs to be writable
# so that we can use it to store temporary files during the conversing process.

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
from vmp import encode_vmp
from pathlib import Path

from gamedb import games
from bchunk import bchunk
from popstation import popstation

PSX_SITE = 'https://psxdatacenter.com/'
verbose = False
font = '/usr/share/fonts/dejavu/DejaVuSansMono.ttf'

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
    print('get', PSX_SITE + path) if verbose else None
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

def add_image_text(image, title, game_id):
    # Add a nice title text to the background image
    # Split it into separate lines
    #   for ' - '
    print('Add image text: title:', title) if verbose else None
    strings = title.split(' - ')
    y = 18
    txt = Image.new("RGBA", image.size, (255,255,255,0))
    fnt = ImageFont.truetype(font, 20)
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
    
        image = Image.open(io.BytesIO(icon0))
        image = image.resize((256,256), Image.BILINEAR)
        #The following characters in playlist titles must be replaced with _ in the corresponding thumbnail filename: &*/:`<>?\|
        f = args.retroarch_thumbnail_dir + '/Named_Boxarts/' + game_title + '.png'
        print('Save cover as', f) if verbose else None
        image.save(f, 'PNG')

        image = Image.open(io.BytesIO(pic1))
        try:
            os.stat(args.retroarch_thumbnail_dir + '/Named_Snaps')
        except:
            os.mkdir(args.retroarch_thumbnail_dir + '/Named_Snaps')
        image = image.resize((512,256), Image.BILINEAR)
        #The following characters in playlist titles must be replaced with _ in the corresponding thumbnail filename: &*/:`<>?\|
        f = args.retroarch_thumbnail_dir + '/Named_Snaps/' + game_title + '.png'
        print('Save snap as', f) if verbose else None
        image.save(f, 'PNG')


def create_metadata(img, game_id, game_title, icon0, pic1):
    print('fetching metadata for', game_id) if verbose else None

    with open(create_path(img, 'GAME_ID'), 'w') as d:
        d.write(game_id)
    with open(create_path(img, 'GAME_TITLE'), 'w') as d:
        d.write(game_title)
    with open(create_path(img, 'ICON0.PNG'), 'wb') as d:
        d.write(icon0)
    with open(create_path(img, 'PIC1.PNG'), 'wb') as d:
        d.write(pic1)
        
        
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
                s = cue.split('/')
                if len(s) > 1:
                    f = '/'.join(s[:-1]) + '/' + f
                img_files.append(f)
    return img_files


def create_retroarch(dest, game_title, cue_files, img_files):
    with open(dest + '/' + game_title + '.m3u', 'wb') as md:
        for i in range(len(img_files)):
            g = game_title
            g = g + '-%d' % i + '.img'
            md.write(bytes(g + chr(13) + chr(10), encoding='utf-8'))

            f = dest + '/' + g
            print('Installing', f) if verbose else None
            copy_file(img_files[i], f)


def create_psio(dest, game_id, game_title, icon0, cue_files, img_files):
    try:
        os.stat('./cue2cu2.py')
    except:
        raise Exception('PSIO prefers CU2 files but cue2cu2.pu is not installed. See README file for instructions on how to install cue2cu2.')
    
    f = dest + '/' + game_title
    try:
        os.mkdir(f)
    except:
        True

    with open(f + '/' + game_id[0:4] + '-' + game_id[4:9] + '.bmp', 'wb') as d:
        image = Image.open(io.BytesIO(icon0))
        image = image.resize((80,84), Image.BILINEAR)
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

            try:
                subprocess.call(['./cue2cu2.py', '--size', str(os.stat(img_files[i]).st_size), cue_files[i]])
                cu2 = img_files[i].split('/')[-1][:-4] + '.cu2'
                copy_file(cu2, f + '/' + g[:-4] + '.cu2')
                os.unlink(cu2)
            except:
                True


def create_psp(dest, game_id, game_title, icon0, pic1, cue_files, img_files, mem_cards):
    print('Create PSP EBOOT.PBP for', game_title) if verbose else None

    p = popstation()
    p.verbose = verbose
    p.game_id = game_id
    p.game_title = game_title
    p.icon0 = icon0
    p.pic1 = pic1

    for f in img_files:
        print('Add image', f) if verbose else None
        p.add_img(f)

    f = dest + '/PSP/GAME/' + p.game_id
    print('Install EBOOT in', f) if verbose else None
    try:
        os.mkdir(f)
    except:
        True
            
    p.eboot = f + '/EBOOT.PBP'
    print('Create EBOOT.PBP at', p.eboot)
    p.create()
    os.sync()

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
        print('1, Remove the PSP')
        print('2, Start the game to create the SAVEDATA directory')
        print('   and then quit the game.')
        print('3, Reconnect the PSP')
        print('4, Run this command to finish installing the memory cards:')
        print('')
        print('./pop-fe.py --psp-dir=%s --game_id=%s --psp-install-memory-card' % (dest, game_id))
        print('###################################################')
        print('###################################################')
        os.sync()

        
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
    os.sync()

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
    

# ICON0 is the game cover
# PIC1 is background image/poster
#
if __name__ == "__main__":
    expire_after = datetime.timedelta(days=100)
    requests_cache.install_cache(str(Path.home()) + '/.pop-fe', expire_after=expire_after)

    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help='Verbose')
    parser.add_argument('--retroarch-thumbnail-dir',
                    help='Where to store retroarch thumbnails')
    parser.add_argument('--retroarch-game-dir',
                    help='Where to store retroarch games')
    parser.add_argument('--psio-dir',
                    help='Where to store images for PSIO')
    parser.add_argument('--psp-dir',
                    help='Where the PSP memory card is mounted')
    parser.add_argument('--psp-install-memory-card', action='store_true',
                        help='Finish installing a PSX memory card after '
                        'running the game at least once')
    parser.add_argument('--fetch-metadata', action='store_true',
                    help='Just fetch metadata for the game')
    parser.add_argument('--game_id',
                        help='Force game_id for this iso.')
    parser.add_argument('--title',
                    help='Force title for this iso')
    parser.add_argument('files', nargs='*')
    args = parser.parse_args()

    if args.v:
        verbose = True

    if not args.files and not args.psp_install_memory_card:
        print('You must specify at least one file to fetch images for')
        exit(1)

    try:
        os.unlink('NORMAL01.iso')
    except:
        True

    idx = None
    temp_files = []
    cue_files = []
    img_files = []
    mem_cards = []
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
            tmpcue = 'TMP%d.cue' % (0 if not idx else idx[0])
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
        if len(i) > 1:
            raise Exception('Can not handle disks that consists of separate files per track yet.')
        img_files.append(i[0])
        cue_files.append(cue_file)
        
        if idx:
            idx = (idx[0] + 1, idx[1])

    if args.psp_install_memory_card:
        install_psp_mc(args.psp_dir, args.game_id, mem_cards)
        quit()
            
    # We need to convert the first track of the first ISO so we can open the
    # disk and read system.cnf
    # We only do this for the first disk of a multi-disk set.
    print('Convert CUE to a normal style ISO') if verbose else None
    bc = bchunk()
    bc.verbose = args.v
    bc.open(cue_files[0])
    bc.writetrack(0, 'NORMAL')
    temp_files.append('NORMAL01.iso')

    game_id = None
    if args.game_id:
        game_id = args.game_id
    if not game_id:
        try:
            with open(create_path(img_files[0], 'GAME_ID'), 'r') as d:
                game_id = d.read()
        except:
            True
    if not game_id:
        game_id = get_gameid_from_iso()

    game_title = None
    if args.title:
        game_title = args.title
    if not game_title:
        try:
            with open(create_path(img_files[0], 'GAME_TITLE'), 'r') as d:
                game_title = d.read()
        except:
            True
    if not game_title:
        game_title = get_title_from_game(game_id[0:4].upper() + '-' + game_id[4:9])

    game = None

    # ICON0.PNG
    try:
        image = Image.open(create_path(img_files[0], 'ICON0.PNG'))
        print('Use existing ICON0.PNG as cover') if verbose else None
    except:
        print('Fetch cover for', game_title) if verbose else None
        if not game:
            game = get_game_from_gamelist(game_id[0:4].upper() + '-' + game_id[4:9])
        icon0 = get_icon0_from_game(game_id[0:4].upper() + '-' + game_id[4:9], game)
        image = Image.open(io.BytesIO(icon0))
    image = image.resize((80,80), Image.BILINEAR)
    i = io.BytesIO()
    image.save(i, format='PNG')
    i.seek(0)
    icon0 = i.read()

    # PIC1.PNG
    try:
        image = Image.open(create_path(img_files[0], 'PIC1.PNG'))
        print('Use existing PIC1.PNG as background') if verbose else None
    except:
        print('Fetch screenshot for', game_title) if verbose else None
        if not game:
            game = get_game_from_gamelist(game_id[0:4].upper() + '-' + game_id[4:9])
        pic1 = get_pic1_from_game(game_id[0:4] + '-' + game_id[4:9], game)
        image = Image.open(io.BytesIO(pic1))
    image = image.resize((480, 272), Image.BILINEAR).convert("RGBA")
    image = add_image_text(image, game_title, game_id)
    i = io.BytesIO()
    image.save(i, format='PNG')
    i.seek(0)
    pic1 = i.read()
    
    print('Id:', game_id)
    print('Title:', game_title)
    print('Cue Files', cue_files) if verbose else None
    print('Imb Files', img_files) if verbose else None

    if args.psp_dir:
        create_psp(args.psp_dir, game_id, game_title, icon0, pic1, cue_files, img_files, mem_cards)
    if args.fetch_metadata:
        create_metadata(img_files[0], game_id, game_title, icon0, pic1)
    if args.psio_dir:
        create_psio(args.psio_dir, game_id, game_title, icon0, cue_files, img_files)
    if args.retroarch_game_dir:
        create_retroarch(args.retroarch_game_dir, game_title, cue_files, img_files)
    if args.retroarch_thumbnail_dir:
        create_retroarch_thumbnail(args.retroarch_thumbnail_dir, game_title, icon0, pic1)

    for f in temp_files:
        print('Deleting temp file', f) if verbose else None
        os.unlink(f)

