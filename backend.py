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
sys.path.insert(0, scriptDirectory + '/./include')

import alarm_settings
import common


# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    fName = "on_connect::"
    common.LogDump (zLogger,fName + "Connected with result code "+str(rc) )

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    #client.subscribe("/#")
    client.subscribe( alarm_settings.MQTT_Alarm_Topics )

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    topic = str(msg.topic)
    #decodage du binaire payload
    payload = msg.payload.decode('utf8')

    #print ( common.TsToData(common.GetTimeStamp()) )
    if (alarm_settings.TopicSensorXiaomi in topic) or (alarm_settings.TopicSensorCustom in topic):  
        #information de sensor, on traite  
        common.ProcessMQTTMessage( zLogger,alarm_settings.TypeMqttMessage.Sensor,topic,payload) 
    elif alarm_settings.TopicStatusGW in topic:
        #info status de la GW, on traite
        common.ProcessMQTTMessage(zLogger,alarm_settings.TypeMqttMessage.Status,topic,payload) 
    elif alarm_settings.TopicConfigGW in topic:
        #info de config de la GW, on traite
        common.ProcessMQTTMessage(zLogger,alarm_settings.TypeMqttMessage.Config,topic,payload)
    else:
        #type inconnu : ne devrait pas arriver
        common.ProcessMQTTMessage(zLogger,alarm_settings.TypeMqttMessage.Unknown,topic,payload)



######## main ########
file_name = os.path.basename(sys.argv[0])
zLogger = common.StartLogging( alarm_settings.LogFolder,file_name )
common.LogDump( zLogger,file_name )

common.OpenDatabase(zLogger)
common.rdb.client_setname("mqtt_watcher")

common.LogDump (zLogger,'Topic subscribe list ' + str(alarm_settings.MQTT_Alarm_Topics) )

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(alarm_settings.MQTT_Server, alarm_settings.MQTT_Port, 60)

# Blocking call that processes network traffic, dispatches callbacks and
# handles reconnecting.
# Other loop*() functions are available that give a threaded interface and a
# manual interface.

client.loop_forever()

#a trapper sur CTRL+C
common.CloseDatabase(zLogger)
