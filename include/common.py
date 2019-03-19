import os
import asyncio
import time,datetime
import subprocess
import logging
import logging.handlers
import fcntl
import sys
import sqlite3
import collections
import json
import redislite
import alarm_settings

#variable globale (common.rdb)
rdb = None

scriptDirectory = os.path.dirname(os.path.realpath(__file__)) 

def OpenDatabase(wLogger, mylogfile=True, mydumpstdout=True, mydumpstderr=False):
  global rdb
  fName = "OpenDatabase::"
  LogDump( wLogger, fName + "db(" + alarm_settings.Redis_Db_Path + ")",mylogfile,mydumpstdout,mydumpstderr )
  rdb = redislite.StrictRedis(alarm_settings.Redis_Db_Path)
  LogDump( wLogger, fName + "db_socket=[" + rdb.socket_file + "]",mylogfile,mydumpstdout,mydumpstderr)

def CloseDatabase(wLogger, mylogfile=True, mydumpstdout=True, mydumpstderr=False):
  fName = "CloseDatabase::"
  global rdb
  LogDump( wLogger, fName + "db(" + alarm_settings.Redis_Db_Path +")", mylogfile, mydumpstdout, mydumpstderr )
  LogDump( wLogger, fName + "db_socket=[" + rdb.socket_file + "]", mylogfile, mydumpstdout, mydumpstderr)
  rdb.connection_pool.disconnect()

def StartLogging(folder,fichier):
  my_logger = logging.getLogger('MyLogger')
  my_logger.setLevel(logging.DEBUG)
  zfolder = folder.rstrip("/")
  zfichier = fichier.rstrip('.py')
  formatter = logging.Formatter('%(asctime)s :: %(levelname)s :: %(process)d :: %(message)s')
  handler = logging.handlers.RotatingFileHandler(zfolder +'/'+zfichier+'.log', maxBytes=1024*1024 *2, backupCount=5)
  handler.setFormatter(formatter)
  my_logger.addHandler(handler)
  return my_logger

def LogDump(oLogger, chaine,logfile=True,dumpstdout=True,dumpstderr=False):
  if logfile == True:
    if oLogger != None:
      oLogger.debug(chaine)
  if dumpstdout == True:
    print ( "["+str(os.getpid())+"]::"+ time.strftime("%Y-%m-%d %X") + "::out::script::" + os.path.basename(sys.argv[0]) + "::" + chaine )
  if dumpstderr == True:
    sys.stderr.write(chaine)
    sys.stderr.flush()

#obtenir un timestamp
def GetTimeStamp():
  return int(time.time())

  #convertir un ts en texte
def TsToData(local_ts):
 if local_ts == 'nan':
   return 'nan'
 return time.strftime("%b %d %Y %H:%M", time.localtime(float(local_ts)))

#compare les donnes, ainsi que l'heure de mise a jour
#time_in_minutes : ecart max en timestamps
def CheckValidityData(local_ts, update_ts, time_in_minutes):
  if str(update_ts) == '??':
    return False
  val_update_ts = int(update_ts)
  # donnees obsoletes de collecte ? plus de n minutes
  if (local_ts - val_update_ts) > (time_in_minutes * 60):
    return False
  return True

def ProcessMQTTMessage(wLogger, TypeMsg , topic, payload):
  fName = "ProcessMQTTMessage::"
  LogDump( wLogger, fName + "typeof(["+ topic + "]/[" + payload+ "])=" + str(TypeMsg) )
  if  ( TypeMsg == alarm_settings.TypeMqttMessage.Status ):
    pass
  elif ( TypeMsg == alarm_settings.TypeMqttMessage.Sensor ):
    SplitSensorInfos( wLogger, topic, payload )
  elif ( TypeMsg == alarm_settings.TypeMqttMessage.Config ):
    pass
  else:
    LogDump(wLogger, fName + "Attention le type est [Unknown]!!")
  return    

def IsIEEEObjectInDB(wLogger,id_object):
  fName = "IsIEEEObjectInDB::"
  global rdb
  if rdb.exists(id_object) == False:
    LogDump (wLogger,fName + "Key [" + id_object + "] NOT in DB")
    return False
  else:
    LogDump( wLogger,fName + "Key ["+ id_object + "] found in DB" )
    return True
 
