#!/usr/bin/env python
# coding: utf-8
#
# Auto theme for DOTPAINTING art
#
#

from PIL import Image, ImageDraw, ImageFont
import os
import sys

if sys.platform == 'win32':
    font = 'arial.ttf'
else:
    font = 'DejaVuSansMono.ttf'

def create_dotpainting_pic0(game_id, title):
    p0 = Image.new("RGB", (250, 140), (0,0,0))
    fnt = ImageFont.truetype(font, 12)
    d = ImageDraw.Draw(p0)

    off = 80
    y = 1
    t = '##############################'
    ts = d.textsize(t, font=fnt)
    d.text((off, y), t, font=fnt, fill=(255,128,128,255))
    y = y + ts[1] + 2
    
    strings = title.split(' - ')
    for t in strings:
        ts = d.textsize('#', font=fnt)
        d.text((off, y), '#', font=fnt, fill=(255,128,128,255))
        
        ts = d.textsize(t, font=fnt)
        d.text((off + 11, y), t, font=fnt,
               fill=(255,255,255,255))
        y = y + ts[1] + 2

    t = '##############################'
    ts = d.textsize(t, font=fnt)
    d.text((off, y), t, font=fnt, fill=(255,128,128,255))

    pic0 = Image.new("RGBA", (1000, 560), (255,255,255,0))
    d = ImageDraw.Draw(pic0)
    for i in range(250):
        for j in range(140):
            p = p0.getpixel((i,j))
            if p != (0,0,0):
                d.ellipse([(i * 4, j * 4), (i * 4 + 3, j * 4 + 3)], fill = p)

    return pic0

def create_dotpainting_pic1(game_id, icon0):
    icon0 = icon0.resize((120,120), Image.Resampling.BILINEAR)
    pic1 = Image.new("RGB", (1920, 1080), (0,0,0))
    d = ImageDraw.Draw(pic1)
    for i in range(120):
        for j in range(120):
            p = icon0.getpixel((i,j))
            d.ellipse([(i * 9 - 3, j * 9 - 3), (i * 9 + 4, j * 9 + 4)], fill = p)

    return pic1
    
