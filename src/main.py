import logging
import time
import threading
import os
import json

#mine
import mqtt
import yamlparser
from xiaomihub import XiaomiHub

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)

def process_gateway_messages(gateway, client):
	while True:
		try: 
			packet = gateway._queue.get()
			_LOGGER.debug("data from queuee: " + format(packet))

			sid = packet.get("sid", None)
			model = packet.get("model", "")
			data = packet.get("data", "")

			if (sid != None and data != ""):
				data_decoded = json.loads(data)
				client.publish(model, sid, data_decoded)
			gateway._queue.task_done()
		except Exception as e:
			_LOGGER.error('Error while sending from gateway to mqtt: ', str(e))

def process_mqtt_messages(gateway, client):
	while True:
		try: 
			data = client._queue.get()
			_LOGGER.debug("data from mqtt: " + format(data))

			sid = data.get("sid", None)
			param = data.get("param", None)
			value = data.get("value", None)

			resp = gateway.write_to_hub(sid, param, value)
			client._queue.task_done()
		except Exception as e:
			_LOGGER.error('Error while sending from mqtt to gateway: ', str(e))

if __name__ == "__main__":
	_LOGGER.info("Loading config file...")
	config=yamlparser.load_yaml('config/config.yaml')
	gateway_pass = yamlparser.get_gateway_password(config)

	_LOGGER.info("Init mqtt client.")
	client = mqtt.Mqtt(config)
	client.connect()
	#only this devices can be controlled from MQTT
	client.subscribe("gateway", "+", "rgb", "set")
	client.subscribe("plug", "+", "status", "set")

	gateway = XiaomiHub(gateway_pass)
	t1 = threading.Thread(target=process_gateway_messages, args=[gateway, client])
	t1.daemon = True
	t1.start()

	t2 = threading.Thread(target=process_mqtt_messages, args=[gateway, client])
	t2.daemon = True
	t2.start()

	while True:
		time.sleep(10)
