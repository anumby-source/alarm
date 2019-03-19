#!/usr/bin/env python3
#dossier virtuel

import json
import time,datetime
import multiprocessing, subprocess, os
import fcntl
import signal
import sys
import logging
import logging.handlers
import math
import os,sys
import redis
import paho.mqtt.client as mqtt

scriptDirectory = os.path.dirname(os.path.realpath(__file__))
os.chdir(scriptDirectory)
sys.path.insert(0,scriptDirectory + '/../include')

import alarm_settings
import common

#if common.checkPythonInterpreter(zLogger) == False:
#    common.LogDump( zLogger,"Let's stop now !")
#    sys.exit(1)

srcFile = alarm_settings.InputStatusJsonTpl 
dstFile = alarm_settings.OutputStatusJson

print ("Input: " + srcFile)
print ("Output: " + dstFile)

with open(srcFile) as f:
    lines = f.readlines()

f = open(dstFile,"w")
for line in lines:
    if '#' not in line:
        f.write(line)
f.close()