def SplitSensorInfos(wLogger,topic, zpayload):
  fName = "SplitSensorInfos::"
  global rdb

  LogDump ( wLogger, fName + "Starting Sensor processing" )
  
  #remplacer :false, par :"False", idem pour true en vue d'insertion en DB
  #car en cas d'import JSON ça foire
  zpayload = zpayload.replace( ':true',':"True"' )
  zpayload = zpayload.replace( ':false',':"False"' )
  zpayload = zpayload.replace( ':False',':"False"' )
  zpayload = zpayload.replace( ':True',':"True"' )

  ts_now = GetTimeStamp()
  #recupere la chaine apres le dernier / dans le topic
  id_object = topic [topic.rfind("/")+1:]
  LogDump( wLogger,"idobject=["+str(id_object)+"]" )
  #verifier si objet dans database, sinon on le drop
  if IsIEEEObjectInDB(wLogger,id_object+":sensor") == False:
    return

  #recuperation d'infos sur la capteur en BDD afin de determiner les champs 
  #a recuperer
  #                                   0       1          2
  mark_sensor = rdb.hmget(id_object+":sensor","type","model","fields_to_save")

  #liste des champs a stocker en BDD
  zfields_to_save = mark_sensor[2].decode('utf8')
  zfields_to_save = '{ "fields": ' + zfields_to_save + '}' 
  #remplacer les quotes simples par des doubles
  zfields_to_save = zfields_to_save.replace("'","\"")
  
  #inserer un timestamp dans le payload, du genre :
  #{ "event_ts":1552403607, "type": "DO", "model": "Xiaomi", "data":{"battery":97,"voltage":2995,"contact":false,"linkquality":105} }
  
  #djs = dynamic json  
  djs_payload = json.loads(zpayload)
  djs_payload["id_object"] = id_object + ':sensor'
  djs_payload["date_activity"] =  str(ts_now)
  djs_payload["type"] =  mark_sensor[0].decode('utf8')
  djs_payload["model"] = mark_sensor[1].decode('utf8')

  zpayload = str(djs_payload).replace("'","\"")
  LogDump ( wLogger, fName + "payload built is [" + zpayload + "]" )
  
  #determiner le nom de la file d'attente en fonction du model de sensor
  rdb_message_queue = alarm_settings.rdb_message_queue[ djs_payload["model"].lower() ]
  
  #inserer dans la liste le payload fabrique
  LogDump ( wLogger, fName + "inserting into event list [" + rdb_message_queue + "]" )
  rdb.rpush (rdb_message_queue ,zpayload.replace("'","\""))
  
  #isoler la liste des champs a recuperer du json : passage en json pour split
  LogDump ( wLogger, fName + "fields_to_save is [" + zfields_to_save + "]" )
  djs_fields = json.loads(zfields_to_save)
  #for i in djs_fields[0]:
  #  LogDump( wLogger, fName + " value(" + str(i) + ")=" + str(djs_fields[i]) )
  for i in range(0,len(djs_fields['fields'])):
    #nom du champ a remplacer en DB par celui du JSON
    field_name = str( djs_fields['fields'][i] )
    #valeur associée au champ dans le json
    new_value_of_field = str(djs_payload[field_name])
    LogDump( wLogger, fName + "setting field to DB [" + field_name + "]=" + new_value_of_field)
    rdb.hset(id_object+":sensor", field_name, new_value_of_field) 
    #Indique que le capteur est actif
    rdb.hset(id_object+":sensor", "isalive", "True")

  #TODO: pousser une notification au consommateur
  #rdb.publish()
  LogDump ( wLogger, fName + "Ending Sensor processing" )

  return

