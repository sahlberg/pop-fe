#!/usr/bin/env python
# coding: utf-8
#
# Auto theme for ASCII art
#
#

from PIL import Image, ImageDraw, ImageFont
import os
import sys

if sys.platform == 'win32':
    font = 'arial.ttf'
else:
    font = 'DejaVuSansMono.ttf'

def create_ascii_pic0(game_id, title):
    pic0 = Image.new("RGBA", (250, 140), (255,255,255,0))
    fnt = ImageFont.truetype(font, 12)
    d = ImageDraw.Draw(pic0)

    off = 80
    y = 1
    t = '##############################'
    ts = d.textsize(t, font=fnt)
    d.text((off, y), t, font=fnt, fill=(128,255,128,255))
    y = y + ts[1] + 2
    
    strings = title.split(' - ')
    for t in strings:
        ts = d.textsize('#', font=fnt)
        d.text((off, y), '#', font=fnt, fill=(128,255,128,255))
        
        ts = d.textsize(t, font=fnt)
        d.text((off + 12, y), t, font=fnt,
               fill=(0,0,0,255))
        d.text((off + 11, y - 1), t, font=fnt,
               fill=(255,255,255,255))
        y = y + ts[1] + 2

    t = '##############################'
    ts = d.textsize(t, font=fnt)
    d.text((off, y), t, font=fnt, fill=(128,255,128,255))

    pic0 = pic0.resize((1000,560), Image.Resampling.NEAREST)
    return pic0

def create_ascii_pic1(game_id, icon0):
    AC = ["W", "#", "%", "?", "*", "+", ";", ":", ",", ".", " "]
    icon0 = icon0.convert("L").resize((120,120), Image.Resampling.BILINEAR)
    pic1 = Image.new("RGB", (1920, 1080), (0,0,0))
    fnt = ImageFont.truetype(font, 12)
    d = ImageDraw.Draw(pic1)
    for i in range(120):
        for j in range(120):
            p = icon0.getpixel((i,j))
            d.text((210 + i * 9, j * 9), AC[10 - p//25], font=fnt,
                   fill=(192,192,192,255))

    return pic1
    
