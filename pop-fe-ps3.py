#!/usr/bin/python3
#!/usr/bin/env python

import argparse
import datetime
import io
import os
import pathlib
import pygubu
import requests
import requests_cache
import subprocess
import tkinter as tk
import tkinter.ttk as ttk
from tkinterdnd2 import *

have_pytube = False
try:
    import pytube
    have_pytube = True
except:
    True

from PIL import Image, ImageDraw
from bchunk import bchunk
import importlib  
from gamedb import games, libcrypt, themes
popfe = importlib.import_module("pop-fe")

verbose = False
temp_files = []

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "pop-fe-ps3.ui"

def get_disc_id(cue, tmp):
    print('Convert ' + cue + ' to a normal style ISO') if verbose else None
    bc = bchunk()
    bc.verbose = False
    bc.open(cue)
    bc.writetrack(0, tmp)

    gid = popfe.get_gameid_from_iso(tmp + '01.iso')
    return gid


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
        self.icon0_disc = 'off'
        self.square_icon0 = 'off'
        self.preview_tk = None
        self.pkgdir = None
        
        self.master = master
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object("top_frame", master)

        callbacks = {
            'on_icon0_clicked': self.on_icon0_clicked,
            'on_icon0_dropped': self.on_icon0_dropped,
            'on_icon0_from_disc': self.on_icon0_from_disc,
            'on_square_icon0': self.on_square_icon0,
            'on_pic0_clicked': self.on_pic0_clicked,
            'on_pic0_dropped': self.on_pic0_dropped,
            'on_pic0_disabled': self.on_pic0_disabled,
            'on_pic1_clicked': self.on_pic1_clicked,
            'on_pic1_dropped': self.on_pic1_dropped,
            'on_pic1_from_bc': self.on_pic1_from_bc,
            'on_path_changed': self.on_path_changed,
            'on_dir_changed': self.on_dir_changed,
            'on_youtube_audio': self.on_youtube_audio,
            'on_create_pkg': self.on_create_pkg,
            'on_reset': self.on_reset,
            'on_theme_selected': self.on_theme_selected,
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
        temp_files.append('pop-fe-ps3-work')
        try:
            os.mkdir('pop-fe-ps3-work')
        except:
            True
        self.cue_files = []
        self.cu2_files = []
        self.img_files = []
        self.disc_ids = []
        self.icon0 = None
        self.icon0_tk = None
        self.pic0 = None
        self.pic0_tk = None
        self.pic1 = None
        self.pic1_tk = None
        self.back = None
        self.disc = None
        self.preview_tk = None
        self.pkgdir = None
        
        for idx in range(1,6):
            self.builder.get_object('discid%d' % (idx), self.master).config(state='disabled')
        for idx in range(1,5):
            self.builder.get_object('disc' + str(idx), self.master).config(filetypes=[('Image files', ['.cue', '.bin', '.img']), ('All Files', ['*.*', '*'])])
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
        
        if not self.pic1:
            return
        if self.pic0 and self.pic0.mode == 'P':
            self.pic0 = self.pic0.convert(mode='RGBA')
        c = self.builder.get_object('preview_canvas', self.master)
        if self.pic1_bc == 'off':
            p1 = self.pic1.resize((382,216), Image.BILINEAR)
        else:
            p1 = self.back.resize((382,216), Image.BILINEAR)
        if self.pic0 and self.pic0_disabled == 'off':
            p0 = self.pic0.resize((int(p1.size[0] * 0.55) , int(p1.size[1] * 0.58)), Image.BILINEAR)
            if has_transparency(p0):
                Image.Image.paste(p1, p0, box=(148,79), mask=p0)
            else:
                Image.Image.paste(p1, p0, box=(148,79))
        if self.icon0:
            if self.icon0_disc == 'off':
                i0 = self.icon0.resize((int(p1.size[0] * 0.10) , int(p1.size[0] * 0.10)), Image.BILINEAR)
            else:
                i0 = self.disc.resize((int(p1.size[0] * 0.10) , int(p1.size[0] * 0.10)), Image.BILINEAR)
            if has_transparency(i0):
                Image.Image.paste(p1, i0, box=(100,79), mask=i0)
            else:
                Image.Image.paste(p1, i0, box=(100,79))
        temp_files.append('pop-fe-ps3-work/PREVIEW.PNG')
        p1.save('pop-fe-ps3-work/PREVIEW.PNG')
        self.preview_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/PREVIEW.PNG')
        c = self.builder.get_object('preview_canvas', self.master)
        c.create_image(0, 0, image=self.preview_tk, anchor='nw')

    def on_theme_selected(self, event):
        self._theme = self.builder.get_object('theme', self.master).get()
        if self._theme:
            self.square_icon0 = 'on' if themes[self._theme]['square_icon0'] else 'off'
        self.builder.get_variable('square_icon0_variable').set(self.square_icon0)
        self.update_assets()

    def update_assets(self):
        if not self.disc_ids:
            return
        if not self.cue_file_orig:
            return
        disc_id = self.disc_ids[0]
        game = popfe.get_game_from_gamelist(disc_id)
        print('Fetching SND0')
        snd0 = None
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
            self.icon0 = popfe.get_icon0_from_game(disc_id, game, self.cue_file_orig, 'pop-fe-ps3-work/ICON0.PNG')
        if self.icon0:
            temp_files.append('pop-fe-ps3-work/ICON0.PNG')
            self.icon0.resize((80,80), Image.BILINEAR).save('pop-fe-ps3-work/ICON0.PNG')
            self.icon0_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/ICON0.PNG')
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
        temp_files.append('pop-fe-ps3-work/PIC0.PNG')
        self.pic0.resize((128,80), Image.BILINEAR).save('pop-fe-ps3-work/PIC0.PNG')
        self.pic0_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/PIC0.PNG')
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
        temp_files.append('pop-fe-ps3-work/PIC1.PNG')
        self.pic1.resize((128,80), Image.BILINEAR).save('pop-fe-ps3-work/PIC1.PNG')
        self.pic1_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/PIC1.PNG')
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
        if cue_file[-4:] == '.bin' or cue_file[-4:] == '.img':
            tmpcue = 'pop-fe-ps3-work/TMPCUE' + disc + '.cue'
            tmpimg = 'pop-fe-ps3-work/TMPIMG' + disc + '.bin'
            print('Need to create a temporary cue/bin', tmpcue, tmpimg)
            temp_files.append(tmpcue)
            temp_files.append(tmpimg)
            popfe.copy_file(cue_file, tmpimg)

            with open(tmpcue, "w") as f:
                f.write('FILE "%s" BINARY\n' % ('TMPIMG' + disc + '.bin'))
                f.write('  TRACK 01 MODE2/2352\n')
                f.write('    INDEX 01 00:00:00\n')
            img_file = cue_file
            cue_file = tmpcue
        else:
            i = popfe.get_imgs_from_bin(cue_file)
            img_file = i[0]
            if len(i) > 1:
                print('Merging multi-bin disc') if verbose else None
                mb = 'MB' + disc
                if os.name == 'posix':
                    subprocess.call(['python3', './binmerge', '-o', 'pop-fe-ps3-work', cue_file, mb])
                else:
                    subprocess.call(['binmerge.exe', '-o', 'pop-fe-ps3-work', cue_file, mb])
                cue_file = 'pop-fe-ps3-work/' + mb + '.cue'
                temp_files.append(cue_file)
                img_file = 'pop-fe-ps3-work/' + mb + '.bin'
                temp_files.append(img_file)
            
        print('Generating cu2') if verbose else None
        cu2_file = cue_file[:-4] + '.cu2'
        try:
            os.stat(cu2_file).st_size
            print('Using existing CU2 file: %s' % cu2_file) if verbose else None
        except:
            cu2_file = 'pop-fe-ps3-work/CUE' + disc + '.cu2'
            print('Creating temporary CU2 file %s from %s' % (cu2_file, cue_file)) if verbose else None
            if os.name == 'posix':
                subprocess.call(['python3', './cue2cu2.py', '-n', cu2_file, '--size', str(os.stat(img_file).st_size), cue_file])
            else:
                subprocess.call(['cue2cu2.exe', '-n', cu2_file, '--size', str(os.stat(img_file).st_size), cue_file])
            temp_files.append(cu2_file)
        print('Scanning for Game ID') if verbose else None
        tmp = 'pop-fe-ps3-work/TMP'
        disc_id = get_disc_id(cue_file, tmp)
        temp_files.append(tmp + '01.iso')

        self.builder.get_variable('disci%s_variable' % (disc)).set(disc_id)

        self.img_files.append(img_file)
        self.disc_ids.append(disc_id)
        self.cue_files.append(cue_file)
        self.cu2_files.append(cu2_file)

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
            self.builder.get_object('square_icon0', self.master).config(state='normal')
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
        temp_files.append('pop-fe-ps3-work/ICON0.PNG')
        self.icon0.resize((80,80), Image.BILINEAR).save('pop-fe-ps3-work/ICON0.PNG')
        self.icon0_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/ICON0.PNG')
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
        temp_files.append('pop-fe-ps3-work/ICON0.PNG')
        self.icon0.resize((80,80), Image.BILINEAR).save('pop-fe-ps3-work/ICON0.PNG')
        self.icon0_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/ICON0.PNG')
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
        temp_files.append('pop-fe-ps3-work/PIC0.PNG')
        self.pic0.resize((128,80), Image.BILINEAR).save('pop-fe-ps3-work/PIC0.PNG')
        self.pic0_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/PIC0.PNG')
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
        temp_files.append('pop-fe-ps3-work/PIC0.PNG')
        self.pic0.resize((128,80), Image.BILINEAR).save('pop-fe-ps3-work/PIC0.PNG')
        self.pic0_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/PIC0.PNG')
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
        temp_files.append('pop-fe-ps3-work/PIC1.PNG')
        self.pic1.resize((128,80), Image.BILINEAR).save('pop-fe-ps3-work/PIC1.PNG')
        self.pic1_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/PIC1.PNG')
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
        temp_files.append('pop-fe-ps3-work/PIC1.PNG')
        self.pic1.resize((128,80), Image.BILINEAR).save('pop-fe-ps3-work/PIC1.PNG')
        self.pic1_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/PIC1.PNG')
        c = self.builder.get_object('pic1_canvas', self.master)
        c.create_image(0, 0, image=self.pic1_tk, anchor='nw')
        self.update_preview()

    def on_pic0_disabled(self):
        self.pic0_disabled = self.builder.get_variable('pic0_disabled_variable').get()
        self.update_preview()

    def on_icon0_square(self):
        self.icon0_square = self.builder.get_variable('icon0_square_variable').get()
        
    def on_square_icon0(self):
        self.square_icon0 = self.builder.get_variable('square_icon0_variable').get()
        
    def on_icon0_from_disc(self):
        self.icon0_disc = self.builder.get_variable('disc_as_icon0_variable').get()
        if not self.disc and self.disc_ids:
            disc_id = self.disc_ids[0]
            game = popfe.get_game_from_gamelist(disc_id)
            self.master.config(cursor='watch')
            self.master.update()
            d = popfe.get_icon0_from_disc(disc_id, game, self.cue_files[0], 'DISC.PNG')
            size = (176,176)
            d = d.resize(size, Image.BILINEAR)
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
            self.icon0.resize((80,80), Image.BILINEAR).save('pop-fe-ps3-work/ICON0.PNG')
        else:
            self.disc.resize((80,80), Image.BILINEAR).save('pop-fe-ps3-work/ICON0.PNG')
        self.icon0_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/ICON0.PNG')
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
            self.pic1.resize((128,80), Image.BILINEAR).save('pop-fe-ps3-work/PIC1.PNG')
        else:
            self.back.resize((128,80), Image.BILINEAR).save('pop-fe-ps3-work/PIC1.PNG')
        self.pic1_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/PIC1.PNG')
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
            print(idx)
            d = self.builder.get_variable('discid%d_variable' % (idx + 1)).get()
            print(idx, d)
            disc_ids.append(d)

        disc_id = disc_ids[0]
        title = self.builder.get_variable('title_variable').get()
        print('DISC', disc_id)
        print('TITLE', title)
        resolution = 1
        magic_word = []
        if disc_id in libcrypt:
            for idx in range(len(self.cue_files)):
                magic_word.append(libcrypt[self.disc_ids[idx]]['magic_word'])

        if disc_id[:4] == 'SLES' or disc_id[:4] == 'SCES':
            print('SLES/SCES PAL game. Default resolution set to 2 (640x512)') if verbose else None
            resolution = 2

        self.master.config(cursor='watch')
        self.master.update()
        aea_files = {}
        print('Scanning for audio tracks')
        for d in range(len(self.cue_files)):
            aea_files[d] = []
            bc = bchunk()
            bc.towav = True
            bc.open(self.cue_files[d])
            for i in range(1, len(bc.cue)):
                if not bc.cue[i]['audio']:
                    continue
                f = 'pop-fe-ps3-work/TRACK_%d_' % (d)
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
                        subprocess.run(['atracdenc/src/atracdenc.exe', '--encode=atrac3', '-i', wav_file, '-o', aea_file], check=True)
                except:
                    print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\natracdenc not found.\nCan not convert CDDA tracks.\nCreating EBOOT.PBP without support for CDDA audio.\nPlease see README file for how to install atracdenc\nXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                    break
                aea_files[d].append(aea_file)

        snd0 = self.builder.get_variable('snd0_variable').get()
        if snd0[:24] == 'https://www.youtube.com/':
            snd0 = popfe.get_snd0_from_link(snd0)
            if snd0:
                temp_files.append(snd0)
        popfe.create_ps3(pkg, disc_ids, title,
                         self.icon0 if self.icon0_disc=='off' else self.disc,
                         self.pic0 if self.pic0_disabled =='off' else None,
                         self.pic1 if self.pic1_bc=='off' else self.back,
                         self.cue_files, self.cu2_files,
                         self.img_files, [], aea_files, magic_word,
                         resolution, subdir='pop-fe-ps3-work/', snd0=snd0,
                         square_icon0=False if self.square_icon0=='off' else True)
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

    expire_after = datetime.timedelta(days=100)
    requests_cache.install_cache(str(pathlib.Path.home()) + '/.pop-fe', expire_after=expire_after)
    
    if args.v:
        verbose = True

    root = TkinterDnD.Tk()
    app = PopFePs3App(root)
    root.title('pop-fe PS3')
    root.mainloop()
    
