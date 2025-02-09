#!/usr/bin/python3
#!/usr/bin/env python

import argparse
import datetime
import io
import os
import pathlib
import pygubu
import re
import requests
import shutil
import subprocess
import tkinter as tk
import tkinter.ttk as ttk
from tkinterdnd2 import *
import zipfile


have_pytube = False
try:
    import pytubefix as pytube
    have_pytube = True
except:
    True

from PIL import Image, ImageDraw
from bchunk import bchunk
import importlib  
from gamedb import games, libcrypt, themes
try:
    import popfe
except:
    popfe = importlib.import_module("pop-fe")
from cue import parse_ccd, ccd2cue, write_cue

verbose = False
temp_files = []

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "pop-fe-ps3.ui"


class FinishedDialog(tk.Toplevel):
    def __init__(self, root):
        tk.Toplevel.__init__(self, root)
        label = tk.Label(self, text="Finished creating PKG")
        label.pack(fill="both", expand=True, padx=20, pady=20)

        button = tk.Button(self, text="Continue", command=self.destroy)
        button.pack(side="bottom")

class PopFePs3App:
    def __init__(self, master=None):
        self.myrect = None
        self.cue_file_orig = None
        self.cue_files = None
        self.cu2_files = None
        self.img_files = None
        self.disc_ids = None
        self.md5_sums = None
        self.real_disc_ids = None
        self.icon0 = None
        self.icon0_tk = None
        self.pic0 = None
        self.pic0_tk = None
        self.pic1 = None
        self.pic1_tk = None
        self.back = None
        self.disc = None
        self.pic0_disabled = 'off'
        self.pic1_bc = 'off'
        self.pic1_disabled = 'off'
        self.snd0_disabled = 'off'
        self.icon0_disc = 'off'
        self.preview_tk = None
        self.pkgdir = None
        self.data_track_only = 'off'
        self.configs = []
        self.subdir = 'pop-fe-ps3-work/'
        
        self.master = master
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object("top_frame", master)

        callbacks = {
            'on_icon0_clicked': self.on_icon0_clicked,
            'on_icon0_dropped': self.on_icon0_dropped,
            'on_icon0_from_disc': self.on_icon0_from_disc,
            'on_pic0_clicked': self.on_pic0_clicked,
            'on_pic0_dropped': self.on_pic0_dropped,
            'on_pic0_disabled': self.on_pic0_disabled,
            'on_pic1_clicked': self.on_pic1_clicked,
            'on_pic1_dropped': self.on_pic1_dropped,
            'on_pic1_disabled': self.on_pic1_disabled,
            'on_pic1_from_bc': self.on_pic1_from_bc,
            'on_snd0_disabled': self.on_snd0_disabled,
            'on_path_changed': self.on_path_changed,
            'on_dir_changed': self.on_dir_changed,
            'on_youtube_audio': self.on_youtube_audio,
            'on_create_pkg': self.on_create_pkg,
            'on_reset': self.on_reset,
            'on_theme_selected': self.on_theme_selected,
            'on_data_track_only': self.on_data_track_only,
            'on_force_pal': self.on_force_pal,
            'on_force_ntsc': self.on_force_ntsc,
            'on_force_newemu': self.on_force_newemu,
            'on_allow_swapdisc': self.on_allow_swapdisc,
        }

        builder.connect_callbacks(callbacks)
        c = self.builder.get_object('icon0_canvas', self.master)
        c.drop_target_register(DND_FILES)
        c.dnd_bind('<<Drop>>', self.on_icon0_dropped)
        c = self.builder.get_object('pic0_canvas', self.master)
        c.drop_target_register(DND_FILES)
        c.dnd_bind('<<Drop>>', self.on_pic0_dropped)
        c = self.builder.get_object('pic1_canvas', self.master)
        c.drop_target_register(DND_FILES)
        c.dnd_bind('<<Drop>>', self.on_pic1_dropped)

        self._theme = ''
        o = ['']
        for theme in themes:
            o.append(theme)
        self.builder.get_object('theme', self.master).configure(values=o)
        self.init_data()

    def __del__(self):
        global temp_files
        print('Delete temporary files') if verbose else None
        for f in temp_files:
            print('Deleting temp/dir file', f) if verbose else None
            try:
                os.unlink(f)
            except:
                try:
                    os.rmdir(f)
                except:
                    True
        temp_files = []  
        
    def init_data(self):
        global temp_files
        if temp_files:
            for f in temp_files:
                try:
                    os.unlink(f)
                except:
                    try:
                        os.rmdir(f)
                    except:
                        True

        temp_files = []  
        temp_files.append(self.subdir)
        shutil.rmtree(self.subdir, ignore_errors=True)
        os.mkdir(self.subdir)

        self.cue_files = []
        self.cu2_files = []
        self.img_files = []
        self.disc_ids = []
        self.md5_sums = []
        self.real_disc_ids = []
        self.icon0 = None
        self.icon0_tk = None
        self.pic0 = None
        self.pic0_tk = None
        self.pic1 = None
        self.pic1_tk = None
        self.back = None
        self.disc = None
        self.preview_tk = None
        self.configs = []
        
        for idx in range(1,6):
            self.builder.get_object('discid%d' % (idx), self.master).config(state='disabled')
            self.builder.get_object('disc' + str(idx), self.master).config(filetypes=[('Image files', ['.cue', '.ccd', '.img', '.zip', '.chd']), ('All Files', ['*.*', '*'])])
            self.builder.get_variable('disc%d_variable' % (idx)).set('')
            self.builder.get_variable('discid%d_variable' % (idx)).set('')
            self.builder.get_object('disc' + str(idx), self.master).config(state='disabled')
        self.builder.get_object('disc1', self.master).config(state='normal')
        self.builder.get_object('create_button', self.master).config(state='disabled')
        self.builder.get_object('youtube_button', self.master).config(state='disabled')
        self.builder.get_variable('title_variable').set('')
        self.builder.get_object('snd0', self.master).config(filetypes=[('Audio files', ['.wav']), ('All Files', ['*.*', '*'])])
        self.builder.get_variable('snd0_variable').set('')

    def update_preview(self):
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
        
        if self.pic0 and self.pic0.mode == 'P':
            self.pic0 = self.pic0.convert(mode='RGBA')
        c = self.builder.get_object('preview_canvas', self.master)
        if not self.pic1 or self.pic1_disabled == 'on':
            p1 = Image.new("RGBA", (382,216), (255,255,255,0))
        else:
            if self.pic1_bc == 'off':
                p1 = self.pic1.resize((382,216), Image.Resampling.HAMMING)
            else:
                p1 = self.back.resize((382,216), Image.Resampling.HAMMING)
        if self.pic0 and self.pic0_disabled == 'off':
            p0 = self.pic0.resize((int(p1.size[0] * 0.55) , int(p1.size[1] * 0.58)), Image.Resampling.HAMMING)
            if has_transparency(p0):
                Image.Image.paste(p1, p0, box=(148,79), mask=p0)
            else:
                Image.Image.paste(p1, p0, box=(148,79))
        i0 = None
        if self.icon0 and self.icon0_disc == 'off':
                i0 = self.icon0.resize((int(p1.size[0] * 0.10) , int(p1.size[0] * 0.10)), Image.Resampling.HAMMING)
        if self.disc and self.icon0_disc == 'on':
                i0 = self.disc.resize((int(p1.size[0] * 0.10) , int(p1.size[0] * 0.10)), Image.Resampling.HAMMING)
        if i0:
            if has_transparency(i0):
                Image.Image.paste(p1, i0, box=(100,79), mask=i0)
            else:
                Image.Image.paste(p1, i0, box=(100,79))
        temp_files.append(self.subdir + 'PREVIEW.PNG')
        p1.save(self.subdir + 'PREVIEW.PNG')
        self.preview_tk = tk.PhotoImage(file = self.subdir + 'PREVIEW.PNG')
        c = self.builder.get_object('preview_canvas', self.master)
        c.create_image(0, 0, image=self.preview_tk, anchor='nw')

    def on_theme_selected(self, event):
        self.master.config(cursor='watch')
        self._theme = self.builder.get_object('theme', self.master).get()
        self.update_assets()
        self.master.config(cursor='')

    def update_assets(self):
        if not self.disc_ids:
            return
        if not self.cue_file_orig:
            return
        disc_id = self.disc_ids[0]
        game = popfe.get_game_from_gamelist(disc_id)
        if self.snd0_disabled == 'off':
            snd0 = None
            print('Fetching SND0')
            if self._theme != '':
                snd0 = popfe.get_snd0_from_theme(self._theme, disc_id, 'pop-fe-ps3-work')
                if snd0:
                    temp_files.append(snd0)
            if not snd0 and disc_id in games and 'snd0' in games[disc_id]:
                snd0 = games[disc_id]['snd0']
            if snd0:
                self.builder.get_variable('snd0_variable').set(snd0)
                
        print('Fetching ICON0') if verbose else None
        self.icon0 = None
        if self._theme != '':
            print('Get icon0 from theme')
            self.icon0 = popfe.get_image_from_theme(self._theme, disc_id, 'pop-fe-ps3-work', 'ICON0.PNG')
            if not self.icon0:
                self.icon0 = popfe.get_image_from_theme(self._theme, disc_id, 'pop-fe-ps3-work', 'ICON0.png')
            if self.icon0:
                self.icon0 = self.icon0.crop(self.icon0.getbbox())
        if not self.icon0:
            self.icon0 = popfe.get_icon0_from_game(disc_id, game, self.cue_file_orig, self.subdir + 'ICON0.PNG', psn_frame_size=((176,176),(138,138)))
            
        if self.icon0:
            temp_files.append(self.subdir + 'ICON0.PNG')
            self.icon0.resize((80,80), Image.Resampling.HAMMING).save(self.subdir + 'ICON0.PNG')
            self.icon0_tk = tk.PhotoImage(file = self.subdir + 'ICON0.PNG')
            c = self.builder.get_object('icon0_canvas', self.master)
            c.create_image(0, 0, image=self.icon0_tk, anchor='nw')
            
        print('Fetching PIC0') if verbose else None
        self.pic0 = None
        if self._theme != '':
            self.pic0 = popfe.get_image_from_theme(self._theme, disc_id, 'pop-fe-ps3-work', 'PIC0.PNG')
            if not self.pic0:
                self.pic0 = popfe.get_image_from_theme(self._theme, disc_id, 'pop-fe-ps3-work', 'PIC0.png')
        if not self.pic0:
            self.pic0 = popfe.get_pic0_from_game(disc_id, game, self.cue_file_orig)
        if self.pic0:
            temp_files.append(self.subdir + 'PIC0.PNG')
            self.pic0.resize((128,80), Image.Resampling.HAMMING).save(self.subdir + 'PIC0.PNG')
            self.pic0_tk = tk.PhotoImage(file = self.subdir + 'PIC0.PNG')
            c = self.builder.get_object('pic0_canvas', self.master)
            c.create_image(0, 0, image=self.pic0_tk, anchor='nw')
            
        print('Fetching PIC1') if verbose else None
        self.pic1 = None
        if self._theme != '':
            self.pic1 = popfe.get_image_from_theme(self._theme, disc_id, 'pop-fe-ps3-work', 'PIC1.PNG')
            if not self.pic1:
                self.pic1 = popfe.get_image_from_theme(self._theme, disc_id, 'pop-fe-ps3-work', 'PIC1.png')
        if not self.pic1:
            self.pic1 = popfe.get_pic1_from_game(disc_id, game, self.cue_file_orig)
        if self.pic1:
            temp_files.append(self.subdir + 'PIC1.PNG')
            self.pic1.resize((128,80), Image.Resampling.HAMMING).save(self.subdir + 'PIC1.PNG')
            self.pic1_tk = tk.PhotoImage(file = self.subdir + 'PIC1.PNG')
            c = self.builder.get_object('pic1_canvas', self.master)
            c.create_image(0, 0, image=self.pic1_tk, anchor='nw')

        self.update_preview()
        
    def on_path_changed(self, event):
        cue_file = event.widget.cget('path')
        img_file = None
        if not len(cue_file):
            return

        self.master.config(cursor='watch')
        self.master.update()
        self.cue_file_orig = cue_file
        print('Processing', cue_file)  if verbose else None
        disc = event.widget.cget('title')
        print('Disc', disc)  if verbose else None
        idx = int(disc[1])

        cue_file , real_cue_file, img_file = popfe.process_disk_file(cue_file, idx, temp_files, subdir=self.subdir)
        self.cue_file_orig = real_cue_file
            
        print('Scanning for Game ID') if verbose else None
        tmp = self.subdir + 'TMP01.iso'
        disc_id, md5_sum = popfe.get_disc_id(cue_file, self.cue_file_orig, tmp)

        self.builder.get_variable('disci%s_variable' % (disc)).set(disc_id)

        self.img_files.append(img_file)
        self.disc_ids.append(disc_id)
        self.md5_sums.append(md5_sum)
        self.real_disc_ids.append(disc_id)
        self.cue_files.append(cue_file)
        self.configs.append(bytes())

        try:
            os.stat(self.cue_file_orig[:-3]+'ps3config').st_size
            print('Found an external config ', self.cue_file_orig[:-3]+'ps3config')
            with open(self.cue_file_orig[:-3]+'ps3config', 'rb') as f:
                      f.seek(8)
                      self.configs[-1] = self.configs[-1] + f.read()
                      print('Read external config ', self.cue_file_orig[:-3]+'ps3config')
        except:
            True
        if disc_id in games and 'ps3config' in games[disc_id]:
            print('Found an external config for', disc_id)
            with open(games[disc_id]['ps3config'], 'rb') as f:
                      f.seek(8)
                      self.configs[-1] = self.configs[-1] + f.read()
        if disc == 'd1':
            self.builder.get_object('discid1', self.master).config(state='normal')
            self.builder.get_variable('title_variable').set(popfe.get_title_from_game(disc_id))
            self.update_assets()
            
            self.builder.get_object('disc1', self.master).config(state='disabled')
            self.builder.get_object('disc2', self.master).config(state='normal')
            self.builder.get_object('create_button', self.master).config(state='normal')
            self.builder.get_object('youtube_button', self.master).config(state='normal')
            self.builder.get_object('disable_pic0', self.master).config(state='normal')
            self.builder.get_object('pic1_as_background', self.master).config(state='normal')
            self.builder.get_object('disc_as_icon0', self.master).config(state='normal')
        elif disc == 'd2':
            self.builder.get_object('discid2', self.master).config(state='normal')
            self.builder.get_object('disc2', self.master).config(state='disabled')
            self.builder.get_object('disc3', self.master).config(state='normal')
        elif disc == 'd3':
            self.builder.get_object('discid3', self.master).config(state='normal')
            self.builder.get_object('disc3', self.master).config(state='disabled')
            self.builder.get_object('disc4', self.master).config(state='normal')
        elif disc == 'd4':
            self.builder.get_object('discid4', self.master).config(state='normal')
            self.builder.get_object('disc4', self.master).config(state='disabled')
            self.builder.get_object('disc5', self.master).config(state='normal')
        elif disc == 'd5':
            self.builder.get_object('discid5', self.master).config(state='normal')
            self.builder.get_object('disc5', self.master).config(state='disabled')
        print('Finished processing disc') if verbose else None
        self.master.config(cursor='')


    def on_icon0_dropped(self, event):
        self.master.config(cursor='watch')
        self.master.update()
        # try to open it as a file
        self.icon0_tk = None
        try:
            os.stat(event.data)
            self.icon0 = Image.open(event.data)
        except:
            self.icon0 = None
        # if that failed, check if it was a link
        if not self.icon0:
            try:
                _s = event.data
                _p = _s.find('src="')
                if _p < 0:
                    raise Exception('Not a HTTP link')
                _s = _s[_p + 5:]
                _p = _s.find('"')
                if _p < 0:
                    raise Exception('Not a HTTP link')
                _s = _s[:_p]
                ret = requests.get(_s, stream=True)
                if ret.status_code != 200:
                    raise Exception('Failed to fetch file ', _s)
                self.icon0 = Image.open(io.BytesIO(ret.content))
            except:
                True

        self.master.config(cursor='')
        if not self.icon0:
            return
        temp_files.append(self.subdir + 'ICON0.PNG')
        self.icon0.resize((80,80), Image.Resampling.HAMMING).save(self.subdir + 'ICON0.PNG')
        self.icon0_tk = tk.PhotoImage(file = self.subdir + 'ICON0.PNG')
        c = self.builder.get_object('icon0_canvas', self.master)
        c.create_image(0, 0, image=self.icon0_tk, anchor='nw')
        self.update_preview()
        
    def on_icon0_clicked(self, event):
        filetypes = [
            ('Image files', ['.png', '.PNG', '.jpg', '.JPG']),
            ('All Files', ['*.*', '*'])]
        path = tk.filedialog.askopenfilename(title='Select image for COVER',filetypes=filetypes)
        try:
            os.stat(path)
            self.icon0 = Image.open(path)
        except:
            return
        temp_files.append(self.subdir + 'ICON0.PNG')
        self.icon0.resize((80,80), Image.Resampling.HAMMING).save(self.subdir + 'ICON0.PNG')
        self.icon0_tk = tk.PhotoImage(file = self.subdir + 'ICON0.PNG')
        c = self.builder.get_object('icon0_canvas', self.master)
        c.create_image(0, 0, image=self.icon0_tk, anchor='nw')
        self.update_preview()

    def on_pic0_dropped(self, event):
        self.master.config(cursor='watch')
        self.master.update()
        # try to open it as a file
        self.pic0_tk = None
        try:
            os.stat(event.data)
            self.pic0 = Image.open(event.data)
        except:
            self.pic0 = None
        # if that failed, check if it was a link
        if not self.pic0:
            try:
                _s = event.data
                _p = _s.find('src="')
                if _p < 0:
                    raise Exception('Not a HTTP link')
                _s = _s[_p + 5:]
                _p = _s.find('"')
                if _p < 0:
                    raise Exception('Not a HTTP link')
                _s = _s[:_p]
                ret = requests.get(_s, stream=True)
                if ret.status_code != 200:
                    raise Exception('Failed to fetch file ', _s)
                self.pic0 = Image.open(io.BytesIO(ret.content))
            except:
                True

        self.master.config(cursor='')
        if not self.pic0:
            return
        temp_files.append(self.subdir + 'PIC0.PNG')
        self.pic0.resize((128,80), Image.Resampling.HAMMING).save(self.subdir + 'PIC0.PNG')
        self.pic0_tk = tk.PhotoImage(file = self.subdir + 'PIC0.PNG')
        c = self.builder.get_object('pic0_canvas', self.master)
        c.create_image(0, 0, image=self.pic0_tk, anchor='nw')
        self.update_preview()
        
    def on_pic0_clicked(self, event):
        filetypes = [
            ('Image files', ['.png', '.PNG', '.jpg', '.JPG']),
            ('All Files', ['*.*', '*'])]
        path = tk.filedialog.askopenfilename(title='Select image for PIC0',filetypes=filetypes)
        try:
            os.stat(path)
            self.pic0 = Image.open(path)
        except:
            return
        temp_files.append(self.subdir + 'PIC0.PNG')
        self.pic0.resize((128,80), Image.Resampling.HAMMING).save(self.subdir + 'PIC0.PNG')
        self.pic0_tk = tk.PhotoImage(file = self.subdir + 'PIC0.PNG')
        c = self.builder.get_object('pic0_canvas', self.master)
        c.create_image(0, 0, image=self.pic0_tk, anchor='nw')
        self.update_preview()

    def on_pic1_dropped(self, event):
        self.master.config(cursor='watch')
        self.master.update()
        # try to open it as a file
        self.pic1_tk = None
        try:
            os.stat(event.data)
            self.pic1 = Image.open(event.data)
        except:
            self.pic1 = None
        # if that failed, check if it was a link
        if not self.pic1:
            try:
                _s = event.data
                _p = _s.find('src="')
                if _p < 0:
                    raise Exception('Not a HTTP link')
                _s = _s[_p + 5:]
                _p = _s.find('"')
                if _p < 0:
                    raise Exception('Not a HTTP link')
                _s = _s[:_p]
                ret = requests.get(_s, stream=True)
                if ret.status_code != 200:
                    raise Exception('Failed to fetch file ', _s)
                self.pic1 = Image.open(io.BytesIO(ret.content))
            except:
                True

        self.master.config(cursor='')
        if not self.pic1:
            return
        temp_files.append(self.subdir + 'PIC1.PNG')
        self.pic1.resize((128,80), Image.Resampling.HAMMING).save(self.subdir + 'PIC1.PNG')
        self.pic1_tk = tk.PhotoImage(file = self.subdir + 'PIC1.PNG')
        c = self.builder.get_object('pic1_canvas', self.master)
        c.create_image(0, 0, image=self.pic1_tk, anchor='nw')
        self.update_preview()
        
    def on_pic1_clicked(self, event):
        filetypes = [
            ('Image files', ['.png', '.PNG', '.jpg', '.JPG']),
            ('All Files', ['*.*', '*'])]
        path = tk.filedialog.askopenfilename(title='Select image for PIC1',filetypes=filetypes)
        try:
            os.stat(path)
            self.pic1 = Image.open(path)
        except:
            return
        temp_files.append(self.subdir + 'PIC1.PNG')
        self.pic1.resize((128,80), Image.Resampling.HAMMING).save(self.subdir + 'PIC1.PNG')
        self.pic1_tk = tk.PhotoImage(file = self.subdir + 'PIC1.PNG')
        c = self.builder.get_object('pic1_canvas', self.master)
        c.create_image(0, 0, image=self.pic1_tk, anchor='nw')
        self.update_preview()

    def on_force_pal(self):
        if self.builder.get_variable('force_pal_variable').get() == 'on':
            self.builder.get_variable('force_ntsc_variable').set('off')
            
    def on_force_ntsc(self):
        if self.builder.get_variable('force_ntsc_variable').get() == 'on':
            self.builder.get_variable('force_pal_variable').set('off')
        
    def on_force_newemu(self):
        True
        
    def on_allow_swapdisc(self):
        True
        
    def on_data_track_only(self):
        self.data_track_only = self.builder.get_variable('data_track_only_variable').get()
        self.update_preview()

    def on_pic0_disabled(self):
        self.pic0_disabled = self.builder.get_variable('pic0_disabled_variable').get()
        self.update_preview()

    def on_pic1_disabled(self):
        self.pic1_disabled = self.builder.get_variable('pic1_disabled_variable').get()
        self.update_preview()

    def on_snd0_disabled(self):
        self.snd0_disabled = self.builder.get_variable('snd0_disabled_variable').get()

    def on_icon0_from_disc(self):
        self.icon0_disc = self.builder.get_variable('disc_as_icon0_variable').get()
        if not self.disc and self.disc_ids:
            disc_id = self.disc_ids[0]
            game = popfe.get_game_from_gamelist(disc_id)
            self.master.config(cursor='watch')
            self.master.update()
            d = popfe.get_icon0_from_disc(disc_id, game, self.cue_files[0], 'DISC.PNG')
            size = (176,176)
            d = d.resize(size, Image.Resampling.HAMMING)
            bigsize = (d.size[0] * 3, d.size[1] * 3)
            mask = Image.new('L', bigsize, 0)
            draw = ImageDraw.Draw(mask) 
            draw.ellipse((0, 0) + bigsize, fill=255)
            mask = mask.resize(d.size, Image.ANTIALIAS)
            d.putalpha(mask)
            self.disc = d
            self.master.config(cursor='')

        self.builder.get_object('icon0_or_disc', self.master).config(text='COVER' if self.icon0_disc == 'off' else 'DISC')
        if self.icon0_disc == 'off':
            self.icon0.resize((80,80), Image.Resampling.HAMMING).save(self.subdir + 'ICON0.PNG')
        else:
            self.disc.resize((80,80), Image.Resampling.HAMMING).save(self.subdir + 'ICON0.PNG')
        self.icon0_tk = tk.PhotoImage(file = self.subdir + 'ICON0.PNG')
        c = self.builder.get_object('icon0_canvas', self.master)
        c.create_image(0, 0, image=self.icon0_tk, anchor='nw')
        
        self.update_preview()
            
    def on_pic1_from_bc(self):
        self.pic1_bc = self.builder.get_variable('bc_for_pic1_variable').get()
        if not self.back and self.disc_ids:
            disc_id = self.disc_ids[0]
            game = popfe.get_game_from_gamelist(disc_id)
            self.master.config(cursor='watch')
            self.master.update()
            self.back = popfe.get_pic1_from_bc(disc_id, game, self.cue_files[0])
            self.master.config(cursor='')
        self.builder.get_object('pic1_or_back', self.master).config(text='PIC1' if self.pic1_bc == 'off' else 'BACK')
        if self.pic1_bc == 'off':
            self.pic1.resize((128,80), Image.Resampling.HAMMING).save(self.subdir + 'PIC1.PNG')
        else:
            self.back.resize((128,80), Image.Resampling.HAMMING).save(self.subdir + 'PIC1.PNG')
        self.pic1_tk = tk.PhotoImage(file = self.subdir + 'PIC1.PNG')
        c = self.builder.get_object('pic1_canvas', self.master)
        c.create_image(0, 0, image=self.pic1_tk, anchor='nw')
        
        self.update_preview()

    def on_dir_changed(self, event):
        self.pkgdir = event.widget.cget('path')
        # PKG in print()

    def on_youtube_audio(self):
        if not have_pytube:
            return
        self.master.config(cursor='watch')
        a = pytube.contrib.search.Search(self.builder.get_variable('title_variable').get() + ' ps1 ost')
        if a:
            self.builder.get_variable('snd0_variable').set('https://www.youtube.com/watch?v=' + a.results[0].video_id)
           
        self.master.config(cursor='')

    def on_create_pkg(self):        
        pkg = self.builder.get_variable('pkgfile_variable').get()
        pkgdir = self.builder.get_variable('pkgdir_variable').get()
        if len(pkg) == 0:
            pkg = 'game.pkg'
        if len(pkgdir):
            pkg = pkgdir + '/' + pkg
        print('Creating ' + pkg)
        disc_ids = []
        for idx in range(len(self.cue_files)):
            d = self.builder.get_variable('discid%d_variable' % (idx + 1)).get()
            disc_ids.append(d)

        disc_id = disc_ids[0]
        title = self.builder.get_variable('title_variable').get()
        print('DISC', disc_id)
        print('TITLE', title)
        resolution = 1
        magic_word = []
        subchannels = []
        for idx in range(len(self.cue_files)):
            if self.real_disc_ids[idx] in libcrypt:
                magic_word.append(libcrypt[self.real_disc_ids[idx]]['magic_word'])
                subchannels.append(popfe.generate_subchannels(libcrypt[self.real_disc_ids[idx]]['magic_word']))
            else:
                magic_word.append(0)
                subchannels.append(None)
                
        if disc_id[:3] == 'SLE' or disc_id[:3] == 'SCE':
            print('SLES/SCES PAL game. Default resolution set to 2 (640x512)') if verbose else None
            resolution = 2
        if self.builder.get_variable('force_pal_variable').get() == 'on':
            resolution = 2
        if self.builder.get_variable('force_ntsc_variable').get() == 'on':
            resolution = 1
            for idx in range(len(self.cue_files)):
                self.configs[idx] = popfe.force_ntsc_config(self.configs[idx])

        self.master.config(cursor='watch')
        self.master.update()

        snd0 = None
        if self.snd0_disabled == 'off':
            snd0 = self.builder.get_variable('snd0_variable').get()
            if snd0[:24] == 'https://www.youtube.com/':
                snd0 = popfe.get_snd0_from_link(snd0, subdir=self.subdir)
                if snd0:
                    temp_files.append(snd0)

        p1 = self.pic1 if self.pic1_bc=='off' else self.back
        if self.pic1_disabled == 'on':
            p1 = None

        #
        # Apply all PPF fixes we might need
        #
        self.cue_files, self.img_files = popfe.apply_ppf_fixes(self.real_disc_ids, self.cue_files, self.img_files, self.md5_sums, self.subdir)

        self.cu2_files = popfe.generate_cu2_files(self.cue_files, self.img_files, self.subdir)
        
        aea_files, extra_data_tracks = popfe.generate_aea_files(self.cue_files, self.img_files, self.subdir)
        if extra_data_tracks:
            self.data_track_only = 'on'
        
        if self.builder.get_variable('allow_discswap_variable').get() == 'on':
            print('Enable swapdisc for all discs')
            for idx in range(len(self.cue_files)):
                self.configs[idx] = bytes([0x12, 0x00, 0x00, 0x00, 0x20,  0x00, 0x00, 0x00])

        #
        # Force NEWEMU
        #
        if self.builder.get_variable('force_newemu_variable').get() == 'on':
            print('Forcing ps1_newemu for all discs')
            for idx in range(len(self.cue_files)):
                self.configs[idx] = bytes([0x38, 0x00, 0x00, 0x00, 0x02,  0x00, 0x00, 0x00])
            
        popfe.create_ps3(pkg, disc_ids, title,
                         self.icon0 if self.icon0_disc=='off' else self.disc,
                         self.pic0 if self.pic0_disabled =='off' else None,
                         p1,
                         self.cue_files, self.cu2_files,
                         self.img_files, [], aea_files, magic_word,
                         resolution, subdir=self.subdir, snd0=snd0,
                         subchannels=subchannels,
                         whole_disk=True if self.data_track_only=='off' else False,
                         configs=self.configs)
        self.master.config(cursor='')

        d = FinishedDialog(self.master)
        self.master.wait_window(d)
        self.init_data()

    def on_reset(self):
        self.init_data()

        
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help='Verbose')
    args = parser.parse_args()

    if args.v:
        verbose = True

    root = TkinterDnD.Tk()
    app = PopFePs3App(root)
    root.title('pop-fe PS3')
    root.mainloop()
    
