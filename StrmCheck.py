#!/usr/bin/env python
# -*- coding: utf-8 -*-

import fnmatch,os
import json

from subprocess import PIPE
from subprocess import Popen
from subprocess import TimeoutExpired

import logging                                                                                                                                                                          
import time
from colorama import Fore

from pathlib import Path

directory = r'/Users/fofanov.dmitry/Project/Emby/@@@'
AceServer = r'10.0.10.6'
AceUrlSrv = r'http://127.0.0.1:6878/ace/getstream?infohash='
TorrUrlSrv = r'http://ace.srv:8090/torrent/play?link='

PROBE_COMMAND = (
    'ffprobe -hide_banner -show_streams -select_streams v '
    '-of json=c=1 -v quiet'
)

ok_msg = Fore.GREEN + "OK!  " + Fore.RESET                                                                                                                                              
fail_msg = Fore.RED + "FAIL " + Fore.RESET   

logging.basicConfig(                                                                                                                                                                    
    level=logging.WARNING,                                                                                                                                                              
    format='[%(asctime)s] %(levelname)s: %(message)s',                                                                                                                                  
    datefmt='%Y-%m-%d %I:%M:%S')                                                                                                                                                        
log = logging.getLogger('ParseRuTor')                                                                                                                                                   
log.setLevel(logging.DEBUG)  

# Getting the frame width of a video picture
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

# We get by frame size, video quality
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

# Checking the folder if there is a file with the specified extension, 
# if not, then delete the folder
def CheckDir(root,files,ext):
    contains_other_ext = 0
    for file in files:
        if file.endswith(ext):  
            contains_other_ext = True
    if contains_other_ext == 0:
        deleteDir(root)    

# Main process
def main():
    os.chdir(directory)
    i = 0
    del_filenames = []
    # We get the number of files in the directory
    count = len([files for _, _, files in os.walk(directory) for file in files if file.endswith('.strm')])
    for root, dirs, files in os.walk(".", topdown=False):
        del_filenames.clear()
        for name in filter(lambda x: x.endswith('.strm'), files):
            filename = os.path.join(directory, root.replace('./',''), name)
            i = i + 1
            url = ''
            with open(filename) as file:
                lines = file.readlines()
                for line in lines:
                    line = line.strip()
                    if (AceServer in line) or (AceUrlSrv in line):
                        url = line.replace(AceServer,'ace.srv').replace(AceUrlSrv,TorrUrlSrv)
                        probe_url = url
            if len(url) > 0:
                with open(filename, 'w') as file:
                    file.writelines(url)
            else: probe_url = line            
            width = None
            t1 = time.time()  
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
                log_msg = str("Rec: %-4s of %-4s, FileName: %-60s \t\t" % (int(i), int(count)-1, os.path.basename(filename)))
                log_msg += "%s (%s)" % (fail_msg, 'DELETE FILE')
                print(log_msg)
            else:
                try:
                    upd_filename = os.path.splitext(filename)[0].replace('-CamRip','-'+get_category(width)).replace('-SD','-'+get_category(width)).replace('-HD','-'+get_category(width)).replace('-FULL HD','-'+get_category(width)).replace('-4K UHD','-'+get_category(width)) + os.path.splitext(filename)[1]
                    if not ('(nnm)' in upd_filename):
                        upd_filename = os.path.splitext(upd_filename)[0] + ' (nnm)' + os.path.splitext(upd_filename)[1]
                    os.rename(filename, upd_filename)
                    log_msg = str("Rec: %-4s of %-4s, FileName: %-60s \t\t" % (int(i), int(count)-1, os.path.basename(upd_filename)))
                    t2 = time.time() 
                    log_msg += ok_msg + "Response time: %d" % ( int((t2-t1)*1000)) 
                    print(log_msg)
                except Exception as e:
                    log_msg = str("Rec: %-4s of %-4s, FileName: %-60s \t\t" % (int(i), int(count)-1, os.path.basename(filename)))
                    log_msg += "%s (%s)" % (fail_msg, str(e))
                    print(log_msg)
                    pass                
            if os.path.isfile(os.path.splitext(filename)[0].split('-')[0] + '.nfo'):
                os.remove(os.path.splitext(filename)[0].split('-')[0] + '.nfo')
        if (dirs == [] and len(del_filenames) != 0):
            for del_filename in del_filenames:
                files.remove(del_filename)
            CheckDir(root,files,('.strm'))
            log_msg = str("DELETE PATH: %s" % (root))
            print(log_msg)
    if root != "." and os.listdir(root) == []:
        deleteDir(root)
        log_msg = str("DELETE PATH: %s" % (root))
        print(log_msg)

if __name__ == '__main__':
    main()
