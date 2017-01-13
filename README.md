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
Edit file config/config-sample.yaml and rename it to config/config.yaml

## Docker-Compose
Sample docker-compose.yaml file for user:
```
aqara:
  image: monster1025/aqara-mqtt
  container_name: aqara
  volumes:
    - "./config:/app/config"
  net: host
  restart: always
```

## Related projects
- https://github.com/lazcad/homeassistant
- https://github.com/fooxy/homeassistant-aqara/
