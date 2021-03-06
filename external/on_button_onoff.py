#!/usr/bin/env python3
# #dossier virtuel

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
sys.path.insert(0, scriptDirectory + '/../include')

import alarm_settings
import common

def main(argv):
    common.LogDump( zLogger,"external_on_button_onoff is starting." )

    if common.checkPythonInterpreter(zLogger) == False:
        common.LogDump( zLogger,"Let's stop now !")
        sys.exit(1)

    opt_debug = False

    try:
        opts, args = getopt.getopt(argv,"d",["debug"])
    except getopt.GetoptError:
        common.LogDump( zLogger, (__file__ + ' [-d/--debug]') )
        sys.exit(2)

    for opt,arg in opts:
        print (opt)
        if opt in ("-d", "--debug"):
            opt_debug = True

    common.OpenDatabase(zLogger)
    common.rdb.client_setname( "alarm_external_on_button_onoff_["+str(os.getpid())+"]" )

    if opt_debug == True:
        common.LogDump( zLogger, "Debug is activated" )

    #recuperer la liste des variables de notification
    liste_EnvNotify = common.getEnvironmentWithPrefix(zLogger)
    common.LogDump( zLogger, str(liste_EnvNotify) )

    #controle presence action 'click' :  'simple' active l'alarme, 'long_release' arrete l'alarme 
    s_action = alarm_settings.prefix_notification_variables + 'click'
    if s_action in liste_EnvNotify:
        common.LogDump( zLogger, liste_EnvNotify[s_action] )
        if 'single' == liste_EnvNotify[s_action]:
            common.LogDump( zLogger, "Starting alarm monitoring" )
            time.sleep(20)
        elif 'long_release'  == liste_EnvNotify[s_action]:
            common.LogDump( zLogger, "Stopping alarm monitoring" )
        else:
            common.LogDump( zLogger, "Ignoring action (1)")
    else:
        common.LogDump( zLogger, "Ignoring action (2)")
        
    common.CloseDatabase( zLogger )

    common.LogDump( zLogger,"external_on_button_onoff is exiting." )

    sys.exit(0)

######## main ########

if __name__ == "__main__": 
    file_name = os.path.basename(sys.argv[0])
    zLogger = common.StartLogging( alarm_settings.LogFolder,file_name )
    common.LogDump( zLogger,file_name )
    main(sys.argv[1:])
