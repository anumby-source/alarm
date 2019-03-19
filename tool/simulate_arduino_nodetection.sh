#!/bin/bash

#([zigbee2mqtt/0x00158d000252acd4]/[{"battery":91,"voltage":2985,"contact":true,"linkquality":2}]
#zigbee2mqtt/0x00158d000252acd4 {"battery":91,"voltage":2985,"contact":false,"linkquality":47}

mosquitto_pub -d -h 10.0.96.1 -p 1883 -t 'arduinocustom/0x0000010000000001' -m '{"contact":true}'
