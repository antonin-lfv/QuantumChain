# Online app

## Installation

git clone
git checkout online_app

depuis le dossier Blockchain créer app_config.json en mettant l'ip du broker MQTT, l'ip de l'API (votre IP) et le port de l'API (on prendra 5101)
```
{
  "MQTT_BROKER_IP": "ip_broker"
  "API_IP_FLASK_MINER": "ip_api",
  "API_PORT_FLASK_MINER": "port_api"
}

Installer les dépendances
```
pip install -r requirements.txt
```

Sur linux il faudra possiblement installer graphviz avec apt-get
```
sudo apt-get install graphviz
```

run mosquitto broker (only on one device)
```
brew services start mosquitto
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
chmod u+x clean.sh
./clean.sh
```

Sinon 
- supprimer le fichier blockchain_data.json
- remplacer le contenu de miner.json par {}


Pour redémarrer mosquitto broker (pour vider les topics si besoin)
```
brew services restart mosquitto
```
