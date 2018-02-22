# Aqara-MQTT
[![Build Status](https://travis-ci.org/monster1025/aqara-mqtt.svg?branch=master)](https://travis-ci.org/monster1025/aqara-mqtt)
Aqara (Xiaomi) Gateway to MQTT bridge. 
I use it for home assistant integration and it works well now.

You need to activate developer mode (described here: http://bbs.xiaomi.cn/t-13198850)

Bridge accept following MQTT set:
```
"home/plug/heater/status/set" -> on 
```

will turn on plug/heater and translate devices state from gateway:
```
"home/plug/heater/status" on
```

## Architecture
Docker image support following architectures (you must choose your architecture in docker-compose):
- armhf (raspberry pi 3, arm32v7)
- i386 (x86 pc)
- x64 (x64 pc)

## Config
Edit file config/config-sample.yaml and rename it to config/config.yaml

## Docker-Compose
Sample docker-compose.yaml file for user:
```
aqara:
  image: monster1025/aqara-mqtt:1-armhf
  container_name: aqara
  volumes:
    - "./config:/app/config"
  net: host
  restart: always
```

## Related projects
- https://github.com/lazcad/homeassistant
- https://github.com/fooxy/homeassistant-aqara/

General discussions:
- https://community.home-assistant.io/t/beta-xiaomi-gateway-integration/8213/288

## Home assistant examples:
- Gateway rgb light as home assistant bulb template
```
- platform: mqtt_template
  name: "Main Gateway"
  state_topic: "home/gateway/main/rgb"
  command_topic: "home/gateway/main/rgb/set"
  command_on_template: "{%- if red is defined and green is defined and blue is defined -%}{{ red }},{{ green }},{{ blue }}{%- else -%}255,179,0{%- endif -%},{%- if brightness is defined -%}{{ (float(brightness) / 255 * 100) | round(0) }}{%- else -%}100{%- endif -%}"
  command_off_template: "0,0,0,0"
  state_template: "{%- if value.split(',')[3]| float > 0 -%}on{%- else -%}off{%- endif -%}"  # must return `on` or `off`
  brightness_template: "{{ (float(value.split(',')[3])/100*255) | round(0) }}"
  red_template: "{{ value.split(',')[0] | int }}"
  green_template: "{{ value.split(',')[1] | int }}"
  blue_template: "{{ value.split(',')[2] | int }}"
```

- Switch automation example:
```
trigger:
    platform: mqtt
    topic: home/switch/hall/status
    payload: 'click'
action:
  service: script.hall_force_light_on
```
