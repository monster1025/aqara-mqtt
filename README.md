# Aqara-MQTT
Aqara (Xiaomi) Gateway to MQTT brodge. 
I use it for home assistant integration and it works well now (exclude Brightness+RGB value of gateway - you need to send it in xiaomi format).

You need to activate developer mode (described here: http://bbs.xiaomi.cn/t-13198850)

Bridge accept following MQTT set:
```
"home/plug/heater/status/set" -> on 
```

will turn on plug/heater and translate devices state from gateway:
```
"home/plug/heater/status" on
```

## Config

Sample config file (config.yaml):
```
mqtt:
  server: 192.168.1.2
  port: 1883
  username: username
  password: passw0rd
  prefix: home

gateway:
  password: passw0rd

sids:
  # motion
  158d0000e7c7ad:
    model: motion
    name: hall

  # temperature
  158d0001149b3c: 
    model: sensor_ht
    name: living

  # plugs
  158d00010dd98d: 
    model: plug
    name: heater

  # buttons
  158d00012d5720: 
    model: switch
    name: kitchen

  # cube
  158d00011065e3: 
    model: cube
    name: main

  # gateway
  f0b429aa1463: 
    model: gateway
    name: main
```

## Related projects
- https://github.com/lazcad/homeassistant
- https://github.com/fooxy/homeassistant-aqara/
