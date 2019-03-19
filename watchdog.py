#!/usr/bin/env /home/mikou/Documents/python-backend/myprojet/bin/python3
#cf. alarm_environment_python

import time, multiprocessing, subprocess, os
import fcntl
import signal
import sys
import logging
import logging.handlers
import datetime
import math
import os

scriptDirectory = os.path.dirname(os.path.realpath(__file__))
os.chdir(scriptDirectory)
sys.path.insert(0,scriptDirectory + '/include')

import alarm_settings
import common

def start_and_wait(my_processdisplay,my_processname):
    common.LogDump( zLogger,"starting process ["+my_processdisplay+"]:"+str(my_processname) )

    command = my_processname  
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=None)
    process.communicate()
    common.LogDump( zLogger,"finished ["+my_processdisplay+"]" )

def launch(displayname,my_args):
    p=multiprocessing.Process(target=start_and_wait,args=(displayname,my_args) )
    p.start()
    return p

def checkAliveAndRestart(p,displayname,my_args):
    if (p is None) or (p.is_alive()==False):
        p = launch( displayname,my_args )
    else:
        common.LogDump( zLogger, "process ["+ displayname +"] found")
    return p

def main(argv):
    common.LogDump( zLogger, "Main is starting")

    p1 = p2 = p3 = None

    while(1):
        p1 = checkAliveAndRestart( p1,"Backend MQTT",[alarm_settings.pythonscripter, alarm_settings.RootFolder+"backend.py"] )
        #laisse le temps de demarrer la base redis embarquee de reference
        #afin que tout le monde accroche la meme instance de socket
        time.sleep(2)
        p2 = checkAliveAndRestart( p2,"Frontend",[alarm_settings.pythonscripter, alarm_settings.RootFolder+"frontend.py"] )
        #p3 = checkAliveAndRestart(p3,"Camera moniteur",["/bin/bash", "/home/mikou/mycam.sh"])
        time.sleep(60)


######## main ########

if __name__ == "__main__": 
    file_name = os.path.basename(sys.argv[0])
    zLogger = common.StartLogging( alarm_settings.LogFolder,file_name )
    common.LogDump( zLogger,file_name, True,False,False )

    if common.checkPythonInterpreter(zLogger) == False:
        common.LogDump( zLogger,"Let's stop now !")
        sys.exit(1)

    main(sys.argv[1:])
