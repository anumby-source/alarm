from enum import Enum

#MQTT topics a souscrire du backend
PrefixGwMqtt = "zigbee2mqtt/"
TopicSensorXiaomi = PrefixGwMqtt + "0x"

PrefixArduinoMqtt = "arduinocustom/"
TopicSensorCustom = PrefixArduinoMqtt + "0x"

TopicStatusGW = PrefixGwMqtt + "bridge/state"
TopicConfigGW = PrefixGwMqtt + "bridge/config"
MQTT_Alarm_Topics = [ (PrefixGwMqtt + '#',1),(PrefixArduinoMqtt + '#',1) ]

MQTT_Server = '10.0.96.1'
MQTT_Port = 1883

class TypeMqttMessage(Enum):
    Sensor = 1
    Status = 2
    Config = 3
    Unknown = 4

#interpreteur venv a personnaliser
pythonscripter = "/home/mikou/Documents/python-backend/myprojet/bin/python3"

# chemins globaux
RootFolder = '/home/mikou/Documents/python-backend/'
LogFolder = RootFolder + 'log/'
DataFolder = RootFolder + 'data/'

#dossier externe
ExternalFolder =  "external/"

#DB Redis locale
Redis_Db_Path = DataFolder + "redis.db"

#section pour le dossier tool
InputStatusJsonTpl = DataFolder + "status.tpl.json"
OutputStatusJson = DataFolder + "status.json"

#si un capteur ne s'est pas manifeste depuis SensorTimeOut secondes (62 minutes) 
#il est considere comme inactif
SensorTimeOut = 60 * 62

#message queue (liste redis) RDB en fonction du fournisseur
#le nom du fournisseur en minuscule
rdb_message_queue={"xiaomi": "sensor_status:events",\
    "arduinocustom":"sensor_status:events"}

#lors de l'appel de script externe, prefixer les variables d'environnement du parent ainsi
prefix_notification_variables = 'notification_'

