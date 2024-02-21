#!/usr/bin/python3
#!/usr/bin/env python

import argparse
import os
import pathlib
import pygubu
import re
import shutil
import struct
import subprocess
import tkinter as tk
import tkinter.ttk as ttk
import zipfile

have_pytube = False
try:
    import pytube
    have_pytube = True
except:
    True

from PIL import Image
from bchunk import bchunk
import importlib  
from gamedb import games, libcrypt, themes
popfe = importlib.import_module("pop-fe")
from cue import parse_ccd, ccd2cue, write_cue

verbose = False
temp_files = []

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "pop-fe-psp.ui"

EMPTY_CONFIG = bytes([
    0x70,0x00,0x07,0x06,0x00,0x00,0x06,0x06,0x00,0x00,0x00,0x00,0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0x00,0x00,0x00,0x00,
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0x00,0x00,
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xFF,0xFF,0xFF,0xFF,0x00,0x00,0x00,0x00,
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0x00,0x00,0x00,0x00,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0x00,0x00,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0x00,0x00,0x00,0x00,
    0x00,0x00,0x00,0x00,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,0xFF,
    0xFF,0xFF,0xFF,0xFF,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0xFF,0xFF,0xFF,0xFF
])

def get_disc_id(cue, tmp):
    print('Convert ' + cue + ' to a normal style ISO') if verbose else None
    bc = bchunk()
    bc.verbose = False
    bc.open(cue)
    bc.writetrack(1, tmp)

    gid = popfe.get_gameid_from_iso(tmp)
    return gid


