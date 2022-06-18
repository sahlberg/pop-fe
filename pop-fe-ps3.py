#!/usr/bin/python3
#!/usr/bin/env python

import argparse
import os
import pathlib
import pygubu
import subprocess
import tkinter as tk
import tkinter.ttk as ttk

from PIL import Image
from bchunk import bchunk
import importlib  
from gamedb import games, libcrypt
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
        self.pkgdir = None
        
        self.master = master
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        self.mainwindow = builder.get_object("top_frame", master)

        callbacks = {
            'on_icon0_clicked': self.on_icon0_clicked,
            'on_pic0_clicked': self.on_pic0_clicked,
            'on_pic1_clicked': self.on_pic1_clicked,
            'on_path_changed': self.on_path_changed,
            'on_dir_changed': self.on_dir_changed,
            'on_create_pkg': self.on_create_pkg,
            'on_reset': self.on_reset,
        }

        builder.connect_callbacks(callbacks)
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
        self.pkgdir = None
        for idx in range(1,5):
            self.builder.get_object('disc' + str(idx), self.master).config(filetypes=[('Image files', ['.cue', '.bin', '.img']), ('All Files', ['*.*', '*'])])
            self.builder.get_variable('disc%d_variable' % (idx)).set('')
            self.builder.get_variable('d%d_label' % (idx)).set('')
            self.builder.get_object('disc' + str(idx), self.master).config(state='disabled')
        self.builder.get_object('disc1', self.master).config(state='normal')
        self.builder.get_object('create_button', self.master).config(state='disabled')
        self.builder.get_variable('gameid_variable').set('')
        self.builder.get_variable('title_variable').set('')
        self.builder.get_object('snd0', self.master).config(filetypes=[('Audio files', ['.wav']), ('All Files', ['*.*', '*'])])

        
    def on_path_changed(self, event):
        cue_file = event.widget.cget('path')
        img_file = None
        if not len(cue_file):
            return

        self.master.config(cursor='watch')
        self.master.update()
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
        print('ID', disc_id)
        temp_files.append(tmp + '01.iso')

        self.builder.get_variable(disc + '_label').set(disc_id)

        self.img_files.append(img_file)
        self.disc_ids.append(disc_id)
        self.cue_files.append(cue_file)
        self.cu2_files.append(cu2_file)

        if disc == 'd1':
            self.builder.get_variable('gameid_variable').set(disc_id)
            self.builder.get_variable('title_variable').set(popfe.get_title_from_game(disc_id))
            game = popfe.get_game_from_gamelist(disc_id)
            print('Fetching SND0')
            snd0 = popfe.get_snd0_from_game(disc_id, subdir='pop-fe-ps3-work/')
            if snd0:
                print('Found SND0', snd0)
                temp_files.append(snd0)
                self.builder.get_variable('snd0_variable').set(snd0)
            
            print('Fetching ICON0') if verbose else None
            self.icon0 = popfe.get_icon0_from_game(disc_id, game, cue_file, 'pop-fe-ps3-work/ICON0.PNG')
            temp_files.append('pop-fe-ps3-work/ICON0.PNG')
            self.icon0.resize((80,80), Image.BILINEAR).save('pop-fe-ps3-work/ICON0.PNG')
            self.icon0_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/ICON0.PNG')
            c = self.builder.get_object('icon0_canvas', self.master)
            c.create_image(0, 0, image=self.icon0_tk, anchor='nw')
            
            print('Fetching PIC0') if verbose else None
            self.pic0 = popfe.get_pic0_from_game(disc_id, game, cue_file, 'PIC0.PNG')
            temp_files.append('pop-fe-ps3-work/PIC0.PNG')
            self.pic0.resize((128,80), Image.BILINEAR).save('pop-fe-ps3-work/PIC0.PNG')
            self.pic0_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/PIC0.PNG')
            c = self.builder.get_object('pic0_canvas', self.master)
            c.create_image(0, 0, image=self.pic0_tk, anchor='nw')
            
            print('Fetching PIC1') if verbose else None
            self.pic1 = popfe.get_pic1_from_game(disc_id, game, cue_file, 'PIC1.PNG')
            temp_files.append('pop-fe-ps3-work/PIC1.PNG')
            self.pic1.resize((128,80), Image.BILINEAR).save('pop-fe-ps3-work/PIC1.PNG')
            self.pic1_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/PIC1.PNG')
            c = self.builder.get_object('pic1_canvas', self.master)
            c.create_image(0, 0, image=self.pic1_tk, anchor='nw')
            self.builder.get_object('disc1', self.master).config(state='disabled')
            self.builder.get_object('disc2', self.master).config(state='normal')
            self.builder.get_object('create_button', self.master).config(state='normal')
        elif disc == 'd2':
            self.builder.get_object('disc2', self.master).config(state='disabled')
            self.builder.get_object('disc3', self.master).config(state='normal')
        elif disc == 'd3':
            self.builder.get_object('disc3', self.master).config(state='disabled')
            self.builder.get_object('disc4', self.master).config(state='normal')
        elif disc == 'd4':
            self.builder.get_object('disc4', self.master).config(state='disabled')
            self.builder.get_object('disc5', self.master).config(state='normal')
        elif disc == 'd5':
            self.builder.get_object('disc5', self.master).config(state='disabled')
        print('Finished processing disc') if verbose else None
        self.master.config(cursor='')


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
        temp_files.append('pop-fe-ps3-work/ICON0.PNG')
        self.icon0.resize((80,80), Image.BILINEAR).save('pop-fe-ps3-work/ICON0.PNG')
        self.icon0_tk = tk.PhotoImage(file = 'pop-fe-ps3-work/ICON0.PNG')
        c = self.builder.get_object('icon0_canvas', self.master)
        c.create_image(0, 0, image=self.icon0_tk, anchor='nw')


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

    def on_dir_changed(self, event):
        self.pkgdir = event.widget.cget('path')
        # PKG in print()

    def on_create_pkg(self):        
        pkg = self.builder.get_variable('pkgfile_variable').get()
        pkgdir = self.builder.get_variable('pkgdir_variable').get()
        if len(pkg) == 0:
            pkg = 'game.pkg'
        if len(pkgdir):
            pkg = pkgdir + '/' + pkg
        print('Creating ' + pkg)
        disc_id = self.builder.get_variable('gameid_variable').get()
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
        popfe.create_ps3(pkg, disc_id, title, self.icon0, self.pic0, self.pic1, self.cue_files, self.cu2_files, self.img_files, [], aea_files, magic_word, resolution, subdir='pop-fe-ps3-work/', snd0=snd0)
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

    root = tk.Tk()
    app = PopFePs3App(root)
    root.title('pop-fe PS3')
    root.mainloop()
    
