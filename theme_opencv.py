#!/usr/bin/env python
# coding: utf-8
#
# Auto theme for DOTPAINTING art
#
#

from PIL import Image, ImageDraw, ImageFont
import cv2
import io
import os
import sys

if sys.platform == 'win32':
    font = 'arial.ttf'
else:
    font = 'DejaVuSansMono.ttf'

def create_oilpainting_pic0(game_id, title, tmpfile):
    p0 = Image.new("RGB", (250, 140), (0,0,0))
    fnt = ImageFont.truetype(font, 12)
    d = ImageDraw.Draw(p0)

    off = 100
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

def create_oilpainting_pic1(game_id, icon0, tmpfile):
    icon0 = icon0.resize((1000,1000), Image.Resampling.BILINEAR)
    icon0.save(tmpfile, format='BMP')
    img = cv2.imread(tmpfile, cv2.IMREAD_COLOR)
    res = cv2.xphoto.oilPainting(img, 7, 1)
    cv2.imwrite(tmpfile, res)
    icon0 = Image.open(tmpfile)
    
    pic1 = Image.new("RGB", (1920, 1080), (0,0,0))
    Image.Image.paste(pic1, icon0, box=(100,0))
    
    return pic1
    
def create_watercolor_pic0(game_id, title, tmpfile):
    p0 = Image.new("RGB", (250, 140), (0,0,0))
    fnt = ImageFont.truetype(font, 12)
    d = ImageDraw.Draw(p0)

    off = 100
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

def create_watercolor_pic1(game_id, icon0, tmpfile):
    icon0 = icon0.resize((1000,1000), Image.Resampling.BILINEAR)
    icon0.save(tmpfile, format='BMP')
    img = cv2.imread(tmpfile, cv2.IMREAD_COLOR)
    res = cv2.stylization(img, sigma_s=60, sigma_r=0.6)
    cv2.imwrite(tmpfile, res)
    icon0 = Image.open(tmpfile)
    
    pic1 = Image.new("RGB", (1920, 1080), (0,0,0))
    Image.Image.paste(pic1, icon0, box=(100,0))

    return pic1
    
def create_colorsketch_pic0(game_id, title, tmpfile):
    p0 = Image.new("RGB", (250, 140), (0,0,0))
    fnt = ImageFont.truetype(font, 12)
    d = ImageDraw.Draw(p0)

    off = 100
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

def create_colorsketch_pic1(game_id, icon0, tmpfile):
    icon0.save(tmpfile, format='BMP')
    img = cv2.imread(tmpfile, cv2.IMREAD_COLOR)
    grey, color = cv2.pencilSketch(img, sigma_s=150, sigma_r=0.20, shade_factor=0.02)
    cv2.imwrite(tmpfile, color)
    icon0 = Image.open(tmpfile)
    icon0 = icon0.resize((1000,1000), Image.Resampling.NEAREST)

    pic1 = Image.new("RGB", (1920, 1080), (0,0,0))
    Image.Image.paste(pic1, icon0, box=(100,0))

    return pic1
    
