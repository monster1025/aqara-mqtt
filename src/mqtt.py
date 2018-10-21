import paho.mqtt.client as mqtt
import logging
import os
import ssl
from queue import Queue
from threading import Thread
import json

_LOGGER = logging.getLogger(__name__)


class Mqtt:
    event_based_sensors = ["switch", "cube"]
    motion_sensors = ["motion", "sensor_motion.aq2"]
    magnet_sensors = ["magnet"]
    username = ""
    password = ""
    server = "localhost"
    port = 1883
    ca = None
    tlsvers = None
    prefix = "home"
    
    _client = None
    _sids = None
    _queue = None
    _threads = None

    def __init__(self, config):
        if (config == None):
            raise "Config is null"

        # load sids dictionary
        self._sids = config.get("sids", None)
        if (self._sids == None):
            self._sids = dict({})

        # load mqtt settings
        mqttConfig = config.get("mqtt", None)
        if (mqttConfig == None):
            raise "Config mqtt section is null"

        self.username = mqttConfig.get("username", "")
        self.password = mqttConfig.get("password", "")
        self.server = mqttConfig.get("server", "localhost")
        self.port = mqttConfig.get("port", 1883)
        self.prefix = mqttConfig.get("prefix", "home")
        self.ca = mqttConfig.get("ca",None)
        self.tlsvers = self._get_tls_version(
                mqttConfig.get("tls_version","tlsv1.2")
        )
        self.json = mqttConfig.get("json", False)
        self._queue = Queue()
        self._threads = []

    def connect(self):
        _LOGGER.info("Connecting to MQTT server " + self.server + ":" + str(self.port) + " with username (" + self.username + ":" + self.password + ")")
        self._client = mqtt.Client()
        if (self.username != "" and self.password != ""):
            self._client.username_pw_set(self.username, self.password)
        self._client.on_message = self._mqtt_process_message
        self._client.on_connect = self._mqtt_on_connect
        if (self.ca != None):
            self._client.tls_set(
                    ca_certs=self.ca,
                    cert_reqs=ssl.CERT_REQUIRED,
                    tls_version=self.tlsvers
            )

            self._client.tls_insecure_set(False)

        self._client.connect(self.server, self.port, 60)
        # run message processing loop
        t1 = Thread(target=self._mqtt_loop)
        t1.start()
        self._threads.append(t1)

    def disconnect(self):
        self._client.disconnect()
        self._queue.put(None)

    def subscribe(self, model="+", name="+", prop="+", command=None):
        topic = self.prefix + "/" + model + "/" + name + "/" + prop
        if command is not None:
            topic += "/" + command
        _LOGGER.info("Subscribing to " + topic + ".")
        self._client.subscribe(topic)

    def publish(self, model, sid, data, retain=True):
        sidprops = self._sids.get(sid, None)
        if (sidprops != None):
            model = sidprops.get("model", model)
            sid = sidprops.get("name", sid)

        items = {}
        for key, value in data.items():
            # fix for latest motion value
            if (model in self.motion_sensors and key == "no_motion"):
                key = "status"
                value = "no_motion"
            if (model in self.magnet_sensors and key == "no_close"):
                key = "status"
                value = "open"
            # do not retain event-based sensors (like switches and cubes).
            if (model in self.event_based_sensors):
                retain = False
            # fix for rgb format
            if (key == "rgb" and str(value).isdigit()):
                value = self._color_xiaomi_to_rgb(str(value))
            items[key] = value

        if self.json == True:
            PATH_FMT = self.prefix + "/{model}/{sid}/json"
            topic = PATH_FMT.format(model=model, sid=sid)
            values = {}
            values['sid'] = sid
            for key in items:
                values[key] = items[key]
            jsondata = json.dumps(values)
            _LOGGER.info("Publishing message to topic " + topic + ": " + str(jsondata) + ".")
            self._client.publish(topic, payload=jsondata, qos=0, retain=retain)
        else:
            for key in items:
                PATH_FMT = self.prefix + "/{model}/{sid}/{prop}"
                topic = PATH_FMT.format(model=model, sid=sid, prop=key)
                _LOGGER.info("Publishing message to topic " + topic + ": " + str(items[key]) + ".")
                self._client.publish(topic, payload=items[key], qos=0, retain=retain)

    def _mqtt_on_connect(self, client, userdata, rc, unk):
        _LOGGER.info("Connected to mqtt server.")

    def _mqtt_process_message(self, client, userdata, msg):
        _LOGGER.info("Processing message in " + str(msg.topic) + ": " + str(msg.payload) + ".")
        parts = msg.topic.split("/")
        if len(parts) < 4:
            # should we return an error message ?
            return

        model = parts[1]
        query_sid = parts[2]  # sid or name part
        param = parts[3]  # param part
        method = None
        if len(parts) > 4:
            method = parts[4]
        else:
            method = parts[3]

        name = ""  # we will find it next
        sid = query_sid
        isFound = False
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
                isFound = True
                break
            else:
                _LOGGER.debug(sidmodel + "-" + sidname + " is not " + model + "-" + query_sid + ".")
                continue

        if isFound == False:
            # should we return an error message ?
            return

        if method == "set":
            # use single value set method

            value = (msg.payload).decode('utf-8')
            if value.isdigit():
                value = int(value)

            # fix for rgb format
            if (param == "rgb" and "," in str(value)):
                value = self._color_rgb_to_xiaomi(value)

            # prepare values dict
            data = {'sid': sid, 'model': model, 'name': name,
                    'values': {param: value}}
            # put in process queuee
            self._queue.put(data)

        elif method == "write":
            # use raw write method to the sensor, we expect a jsonified dict here.
            values = json.loads((msg.payload).decode('utf-8'))
            data = {'sid': sid, 'model': model, 'name': name,
                    'values': values}
            # put in process queuee
            self._queue.put(data)

    def _mqtt_loop(self):
        _LOGGER.info("Starting mqtt loop.")
        self._client.loop_forever()

    def _color_xiaomi_to_rgb(self, xiaomi_color):
        intval = int(xiaomi_color)
        blue = (intval) & 255
        green = (intval >> 8) & 255
        red = (intval >> 16) & 255
        bright = (intval >> 24) & 255
        value = str(red)+","+str(green)+","+str(blue)+","+str(bright)
        return value

    def _color_rgb_to_xiaomi(self, rgb_string):
        arr = rgb_string.split(",")
        r = int(arr[0])
        g = int(arr[1])
        b = int(arr[2])
        if len(arr) > 3:
            bright = int(arr[3])
        else:
            bright = 255
        value = int('%02x%02x%02x%02x' % (bright, r, g, b), 16)
        return value

    def _get_tls_version(self,tlsString):
        switcher = {
            "tlsv1": ssl.PROTOCOL_TLSv1,
            "tlsv1.1": ssl.PROTOCOL_TLSv1_1,
            "tlsv1.2": ssl.PROTOCOL_TLSv1_2
        }
        return switcher.get(tlsString,ssl.PROTOCOL_TLSv1_2)
