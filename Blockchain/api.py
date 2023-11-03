from flask import Flask, jsonify
import json
from block import Block

app = Flask(__name__)

# Vous passerez l'instance de Miner lors du démarrage de l'API
miner_instance = None

# Get app config
with open("app_config.json") as json_file:
    APP_CONFIG = json.load(json_file)


@app.route("/chain", methods=["GET"])
def get_chain():
    chain_data = [b.to_dict() for b in miner_instance.blockchain.chain]
    return jsonify(chain_data), 200


@app.route("/chain/length", methods=["GET"])
def get_chain_length():
    return jsonify(length=len(miner_instance.blockchain.chain)), 200


@app.route("/get_connected_miners", methods=["GET"])
def get_connected_miners():
    print(miner_instance.other_miners)
    return jsonify(miner_instance.other_miners), 200


# D'autres routes peuvent être ajoutées ici


def run_api(miner):
    global miner_instance
    miner_instance = miner
    app.run(host="0.0.0.0", port=APP_CONFIG["API_PORT_FLASK_MINER"])
