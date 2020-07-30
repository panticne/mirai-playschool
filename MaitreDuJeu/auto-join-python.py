#!/usr/bin/env python3
""" This file is used to connect automatically the card to the server game,"""
# Source : https://stackoverflow.com/questions/44112399/automatically-restart-a-python-program-if-its-killed/44112591
__author__ = "Nemanja Pantic"
__copyright__ = "Copyright 2020, HEIG-VD"
__license__ = "GPL"
__version__ = "0.1"
__email__ = "nemanja.pantic@heig-vd.ch"
__status__ = "Prototype"
import subprocess
import time

filename = 'client.py'
while True:
    p = subprocess.Popen('python3 '+filename, shell=True).wait()
    time.sleep(3)
    if p != 0:
        continue
    else:
        break
