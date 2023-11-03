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

run mosquitto broker (only on one device)
```
/opt/homebrew/Cellar/mosquitto/2.0.15/sbin/mosquitto -c /opt/homebrew/Cellar/mosquitto/2.0.15/etc/mosquitto/mosquitto.conf
```

Lancer la blockchain
```
cd Blockchain
python3 main.py
```

Lancer l'inteface web
```
flask run
```

Pour reinitialiser la blockchain (sur un OS unix)
```
chmod i+x clean.sh
./clean.sh
```

Sinon 
- supprimer le fichier blockchain_data.json
- remplacer le contenu de miner.json par {}