class FinishedDialog(tk.Toplevel):
    def __init__(self, root):
        tk.Toplevel.__init__(self, root)
        label = tk.Label(self, text="Finished creating EBOOT")
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
        self.real_disc_ids = None
        self.icon0 = None
        self.icon0_tk = None
        self.pic0 = None
        self.pic0_tk = None
        self.pic1 = None
        self.pic1_tk = None
        self.pkgdir = None
        self.watermark = 'on'
        self.cdda = 'off'
        self.pic0_disabled = 'off'
        self.pic1_disabled = 'off'
        self.snd0_disabled = 'off'
        self.configs = []
        self.subdir='pop-fe-psp-work/'
        
        self.master = master
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object("top_frame", master)

        callbacks = {
            'on_icon0_clicked': self.on_icon0_clicked,
            'on_pic0_clicked': self.on_pic0_clicked,
            'on_pic0_disabled': self.on_pic0_disabled,
            'on_pic1_disabled': self.on_pic1_disabled,
            'on_snd0_disabled': self.on_snd0_disabled,
            'on_pic1_clicked': self.on_pic1_clicked,
            'on_path_changed': self.on_path_changed,
            'on_dir_changed': self.on_dir_changed,
            'on_watermark': self.on_watermark,
            'on_youtube_audio': self.on_youtube_audio,
            'on_create_eboot': self.on_create_eboot,
            'on_reset': self.on_reset,
            'on_cdda': self.on_cdda,
            'on_theme_selected': self.on_theme_selected,
            'on_force_ntsc': self.on_force_ntsc,
        }

        builder.connect_callbacks(callbacks)
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
        self.real_disc_ids = []
        self.icon0 = None
        self.icon0_tk = None
        self.pic0 = None
        self.pic0_tk = None
        self.pic1 = None
        self.pic1_tk = None
        self.preview_tk = None
        self.configs = []
        self.builder.get_variable('watermark_variable').set(self.watermark)
        self.builder.get_variable('cdda_variable').set(self.cdda)
        for idx in range(1,6):
            self.builder.get_object('discid%d' % (idx), self.master).config(state='disabled')
        for idx in range(1,5):
            self.builder.get_object('disc' + str(idx), self.master).config(filetypes=[('Image files', ['.cue', '.bin', '.ccd', '.img', '.zip', '.chd']), ('All Files', ['*.*', '*'])])
            self.builder.get_variable('disc%d_variable' % (idx)).set('')
            self.builder.get_variable('discid%d_variable' % (idx)).set('')
            self.builder.get_object('disc' + str(idx), self.master).config(state='disabled')
        self.builder.get_object('disc1', self.master).config(state='normal')
        self.builder.get_object('create_button', self.master).config(state='disabled')
        self.builder.get_object('youtube_button', self.master).config(state='disabled')
        self.builder.get_variable('title_variable').set('')
        self.builder.get_variable('snd0_variable').set('')
        self.builder.get_object('snd0', self.master).config(filetypes=[('Audio files', ['.wav']), ('All Files', ['*.*', '*'])])

        self.builder.get_object('manual', self.master).config(filetypes=[('All Files', ['*.*', '*'])])
        self.builder.get_variable('manual_variable').set('')
        
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
            print('Fetching SND0') if verbose else None
            if self._theme != '':
                snd0 = popfe.get_snd0_from_theme(self._theme, disc_id, 'pop-fe-psp-work')
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
            self.icon0 = popfe.get_image_from_theme(self._theme, disc_id, 'pop-fe-psp-work', 'ICON0.PNG')
            if not self.icon0:
                self.icon0 = popfe.get_image_from_theme(self._theme, disc_id, 'pop-fe-psp-work', 'ICON0.png')
            if self.icon0:
                self.icon0 = self.icon0.crop(self.icon0.getbbox())
        if not self.icon0:
            self.icon0 = popfe.get_icon0_from_game(disc_id, game, self.cue_file_orig, self.subdir + 'ICON0.PNG', psn_frame_size=((80,80),(62,62)))
            
        if self.icon0:
            temp_files.append(self.subdir + 'ICON0.PNG')
            self.icon0.resize((80,80), Image.Resampling.HAMMING).save(self.subdir + 'ICON0.PNG')
            self.icon0_tk = tk.PhotoImage(file = self.subdir + 'ICON0.PNG')
            c = self.builder.get_object('icon0_canvas', self.master)
            c.create_image(0, 0, image=self.icon0_tk, anchor='nw')
            
        print('Fetching PIC0') if verbose else None
        self.pic0 = None
        if self._theme != '':
            self.pic0 = popfe.get_image_from_theme(self._theme, disc_id, 'pop-fe-psp-work', 'PIC0.PNG')
            if not self.pic0:
                self.pic0 = popfe.get_image_from_theme(self._theme, disc_id, 'pop-fe-psp-work', 'PIC0.png')
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
            self.pic1 = popfe.get_image_from_theme(self._theme, disc_id, 'pop-fe-psp-work', 'PIC1.PNG')
            if not self.pic1:
                self.pic1 = popfe.get_image_from_theme(self._theme, disc_id, 'pop-fe-psp-work', 'PIC1.png')
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
        if cue_file[-4:] == '.chd':
            print('This is a CHD file. Uncompress the file.') if verbose else None
            chd = cue_file
            try:
                tmpcue = self.subdir + 'CDH%s.cue' % disc
                tmpbin = self.subdir + 'CDH%s.bin' % disc
                temp_files.append(tmpcue)
                temp_files.append(tmpbin)
                print('Extracting', tmpcue, 'and', tmpbin, 'chd')  if verbose else None
                subprocess.run(['chdman', 'extractcd', '-f', '-i', chd, '-ob', tmpbin, '-o', tmpcue], check=True)
            except:
                print('XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX\nCHDMAN not found.\nCan not convert game\nPlease see README file for how to install chdman\nXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX')
                os._exit(10)
            cue_file = tmpcue
            self.cue_file_orig = cue_file
        if cue_file[-4:] == '.zip':
            print('This is a ZIP file. Uncompress the file.') if verbose else None
            zip = cue_file
            with zipfile.ZipFile(zip, 'r') as zf:
                for f in zf.namelist():
                    print('Extracting', self.subdir + f) if verbose else None
                    temp_files.append(self.subdir + f)
                    zf.extract(f, path=self.subdir)
                    if re.search('.cue$', f):
                        print('Found CUE file', f) if verbose else None
                        cue_file = self.subdir + f
                        self.cue_file_orig = cue_file
        if cue_file[-4:] == '.ccd':
            tmpcue = self.subdir + 'TMPCUE' + disc + '.cue'
            temp_files.append(tmpcue)
            ccd = parse_ccd(cue_file)
            cue = ccd2cue(ccd)
            write_cue(cue, tmpcue)
            cue_file = tmpcue
        if cue_file[-4:] == '.bin' or cue_file[-4:] == '.img':
            tmpcue = self.subdir + 'TMPCUE' + disc + '.cue'
            tmpimg = self.subdir + 'TMPIMG' + disc + '.bin'
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
                    subprocess.call(['python3', './binmerge', '-o', self.subdir, cue_file, mb])
                else:
                    subprocess.call(['binmerge.exe', '-o', self.subdir, cue_file, mb])
                cue_file = self.subdir + mb + '.cue'
                temp_files.append(cue_file)
                img_file = self.subdir + mb + '.bin'
                temp_files.append(img_file)
            
        print('Scanning for Game ID') if verbose else None
        tmp = self.subdir + 'TMP01.iso'
        disc_id = get_disc_id(cue_file, tmp)
        print('ID', disc_id)
        temp_files.append(tmp)

        self.builder.get_variable('disci%s_variable' % (disc)).set(disc_id)

        self.img_files.append(img_file)
        self.disc_ids.append(disc_id)
        self.real_disc_ids.append(disc_id)
        self.cue_files.append(cue_file)
        self.configs.append(None)

        if disc_id in games and 'psp-use-cdda' in games[disc_id]:
            self.cdda = 'on'
            self.builder.get_variable('cdda_variable').set(self.cdda)
        
        if disc_id in games and 'pspconfig' in games[disc_id]:
            print('Found an external config for', disc_id)
            with open(games[disc_id]['pspconfig'], 'rb') as f:
                      self.configs[-1] = f.read()
        try:
            os.stat(cue_file[:-3]+'pspconfig').st_size
            print('Found an external config ', cue_file[:-3]+'pspconfig')
            with open(cue_file[:-3]+'pspconfig', 'rb') as f:
                      self.configs[-1] = f.read()
        except:
            True
        if disc == 'd1':
            self.builder.get_object('discid1', self.master).config(state='normal')
            self.builder.get_variable('title_variable').set(popfe.get_title_from_game(disc_id))
            self.update_assets()
            
            self.builder.get_object('disc1', self.master).config(state='disabled')
            self.builder.get_object('disc2', self.master).config(state='normal')
            self.builder.get_object('youtube_button', self.master).config(state='normal')
            self.builder.get_object('create_button', self.master).config(state='normal')
            self.update_preview()
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

        if self.pic0_disabled == 'on':
            _pic0 = None
        else:
            _pic0 = self.pic0
        if self.pic1_disabled == 'on':
            _pic1 = Image.new(self.pic0.mode, (1920, 1080), (0,0,0)).convert('RGBA')
            _pic1.putalpha(0)
        else:
            _pic1 = self.pic1

        if _pic0 and self.pic0.mode == 'P':
            _pic0 = _pic0.convert(mode='RGBA')
        c = self.builder.get_object('preview_canvas', self.master)
        p1 = _pic1.resize((382,216), Image.Resampling.HAMMING)
        if _pic0: 
            p0 = _pic0.resize((int(p1.size[0] * 0.55) , int(p1.size[1] * 0.58)), Image.Resampling.HAMMING)
            if has_transparency(p0):
                Image.Image.paste(p1, p0, box=(148,79), mask=p0)
            else:
                Image.Image.paste(p1, p0, box=(148,79))
        if self.icon0:
            i0 = self.icon0.resize((int(p1.size[1] * 0.25) , int(p1.size[1] * 0.25)), Image.Resampling.HAMMING)
            if has_transparency(i0):
                Image.Image.paste(p1, i0, box=(36,81), mask=i0)
            else:
                Image.Image.paste(p1, i0, box=(36,81))
        temp_files.append(self.subdir + 'PREVIEW.PNG')
        p1.save(self.subdir + 'PREVIEW.PNG')
        self.preview_tk = tk.PhotoImage(file = self.subdir + 'PREVIEW.PNG')
        c = self.builder.get_object('preview_canvas', self.master)
        c.create_image(0, 0, image=self.preview_tk, anchor='nw')
        

    def on_watermark(self):
        self.watermark = self.builder.get_variable('watermark_variable').get()
        
    def on_icon0_clicked(self, event):
        filetypes = [
            ('Image files', ['.png', '.PNG', '.jpg', '.JPG']),
            ('All Files', ['*.*', '*'])]
        path = tk.filedialog.askopenfilename(title='Select image for ICON0',filetypes=filetypes)
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


    def on_pic0_disabled(self):
        self.pic0_disabled = self.builder.get_variable('pic0_disabled_variable').get()
        self.update_preview()

    def on_pic1_disabled(self):
        self.pic1_disabled = self.builder.get_variable('pic1_disabled_variable').get()
        self.update_preview()

    def on_snd0_disabled(self):
        self.snd0_disabled = self.builder.get_variable('snd0_disabled_variable').get()

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
        self.pic1.resize((128,80), Image.Resampling.HAMMING).save(self.subdir + 'PIC0.PNG')
        self.pic0_tk = tk.PhotoImage(file = self.subdir + 'PIC0.PNG')
        c = self.builder.get_object('pic0_canvas', self.master)
        c.create_image(0, 0, image=self.pic0_tk, anchor='nw')
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

    def on_dir_changed(self, event):
        self.pkgdir = event.widget.cget('path')

    def on_youtube_audio(self):
        if not have_pytube:
            return
        self.master.config(cursor='watch')
        a = pytube.contrib.search.Search(self.builder.get_variable('title_variable').get() + ' ps1 ost')
        if a:
            self.builder.get_variable('snd0_variable').set('https://www.youtube.com/watch?v=' + a.results[0].video_id)
           
        self.master.config(cursor='')

    def on_create_eboot(self):        
        pkgdir = self.builder.get_variable('pkgdir_variable').get()
        disc_id = self.real_disc_ids[0]
        title = self.builder.get_variable('title_variable').get()
        print('Creating EBOOT')
        print('DISC', disc_id)
        print('TITLE', title)
        disc_ids = []
        for idx in range(len(self.cue_files)):
            d = self.builder.get_variable('discid%d_variable' % (idx + 1)).get()
            disc_ids.append(d)
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

        if disc_id[:4] == 'SLES' or disc_id[:4] == 'SCES':
            print('SLES/SCES PAL game. Default resolution set to 2 (640x512)') if verbose else None
            resolution = 2

        self.master.config(cursor='watch')
        self.master.update()

        snd0 = self.builder.get_variable('snd0_variable').get()
        if snd0[:24] == 'https://www.youtube.com/':
            snd0 = popfe.get_snd0_from_link(snd0, subdir=self.subdir)
            if snd0:
                temp_files.append(snd0)

        manual = self.builder.get_variable('manual_variable').get()
        if manual and len(manual):
            manual = popfe.create_manual(manual, self.disc_ids[0], subdir=self.subdir)
        else:
            manual = None

        ebootdir = self.pkgdir if self.pkgdir else '.'

        #
        # Apply all PPF fixes we might need
        #
        self.cue_files, self.img_files = popfe.apply_ppf_fixes(self.real_disc_ids, self.cue_files, self.img_files, self.subdir, tag="psp")

        self.cu2_files = popfe.generate_cu2_files(self.cue_files, self.img_files, self.subdir)

        aea_files = popfe.generate_aea_files(self.cue_files, self.img_files, self.subdir)

        if self.builder.get_variable('force_ntsc_variable').get() == 'on':
            for i in range(len(self.configs)):
                if not self.configs[i]:
                    # skip the revision header
                    self.configs[i] = EMPTY_CONFIG[:]
                self.configs[i] = bytearray(self.configs[i])
                # Set NTSC bit in configs
                self.configs[i][0x0b] |= 0x10
                self.configs[i][0x8f] |= 0x10
                
        popfe.create_psp(ebootdir, disc_ids, title,
                         self.icon0,
                         self.pic0 if self.pic0_disabled =='off' else None,
                         self.pic1 if self.pic1_disabled =='off' else None,
                         self.cue_files, self.cu2_files, self.img_files, [],
                         aea_files, subdir=self.subdir, snd0=snd0,
                         watermark=True if self.watermark=='on' else False,
                         subchannels=subchannels, manual=manual,
                         configs=self.configs,
                         use_cdda=True if self.cdda=='on' else False)
        self.master.config(cursor='')

        d = FinishedDialog(self.master)
        self.master.wait_window(d)
        self.init_data()

    def on_reset(self):
        self.init_data()

    def on_cdda(self):
        self.cdda = self.builder.get_variable('cdda_variable').get()

    def on_force_ntsc(self):
        True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', action='store_true', help='Verbose')
    args = parser.parse_args()

    if args.v:
        verbose = True

    root = tk.Tk()
    app = PopFePs3App(root)
    root.title('pop-fe PSP')
    root.mainloop()
    
