##!/usr/bin/env python3
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
#import redis
import paho.mqtt.client as mqtt
import redislite 

scriptDirectory = os.path.dirname(os.path.realpath(__file__))
os.chdir(scriptDirectory)
sys.path.insert(0,scriptDirectory + '/include')

import alarm_settings
import common

rdb = redislite.StrictRedis(alarm_settings.Redis_Db_Path)
rdb.client_setname("alarm_db_debugger")

print ("Permetre d'attacher la socket en cli : \n"+ rdb.socket_file)

test = input("enter to quit")
