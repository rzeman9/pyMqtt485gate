import serial
import Simple485
import Mqtt485gate

import paho.mqtt.client as mqtt
import ssl

import logging

MQTT_CACERT = None #"cacert.pem"
MQTT_CERT = None  # user certificate for authentication
MQTT_KEY = None # key for cert
MQTT_SERVER = "10.0.0.2"
MQTT_PORT = 1883
MQTT_REQUIRECERT = ssl.CERT_OPTIONAL #ssl.CERT_REQUIRED
MQTT_TLSVERSION = ssl.PROTOCOL_TLSv1
MQTT_USERNAME = ""
MQTT_PASSWD = ""
MQTT_KEEPALIVE = 60

SERIALPORT = "COM13"
BAUDRATE = 9600
ADDR = b'\x1b'

logger = logging.getLogger('gate')
logger.handlers = []
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter('%(asctime)s %(name)-15s %(message)s', '%H:%M:%S'))
logger.addHandler(ch)
ch = logging.FileHandler('log.txt')
ch.setLevel(logging.DEBUG)
ch.setFormatter(logging.Formatter('%(asctime)s %(name)-10s %(levelname)-8s %(message)s'))
logger.addHandler(ch)
logger.info('Log open.')

ser = serial.Serial()
ser.port = SERIALPORT
ser.baudrate = BAUDRATE

def mqttConnected(client, userdata, flags, rc):
  logger.info("MQTT connected, code " + str(rc) + ".")
  client.subscribe("#", 1)
  logger.debug("MQTT subscribe all.")

def mqttDisconnected(client, userdata, rc):
  if rc != 0:
    logger.warning("MQTT disconnected. Reconnecting.")
    mqttc.reconnect()
  else:
    logger.info("MQTT disconnected.")

mqttc = mqtt.Client()
#mqttc.tls_set(MQTT_CACERT, MQTT_CERT, MQTT_KEY, MQTT_REQUIRECERT, MQTT_TLSVERSION)
mqttc.on_connect = mqttConnected
mqttc.on_disconnect = mqttDisconnected
mqttc.username_pw_set(MQTT_USERNAME, MQTT_PASSWD)
try:
  mqttc.connect(MQTT_SERVER, MQTT_PORT, MQTT_KEEPALIVE)
except ConnectionRefusedError:
  logger.error("Mqtt connection refused.")
  exit(1)
except:
  logger.error("Mqtt connection failed.")
  exit(1)

try:
  ser.open()
except serial.SerialException as e:
  logger.error('Could not open serial port {}: {}.'.format(ser.name, e))
  mqttc.disconnect()
  exit(1)
else:
  logger.info("Serial port open.")
    

rs485 = Simple485.Simple485(ser, ADDR)
mqtt485 = Mqtt485gate.Mqtt485gate(rs485, mqttc)

def mqttReceived(client, userdata, msg):
  logger.debug("Received from MQTT in topic " + msg.topic + ":" + str(msg.payload))
  mqtt485.receivemqtt(msg)

mqttc.on_message = mqttReceived

while 1:
  try:
    rs485.loop()
    while rs485.received() > 0:
      m = rs485.read()
      src = m[0]
      ln = m[1]
      msg = m[2]
      logger.debug("Received from RS-485: " + str(ln) + " from " + str(src))
      logger.debug(msg)
      mqtt485.receive485(src, ln, msg)
    mqttc.loop()
  except KeyboardInterrupt:
    logger.info("Closing")
    ser.close()
    mqttc.disconnect()
    exit(0)
