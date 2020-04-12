import logging
logger = logging.getLogger('gate.Mqtt485')

def b2s(b):
  t = ""
  for c in b:
    if c == 0:
      break
    t += chr(c)
  return t

def topicMatch(t, tt): # does t include t
  if t[0] == "/":
    t = t[1:]
  if tt[0] == "/":
    tt = tt[1:]
  ts = t.split("/")
  tts = tt.split("/")
  if len(tts) > len(ts):
    return 0
  for i in range(0, len(ts)):
    if i >= len(tts):
      return 0
    elif tts[i] == "#":
      return 1
    elif tts[i] == "+":
      pass
    elif tts[i] == ts[i]:
      pass
    else:
      return 0
  return 1

  
NUL = b'\x00'

class Mqtt485gate:
  def __init__(self, rs485, mqttclient):
    logger.debug("Init.")
    self.rs485 = rs485
    self.mqttclient = mqttclient
    self.subscriptions = []
    b = b'mqini' + b'\x00'
    logger.info("Sending mqini.")
    self.rs485.send(b'\x00', b)
    
  def receive485(self, src, ln, msg):
    if ln >= 5 and msg[0:5] == b'mqsub':
      topic = b2s(msg[5:])
      logger.info("Received subscription for " + topic + " from " + str(src))
      if len([item for item in self.subscriptions if item[0] == src and item[1] == topic]) == 0:
        self.subscriptions.append((src, topic))
    elif ln >= 5 and msg[0:5] == b'mquns':
      topic = b2s(msg[5:])
      logger.info("Received unsubscription for " + topic + " from " + str(src))
      for i in [item for item in self.subscriptions if item[0] == src and item[1] == topic]:
        self.subscriptions.remove(i)
    elif ln >= 5 and msg[0:5] == b'mqpub':
      topic = b2s(msg[5:])
      msg = msg[5+len(topic)+1:]
      logger.info("Received publish to " + topic + " from " + str(src) + ":")
      logger.info(msg)
      self.mqttclient.publish(topic, msg)
  def receivemqtt(self, msg):
      toBeSent = set()
      logger.debug("To be sent: topic " + msg.topic + ", payload " + str(msg.payload) + ".")
      for i in self.subscriptions:
        if topicMatch(msg.topic, i[1]):
          toBeSent.add(i[0])
      logger.debug("Sending to: " + str(list(toBeSent)))
      for d in toBeSent:
        b = b'mqrcv' + msg.topic.encode() + NUL + msg.payload
        self.rs485.send(d, b)
        logger.debug("mqrcv sent.")
