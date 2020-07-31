#!/usr/bin/env python3
__author__ = "Nemanja Pantic"
__copyright__ = "Copyright 2020, HEIG-VD"
__license__ = "GPL"
__version__ = "1.0"
__email__ = "nemanja.pantic@heig-vd.ch"
import subprocess
import time

filename = 'client.py'
while True:
    """However, you should be careful with the '.wait()'"""
    p = subprocess.Popen('python3 '+filename, shell=True).wait()

    """#if your there is an error from running 'my_python_code_A.py',
    the while loop will be repeated,
    otherwise the program will break from the loop"""
    time.sleep(3)
    if p != 0:
        continue
    else:
        break
