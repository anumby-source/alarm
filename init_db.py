#!/usr/bin/env python3
#dossier virtuel

#traitement a appliquer en cas de modifiction du fichier status.tpl.json (et donc status.json via moulinette dans tool)
#l'option -p permet de vider completement la base, ayant pour consequence la perte des infos sur la derniere activation
#des capteurs

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
sys.path.insert(0,scriptDirectory + '/include')

import alarm_settings
import common

def main(argv):
    opt_purge = False

    try:
        opts, args = getopt.getopt(argv,"p",["purgedb"])
    except getopt.GetoptError:
        common.LogDump( zLogger, (__file__ + ' [-p / --purgedb]') )
        sys.exit(2)

    for opt,arg in opts:
        if opt in ("-p", "--purgedb"):
            opt_purge = True

    with open(alarm_settings.OutputStatusJson, "r") as read_file:
        data = json.load(read_file)
    print (data)

    common.OpenDatabase(zLogger)
    common.rdb.client_setname("alarm_DB_refresh")

    if opt_purge == True:
        common.LogDump( zLogger, "Flushing database" )
        common.rdb.flushdb() 
    else:
        common.LogDump( zLogger, "Fine cleaning database" )

    common.LogDump( zLogger,"Cleaning database from key not existing in json status" )
    for key in common.rdb.keys("*"):
        key = key.decode('utf8')
        common.LogDump (zLogger,"Checking key ["+ key +"]")
        if key not in data:
            common.LogDump( zLogger,"Deleting from DB ["+ key +"]" )
            common.rdb.delete(key)

    common.LogDump( zLogger,"Updating leaf in database from json status" )

    for cle in data:
        for j in data[cle]:
            #dn = '[' + cle + '][' + j + ']=' + str(data[cle][j])
            hashkey = '['+ cle + '].[' + j + ']'
            value = str(data[cle][j])
            common.LogDump( zLogger,"leaf ["+ cle +"."+j+"=" + value + "]" )
            #print (hashkey,'=',value)
            if (value == '??'):
                if common.rdb.hexists(cle,j) == True:
                    common.LogDump( zLogger, "Do not overwrite HSET" )
                else:
                    common.LogDump( zLogger, "Overwrite HSET" )
                    common.rdb.hset( cle,j,str(data[cle][j]) )
            else:
                common.LogDump( zLogger, "Overwrite HSET" ) 
                #valeur a inserer car differente de ??
                common.rdb.hset( cle,j,str(data[cle][j]) )

    #maj des champs isalive par rapport au timestamp
    common.UpdateSensorsActivity(zLogger,alarm_settings.SensorTimeOut)

    common.CloseDatabase(zLogger)

######## main ########

if __name__ == "__main__": 
    file_name = os.path.basename(sys.argv[0])
    zLogger = common.StartLogging( alarm_settings.LogFolder,file_name )
    common.LogDump( zLogger,file_name )
    main(sys.argv[1:])
