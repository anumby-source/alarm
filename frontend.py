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
sys.path.insert(0, scriptDirectory + '/./include')

import alarm_settings
import common

def main(argv):
    common.LogDump( zLogger,"Frontend is starting." )

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
    common.rdb.client_setname("alarm_frontend")

    if opt_debug == True:
        common.LogDump( zLogger, "Debug is activated" )


    while (True):
        #polling de la liste : attendre jusqu'a 60 secondes max
        evt = common.rdb.blpop("sensor_status:events",30)
        if evt != None:
            #nom de la liste qui a genere l'evenement
            liste_id = evt[0].decode('utf8') 
            #les donnees quasi json
            data = evt[1].decode('utf8')
            common.LogDump( zLogger, "Event from [" + liste_id + '] is [' + data + "]" )
            #on met en forme le quasi-json en json en inserant un sujet à gauche
            djson = json.loads('{ "params": ' + data + ' }')        
            #print ( common.rdb.exists("id_object") )
            id_object = djson['params']['id_object'] 
            if (common.rdb.hexists(id_object, "external_action")) and (common.rdb.hexists(id_object, "external_action_mode_synchronous")):
                external_action = common.rdb.hget( id_object, "external_action" )
                #lancement synchrone ou asynchrone
                external_mode = common.rdb.hget( id_object, "external_action_mode_synchronous")
                if ( (external_action != None) and (external_mode != None) ):
                    external_action = external_action.decode('utf8')
                    external_mode = external_mode.decode('utf8')
                    common.LogDump( zLogger, "External action exists for ["+ id_object +"]=["+ external_action +"], sync=["+ external_mode +"]" )
                    #traduction du json en variables d'environnement pour fork
                    ListeEnvVars = {}
                    for item in djson['params']:
                        #prefixer les variables par un prefixe defini dans alarm_settings.py
                        ListeEnvVars[alarm_settings.prefix_notification_variables + item] = djson['params'][item] 
                    common.LaunchExternalAction( zLogger, alarm_settings.ExternalFolder + external_action, external_mode ,ListeEnvVars )   
                else:
                    common.LogDump( zLogger, "Problem on external_action / external_action_mode_synchronous for  ["+ id_object +"]" )
                
            else:
                common.LogDump( zLogger, "No functionnal external action available ["+ id_object +"]" )
            #maj des champs isalive par rapport au timestamp
            common.UpdateSensorsActivity(zLogger,alarm_settings.SensorTimeOut)
            # liste des capteurs
            common.GetSensorsStatus(zLogger)
        else:
            #ici rien ne s'est passe par le timeout d'attente sur la liste
            common.LogDump( zLogger, "Nothing new today",True,True,False )

    sys.exit(5)

    common.CloseDatabase(zLogger)

######## main ########

if __name__ == "__main__": 
    file_name = os.path.basename(sys.argv[0])
    zLogger = common.StartLogging( alarm_settings.LogFolder,file_name )
    common.LogDump( zLogger,file_name )
    main(sys.argv[1:])
