from flask import Blueprint, render_template, jsonify
import json
import os
import datetime

BLP_general = Blueprint("BLP_general", __name__, template_folder="templates/general")


def beautify_transaction(transaction):
    """
    Beautify a transaction

    From:
    {
        "sender": "Blockchain",
        "recipient": "Miner1",
        "amount": 5.8,
        "timestamp": "2023-10-27 21:26:43"
    }
    To:
    Blockchain -> Miner1: 5.8 (2023-10-27 21:26:43)
    """
    transaction = (
        f"{transaction['sender']} -> {transaction['recipient']}: {transaction['amount']} ("
        f"{transaction['timestamp']})"
    )
    return transaction


@BLP_general.route("/")
def home():
    """# Get blockchain from the file Blockchain/num_blocks.json
    with open('Blockchain/blockchain_data.json') as json_file:
        data = json.load(json_file)
        number_blocks = len(data)
        if number_blocks>0:
            first_block_mined_date = data[0]['end_time']
            last_block_mined_date = data[-1]['end_time']
        else:
            first_block_mined_date = None
            last_block_mined_date = None"""

    # Liste des fichiers JSON dans le dossier
    json_files = [
        f for f in os.listdir("Blockchain/miners_blockchain") if f.endswith(".json")
    ]

    max_len = 0
    max_file = ""

    if len(json_files) == 0:
        return render_template(
            "index.html",
            title="Dashboard",
            number_blocks=0,
            number_miners=0,
            first_block_mined_date=None,
            last_block_mined_date=None,
            reward_per_block=0,
            average_time_between_blocks=0,
            data=[],
        )

    # Trouver le fichier avec le plus grand nombre d'éléments
    for json_file in json_files:
        with open(f"Blockchain/miners_blockchain/{json_file}", "r") as f:
            data = json.load(f)
            if len(data) > max_len:
                max_len = len(data)
                max_file = json_file

    # Charger les 10 derniers éléments du fichier ayant le plus grand nombre d'éléments
    with open(f"Blockchain/miners_blockchain/{max_file}", "r") as f:
        data = json.load(f)
        # Get the avergae time between two blocks, convert date to timestamp (format "2023-10-27 17:43:31")
        first_date = datetime.datetime.strptime(
            data[0]["end_time"], "%Y-%m-%d %H:%M:%S"
        ).timestamp()
        last_date = datetime.datetime.strptime(
            data[-2]["end_time"], "%Y-%m-%d %H:%M:%S"
        ).timestamp()
        average_time_between_blocks = (last_date - first_date) / (len(data) - 1)
        # To minutes and seconds
        average_time_between_blocks = str(
            datetime.timedelta(seconds=average_time_between_blocks)
        ).split(".")[0]

    # Only keep the element with a Nonce, to keep only the mined blocks
    data = [block for block in data if block["nonce"] is not None]
    number_blocks = len(data)
    first_block_mined_date = data[0]["end_time"]
    last_block_mined_date = data[-1]["end_time"]

    # Get miners from the file Blockchain/miners.json
    with open("Blockchain/miners.json") as json_file:
        miners = json.load(json_file)
        # Get activated miners
        number_miners = len([miner for miner in miners if miner["activated"]])

    # Get config from the file Blockchain/config.json
    with open("Blockchain/config.json") as json_file:
        config = json.load(json_file)
        reward_per_block = config["REWARD_TOKEN"]

    return render_template(
        "index.html",
        title="Dashboard",
        number_blocks=number_blocks,
        number_miners=number_miners,
        first_block_mined_date=first_block_mined_date,
        last_block_mined_date=last_block_mined_date,
        reward_per_block=reward_per_block,
        average_time_between_blocks=average_time_between_blocks,
        data=data[-10:],
    )


@BLP_general.route("/miners")
def miners():
    if os.path.exists("Blockchain/miners.json"):
        # Get all miners from the file Blockchain/miners.json
        with open("Blockchain/miners.json") as json_file:
            miners = json.load(json_file)
    else:
        miners = []

    return render_template("miners.html", title="Miners", miners=miners)


@BLP_general.route("/view_blockchain/<miner_name>")
def view_blockchain(miner_name):
    # Get miner from the file Blockchain/miners.json
    with open("Blockchain/miners.json") as json_file:
        miners = json.load(json_file)
        miner = [miner for miner in miners if miner["name"] == miner_name][0]

    # Get blockchain from the file Blockchain/miners_blockchain/<miner_name>.json
    with open(
        f"Blockchain/miners_blockchain/blockchain_data_{miner_name}.json"
    ) as json_file:
        blockchain = json.load(json_file)
        # Get the last 20 transactions where the miner is the sender or the receiver
        miners_last_20_transactions = []
        for block in blockchain:
            if block["nonce"] is None:
                # If the block is not mined,
                continue
            for transaction in block["transactions"]:
                if (
                    transaction["sender"] == miner_name
                    or transaction["recipient"] == miner_name
                ):
                    miners_last_20_transactions.append(transaction)

                if len(miners_last_20_transactions) == 20:
                    break
            if len(miners_last_20_transactions) == 20:
                break
        # get 10 last blocks (the last one is the one being mined)
        last_10_blocks = blockchain[-11:-1][::-1]

    return render_template(
        "view_blockchain.html",
        title="View Blockchain",
        miner=miner,
        miner_name=miner_name,
        miners_last_20_transactions=miners_last_20_transactions,
        last_10_blocks=last_10_blocks,
        beautify_transaction=beautify_transaction,
    )


@BLP_general.route("/get_miners")
def get_miners():
    with open("Blockchain/miners.json") as json_file:
        miners = json.load(json_file)

    return jsonify({"miners": miners})
