#!/usr/bin/env python3
#dossier virtuel

#frontend 

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
import paho.mqtt.client as mqtt
#import redis
import redislite
import getopt

scriptDirectory = os.path.dirname(os.path.realpath(__file__))
os.chdir(scriptDirectory)
sys.path.insert(0,scriptDirectory + '/../include')

import alarm_settings
import common

def main(argv):
    common.LogDump( zLogger,"Device status is starting.",True,False,False )

    if common.checkPythonInterpreter(zLogger) == False:
        common.LogDump( zLogger,"Let's stop now !")
        sys.exit(1)

    opt_debug = False

    try:
        opts, args = getopt.getopt(argv,"d",["debug"])
    except getopt.GetoptError:
        common.LogDump( zLogger, (__file__ + ' [-d/--debug]'), True, False,False )
        sys.exit(2)

    for opt,arg in opts:
        if opt in ("-d", "--debug"):
            opt_debug = True

    common.OpenDatabase(zLogger,True, False,False)
    common.rdb.client_setname("alarm_device_status")

    if opt_debug == True:
        common.LogDump( zLogger, "Debug is activated",True, False,False )


    #maj des champs isalive par rapport au timestamp
    common.UpdateSensorsActivity(zLogger,alarm_settings.SensorTimeOut)

    device_list = common.GetSensorsStatus(zLogger,True,True,False,False)
    #print (device_list)

    print ("[actifs]:")
    for item in device_list:
        if device_list[item]['isalive'] == 'true':
            print ( item, str(device_list[item]) )

    print ("[inactifs]:")
    for item in device_list:
        if device_list[item]['isalive'] != 'true':
            print ( item, str(device_list[item]) )

    common.CloseDatabase(zLogger, True, False, False)

    sys.exit(0)


######## main ########

if __name__ == "__main__": 
    file_name = os.path.basename(sys.argv[0])
    zLogger = common.StartLogging( alarm_settings.LogFolder,file_name )
    common.LogDump( zLogger,file_name, True,False,False )
    main(sys.argv[1:])
