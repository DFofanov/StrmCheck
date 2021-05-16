#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path

from subprocess import PIPE
from subprocess import Popen
from subprocess import TimeoutExpired

directory = r'/Users/fofanov.dmitry/Project/Emby/111'

PROBE_COMMAND = (
    'ffprobe -hide_banner -show_streams -select_streams v '
    '-of json=c=1 -v quiet'
)

def probe(url, timeout=None):
    """Invoke probe to get stream information."""
    outs = None
    proc = Popen(f'{PROBE_COMMAND} {url}'.split(), stdout=PIPE, stderr=PIPE)
    try:
        outs, dummy = proc.communicate(timeout=timeout)
    except TimeoutExpired:
        proc.kill()
    if outs:
        try:
            return json.loads(outs.decode('utf-8'))
        except json.JSONDecodeError as exc:
            print(exc)
    return None

def get_category(width):
    category = None
    if (width <= 256): category = '144p'
    elif (width in range(426, 640)): category = '240p'
    elif (width in range(640, 854)): category = '360p'
    elif (width in range(854, 1280)): category = '480p'
    elif (width in range(1280, 1920)): category = '720p'
    elif (width in range(1920, 2560)): category = '1080p'
    elif (width in range(2560, 3840)): category = '1440p'
    elif (width >= 3840): category = '2160p'
    return category

def deleteDir(dirPath):
    deleteFiles = []
    deleteDirs = []
    for root, dirs, files in os.walk(dirPath):
        for f in files:
            deleteFiles.append(os.path.join(root, f))
        for d in dirs:
            deleteDirs.append(os.path.join(root, d))
    for f in deleteFiles:
        os.remove(f)
    for d in deleteDirs:
        os.rmdir(d)
    os.rmdir(dirPath)

def CheckDir(root,files,ext):
    contains_other_ext = 0
    for file in files:
        if file.endswith(ext):  
            contains_other_ext = True
    if contains_other_ext == 0:
        deleteDir(root)    

def main():
    os.chdir(directory)
    del_filenames = []
    for root, dirs, files in os.walk(".", topdown=False):
        del_filenames.clear()
        for name in filter(lambda x: x.endswith('.strm'), files):
            filename = os.path.join(directory, root.replace('./',''), name)
            url = ''
            with open(filename) as file:
                lines = file.readlines()
                for line in lines:
                    line = line.strip()
                    if ('10.0.10.6' in line) or (':6878/ace/getstream?infohash=' in line):
                        url = line.replace('10.0.10.6','ace.srv').replace('http://127.0.0.1:6878/ace/getstream?infohash=','http://ace.srv:8090/torrent/play?link=')
                        probe_url = url
            if len(url) > 0:
                with open(filename, 'w') as file:
                    file.writelines(url)
            else: probe_url = line            
            width = None
            obj_probe = probe(probe_url,30)
            if obj_probe != None and len(obj_probe) > 0:
                if len(obj_probe["streams"]) > 0:
                    width = obj_probe["streams"][0]["width"]
            if width == None:               
                if os.path.isfile(filename):
                    os.remove(filename)
                del_filenames.append(os.path.basename(filename))
                if os.path.isfile(os.path.splitext(filename)[0]+'.nfo'):
                    os.remove(os.path.splitext(filename)[0]+'.nfo')
                print('DELETE - ' + filename)
            else:
                try:
                    upd_filename = os.path.splitext(filename)[0].replace('-CamRip','-'+get_category(width)).replace('-SD','-'+get_category(width)).replace('-HD','-'+get_category(width)).replace('-FULL HD','-'+get_category(width)).replace('-4K UHD','-'+get_category(width)) + os.path.splitext(filename)[1]
                    if not ('(nnm)' in upd_filename):
                        upd_filename = os.path.splitext(upd_filename)[0] + ' (nnm)' + os.path.splitext(upd_filename)[1]
                    os.rename(filename, upd_filename)
                    print('OK - ' + upd_filename)
                except:
                    pass
                    print('ERROR - ' + filename)
            if os.path.isfile(os.path.splitext(filename)[0].split('-')[0] + '.nfo'):
                os.remove(os.path.splitext(filename)[0].split('-')[0] + '.nfo')
        if dirs == []:
            for del_filename in del_filenames:
                files.remove(del_filename)
            CheckDir(root,files,('.strm'))
    if root != "." and os.listdir(root) == []:
        deleteDir(root)

if __name__ == '__main__':
    main()
