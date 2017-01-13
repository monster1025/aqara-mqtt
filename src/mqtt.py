import paho.mqtt.client as mqtt
import os
import logging
from queue import Queue
from threading import Thread

_LOGGER = logging.getLogger(__name__)

class Mqtt:
	username = ""
	password = ""
	server = "localhost"
	port = 1883
	prefix = "home"
	
	_client = None
	_sids = None
	_queue = None
	_threads = None

	def __init__(self, config):
		if (config == None):
			raise "Config is null"

		#load sids dictionary
		self._sids = config.get("sids", None)
		if (self._sids == None):
			self._sids = dict({})

		#load mqtt settings
		mqttConfig = config.get("mqtt", None)
		if (mqttConfig == None):
			raise "Config mqtt section is null"

		self.username = mqttConfig.get("username", "")
		self.password = mqttConfig.get("password", "")
		self.server = mqttConfig.get("server", "localhost")
		self.port = mqttConfig.get("port", 1883)
		self.prefix = mqttConfig.get("prefix", "home")
		self._queue = Queue()
		self._threads = []

	def connect(self):
		_LOGGER.info("Connecting to MQTT server " + self.server + ":" + str(self.port) + " with username (" + self.username + ":" + self.password + ")")
		self._client = mqtt.Client()
		if (self.username != "" and self.password != ""):
			self._client.username_pw_set(self.username, self.password)
		self._client.on_message = self._mqtt_process_message
		self._client.on_connect = self._mqtt_on_connect
		self._client.connect(self.server, self.port, 60)
        
        #run message processing loop
		t1 = Thread(target=self._mqtt_loop)
		t1.start()
		self._threads.append(t1)

	def subscribe(self, model="+", name="+", prop="+", command="set"):
		topic = self.prefix + "/" + model + "/" + name + "/" + prop + "/" + command
		_LOGGER.info("Subscibing to " + topic + ".")
		self._client.subscribe(topic)

	def publish(self, model, sid, data, retain=True):
		sidprops = self._sids.get(sid, None)
		if (sidprops != None):
			model = sidprops.get("model",model)
			sid = sidprops.get("name",sid)

		# _LOGGER.info("data is " + format(data))
		PATH_FMT = self.prefix + "/{model}/{sid}/{prop}"
		for key, value in data.items():
			# fix for latest motion value
			if (model == "motion" and key == "no_motion"):
				key="status"
				value="no_motion"
			
			# fix for rgb format
			# if (key == "rgb" and self._is_int(value)):
			# 	intval = int(value)
			# 	blue =  (intval) & 255
			# 	green = (intval >> 8) & 255
			# 	red =  (intval >> 16) & 255
			# 	value = str(red)+","+str(green)+","+str(blue)

			topic = PATH_FMT.format(model=model, sid=sid, prop=key)
			_LOGGER.info("Publishing message to topic " + topic + ": " + str(value) + ".")
			self._client.publish(topic, payload=value, qos=0, retain=retain)

	def _mqtt_on_connect(self, client, userdata, rc, unk):
		_LOGGER.info("Connected to mqtt server.")

	def _mqtt_process_message(self, client, userdata, msg):
		_LOGGER.info("Processing message in " + str(msg.topic) + ": " + str(msg.payload) + ".")
		parts = msg.topic.split("/")
		if (len(parts) != 5):
			return
		model = parts[1]
		query_sid = parts[2] #sid or name part
		param = parts[3] #param part
		value = (msg.payload).decode('utf-8')
		if self._is_int(value):
			value = int(value)
		name = "" # we will find it next
		sid = query_sid

		for current_sid in self._sids:
			if (current_sid == None):
				continue
			sidprops = self._sids.get(current_sid, None)
			if sidprops == None:
				continue
			sidname = sidprops.get("name", current_sid)
			sidmodel = sidprops.get("model", "")
			if (sidname == query_sid and sidmodel == model):
				sid = current_sid
				name = sidname
				break
			else:
				_LOGGER.debug(sidmodel + "-" + sidname + " is not " + model + "-" + query_sid + ".")
				continue

		# fix for rgb format
		if (param == "rgb" and "," in str(value)):
			arr = value.split(",")
			r = int(arr[0])
			g = int(arr[1])
			b = int(arr[2])
			value = int('%02x%02x%02x%02x' % (255, r, g, b), 16)

		data = {'sid': sid, 'model': model, 'name': name, 'param':param, 'value':value}
		# put in process queuee
		self._queue.put(data)

	def _mqtt_loop(self):
		_LOGGER.info("Starting mqtt loop.")
		self._client.loop_forever()

	def _is_int(self, x):
		try:
			tmp = int(x)
			return True
		except Exception as e:
			return False