#maj. des champs isalive des capteurs
def UpdateSensorsActivity(wLogger, sensortimeout, mylogfile=True, mydumpstdout=True, mydumpstderr=False):
  fName = "UpdateSensorsActivity::"
  LogDump ( wLogger, fName + "Refreshing sensor activity table", True, False, False )
  global rdb

  ts_now = GetTimeStamp()

  for key in rdb.scan_iter("*:sensor"):
    LogDump ( wLogger, fName + "scanning sensor ["+ str(key) +"]", True, False, False ) 
    date_activity = rdb.hget(key,"date_activity").decode('utf8')
    #date_activity contient il autre chose que ??
    if  (date_activity != '??'):
      #conversion en nombre de la chaine
      date_activity = int(date_activity)
      if (ts_now - date_activity) > sensortimeout:
        rdb.hset(key, "isalive", "False" )
        LogDump ( wLogger, fName + "sensor ["+ str(key) +"] outdated",  True, False, False ) 
      else:
        rdb.hset(key, "isalive", "True" )
        LogDump ( wLogger, fName + "sensor ["+ str(key) +"] is alive", True, False, False )
    else:
      #data_activity=?? donc on ecrase isalive egalement
      LogDump ( wLogger, fName + "sensor ["+ str(key) +"] has never been connected", True, False, False ) 
      rdb.hmset( key, {"date_activity":"??","isalive":"False"} )
  return

#lister les sensors avec leurs etats
def GetSensorsStatus(wLogger, FullList = False, mylogfile=True, mydumpstdout=True, mydumpstderr=False):
  #si FullList== True, retourne un etat de tous les capteurs
  fName = "GetSensorsStatus::"
  LogDump ( wLogger, fName + "Starting",  mylogfile, mydumpstdout, mydumpstderr)

  #fabriquer un dictionnaire depuis la db redis, en ajoutant un champ "something_security_detected"
  #concernant uniquement les DO et les PIR
  status_security_sensors = {}
  for key in rdb.scan_iter("*:sensor"):
    row = rdb.hmget(key, "model","type","isenabled","isalive","description","contact","occupancy","location","zone","date_activity","voltage","battery")
    model_s = row[0].decode('utf8').lower() if row[0] != None else '??'
    type_s = row[1].decode('utf8').lower() if row[1] != None else '??'
    isenabled_s = row[2].decode('utf8').lower() if row[2] != None else '??'
    isalive_s = row[3].decode('utf8').lower() if row[3] != None else '??'
    description_s =  row[4].decode('utf8').lower() if row[4] != None else '??'
    contact_s =  row[5].decode('utf8').lower() if row[5] != None else '??'
    occupancy_s = row[6].decode('utf8').lower() if row[6] != None else '??'
    location_s = row[7].decode('utf8').lower() if row[7] != None else '??'
    zone_s = row[8].decode('utf8').lower() if row[8] != None else '??' 
    date_activity_s = row[9].decode('utf8').lower() if row[9] != None else '??'  
    voltage_s = row[10].decode('utf8').lower() if row[10] != None else '??'
    battery_s = row[11].decode('utf8').lower() if row[11] != None else '??'  

    skey = key.decode('utf8')

    #on ne prend en compte que les PIR et les DO xiaomi/arduinocustom activés (isenabled)
    if (model_s == 'xiaomi') or (model_s == 'arduinocustom'):
      if (FullList == True) or ( (type_s == 'pir' or type_s == 'do') and (isenabled_s == 'true') ):
        human_date_activity_s = "??"
        if date_activity_s != "??":
          human_date_activity_s = datetime.datetime.fromtimestamp(int(date_activity_s)).isoformat()
          
        status_security_sensors[skey] = { "model": model_s, "type": type_s, "isenabled": isenabled_s, \
        "isalive": isalive_s, "description": description_s, "contact": contact_s, \
        "occupancy": occupancy_s, "location": location_s, "zone": zone_s, \
        "date_activity": date_activity_s, "voltage": voltage_s, "battery": battery_s, \
        "human_date_activity": human_date_activity_s, \
        "something_security_detected": False }

        if HasCaptorDetectedSomething( wLogger, status_security_sensors[skey], mylogfile, mydumpstdout, mydumpstderr) == True:
          status_security_sensors[skey]["something_security_detected"] = True
  
        LogDump ( wLogger, fName + "done [" + str(status_security_sensors[skey]) + "]" , mylogfile, mydumpstdout, mydumpstderr) 
 
  LogDump ( wLogger, fName + "count_sensors=["+ str(len(status_security_sensors)) + ']|list_sensors=[' + str(status_security_sensors) + "]" , mylogfile, mydumpstdout, mydumpstderr)
  #LogDump ( wLogger, fName + "scanning sensor ["+ str(key) +"]/[" + row[4].decode('utf8') + "]" )
  
  LogDump ( wLogger, fName + "Ending", mylogfile, mydumpstdout, mydumpstderr)
  return status_security_sensors

