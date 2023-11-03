# Online app

## Installation

git clone
git checkout online_app

depuis le dossier Blockchain créer app_config.json en mettant l'ip du broker MQTT
{
  "MQTT_BROKER_IP": "ip_broker"
}

Installer les dépendances
```
pip install -r requirements.txt
```


run mosquitto broker
```
/opt/homebrew/Cellar/mosquitto/2.0.15/sbin/mosquitto -c /opt/homebrew/Cellar/mosquitto/2.0.15/etc/mosquitto/mosquitto.conf
```