def HasCaptorDetectedSomething(wLogger,dict_sensors_secu, mylogfile=True, mydumpstdout=True, mydumpstderr=False):
  fName = "HasCaptorDetectedSomething::"
  #renvoie True si un DO n'est pas en contact avec son aimant, ou si une presence est detectee par un PIR, False sinon

  if ( (dict_sensors_secu['type'] == 'pir') or (dict_sensors_secu['type'] == 'do') ) \
      and (dict_sensors_secu['isenabled']=='true') and (dict_sensors_secu['isalive']=='true'): 

    #DO
    if (dict_sensors_secu['type'] == 'do'):
      if  dict_sensors_secu['contact'] == 'true':
        LogDump ( wLogger, fName + "DO is normal", mylogfile, mydumpstdout, mydumpstderr )
        return False
      LogDump ( wLogger, fName + "DO is opened", mylogfile, mydumpstdout, mydumpstderr )
      return True
    #PIR 
    #occupancy = true ?
    if  dict_sensors_secu['occupancy'] == 'true':
      LogDump ( wLogger, fName + "PIR detected something", mylogfile, mydumpstdout, mydumpstderr )
      return True
    LogDump ( wLogger, fName + "PIR is normal", mylogfile, mydumpstdout, mydumpstderr )
    return False   
    
  return False

#demarrer une action externe
def LaunchExternalAction(wLogger, filename, SyncMode, ListeVariablesEnv, mylogfile=True, mydumpstdout=True, mydumpstderr=False):
  fName = "LaunchExternalAction::"
  LogDump ( wLogger, fName + "Launching ["+ filename +"]|SyncMode ["+ SyncMode +"]",mylogfile, mydumpstdout, mydumpstderr ) 
  my_env = os.environ.copy()
  for item in ListeVariablesEnv:
    my_env[item] = str(ListeVariablesEnv[item])
    #print ( item + '|' + str(ListeVariablesEnv[item]) )
  #print(filename +"|"+ SyncMode)
  p = subprocess.Popen( filename, stdout=subprocess.PIPE, env=my_env, shell=True, stderr=subprocess.PIPE )
  if SyncMode == True:
    while True:
      out = p.stderr.read(1)
      if out == '' and p.poll() != None:
        break
      if out != '':
        sys.stdout.write(out)
        sys.stdout.flush()
  else:
    sys.stdout.write("[" + time.strftime("%Y/%m/%d %H:%M:%S") + "]:Asynchrone ["+ str(p.pid) +"]\n")
    sys.stdout.flush()
  return

#retourne une liste des variables d'environnement commençant par 
#alarm_settings.prefix_notification_variables
def getEnvironmentWithPrefix(wLogger, mylogfile=True, mydumpstdout=True, mydumpstderr=False):
  list_Env={}
  for i in os.environ:
    if alarm_settings.prefix_notification_variables in i:
      list_Env[i] = os.environ[i]
      #LogDump ( wLogger, i + '=' + list_Env[i], mylogfile, mydumpstdout, mydumpstderr )
  return list_Env


#controle l'interpreteur actif
def checkPythonInterpreter(wLogger, mylogfile=True, mydumpstdout=False, mydumpstderr=False):
  LogDump( wLogger,"venv should be ["+ alarm_settings.pythonscripter +"]", mylogfile, mydumpstdout, mydumpstderr)
  current_interpreter = sys.executable
  if ( current_interpreter != alarm_settings.pythonscripter ):
      LogDump( wLogger,"Wrong interpreter ["+ current_interpreter +"]", mylogfile, mydumpstdout, mydumpstderr)
      return False
  return True


#demarrage de la surveillance
def startingAlarmMonitoring(wLogger):
  return

#controle des batteries
def checkingBatteryLevel(wLogger):
  return
  
#lancement de processus externe
def invoke(wLogger, command,s_standard=False, s_err=True):
  fName = "invoke::"
  '''
  Invoke command as a new system process and return its output.
  '''
  my_env = os.environ.copy()
  #Common.LogDump(wLogger, "Launching ["+ command +"]\n", True, s_standard, s_err)
  return subprocess.Popen(command, stdout=PIPE, env=my_env, shell=True).stdout.read()

#controle de l'etat des capteurs/piles/voltage
def CheckSensorsActivity(wLogger):
  return