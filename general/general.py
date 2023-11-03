from flask import Blueprint, render_template, jsonify
import json
import os
import datetime
import networkx as nx
import plotly.graph_objects as go
import plotly
import time

BLP_general = Blueprint("BLP_general", __name__, template_folder="templates/general")

# For opening the file, retry if it fails (concurent access)
max_retries = 5  # Max number of retries
retry_delay = 2  # Delay between each retry
show_logs = False  # Show logs in the console

with open("Blockchain/config.json", "r") as f:
    CONFIG = json.load(f)


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
    Blockchain -> Miner1: 5.8 Tokens (2023-10-27 21:26:43)
    """
    transaction = (
        f"{transaction['sender']} -> {transaction['recipient']}: {transaction['amount']} Tokens ("
        f"{transaction['timestamp']})"
    )
    return transaction


@BLP_general.route("/")
def home():
    # Get miner from the file Blockchain/miner.json
    miner = None
    if (
        os.path.exists("Blockchain/miner.json")
        and os.path.getsize("Blockchain/miner.json") > 0
    ):
        for _ in range(max_retries):
            try:
                with open("Blockchain/miner.json") as json_file:
                    miner = json.load(json_file)
                    if not miner:
                        return render_template(
                            "index.html",
                            miner=None,
                            miner_name=None,
                            miners_last_20_transactions=None,
                            last_10_blocks=None,
                            beautify_transaction=beautify_transaction,
                        )
                break  # Si la lecture réussit, sortez de la boucle
            except Exception as e:
                if show_logs:
                    print(
                        f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                    )
                time.sleep(retry_delay)
    else:
        return render_template(
            "index.html",
            miner=None,
            miner_name=None,
            miners_last_20_transactions=None,
            last_10_blocks=None,
            beautify_transaction=beautify_transaction,
        )

    # Get blockchain from the file Blockchain/blockchain_data.json
    miners_last_20_transactions = []
    last_10_blocks = []
    if (
        os.path.exists(f"Blockchain/blockchain_data.json")
        or os.path.getsize("Blockchain/blockchain_data.json") > 0
    ):
        for _ in range(max_retries):
            try:
                with open(f"Blockchain/blockchain_data.json") as json_file:
                    blockchain = json.load(json_file)
                    if blockchain:
                        # Get the last 20 transactions where the miner is the sender or the receiver
                        for block in blockchain:
                            if block["nonce"] is None:
                                # If the block is not mined,
                                continue
                            for transaction in block["transactions"]:
                                if (
                                    transaction["sender"] == miner["name"]
                                    or transaction["recipient"] == miner["name"]
                                ):
                                    miners_last_20_transactions.append(transaction)

                                if len(miners_last_20_transactions) == 20:
                                    break
                            if len(miners_last_20_transactions) == 20:
                                break
                        # get 10 last blocks (the last one is the one being mined)
                        last_10_blocks = blockchain[-11:-1][::-1]
                        # Get the number of blocks in the blockchain
                        miner["nb_blocks_blockchain"] = (
                            len(blockchain) - 1
                        )  # -1 for the current block being mined
                        # Get the number of blocks mined by the miner
                        miner["nb_blocks_mined"] = len(
                            [
                                block
                                for block in blockchain
                                if block["miner"] == miner["name"]
                            ]
                        )
                        # Get the number of tokens earned by the miner
                        miner["nb_tokens_earned"] = (
                            miner["nb_blocks_mined"] - 1
                        ) * CONFIG["REWARD_TOKEN"]
                break  # Si la lecture réussit, sortez de la boucle
            except Exception as e:
                if show_logs:
                    print(
                        f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                    )
                time.sleep(retry_delay)

    return render_template(
        "index.html",
        miner=miner,
        miner_name=miner["name"],
        miners_last_20_transactions=miners_last_20_transactions,
        last_10_blocks=last_10_blocks,
        beautify_transaction=beautify_transaction,
    )


# === API ===


@BLP_general.route("/get_miner")
def get_miner():
    for _ in range(max_retries):
        try:
            with open("miner.json") as json_file:
                miner = json.load(json_file)
            break  # Si la lecture réussit, sortez de la boucle
        except Exception as e:
            if show_logs:
                print(
                    f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                )
            time.sleep(retry_delay)

    # Get the number of blocks in the blockchain
    if os.path.exists(f"Blockchain/blockchain_data.json"):
        for _ in range(max_retries):
            try:
                with open(f"Blockchain/blockchain_data.json") as json_file:
                    blockchain = json.load(json_file)
                    miner["nb_blocks_blockchain"] = (
                        len(blockchain) - 1
                    )  # -1 for the current block being mined
                    # Get the number of blocks mined by the miner
                    miner["nb_blocks_mined"] = len(
                        [
                            block
                            for block in blockchain
                            if block["miner"] == miner["name"]
                        ]
                    )
                    # Get the number of tokens earned by the miner
                    miner["nb_tokens_earned"] = (miner["nb_blocks_mined"] - 1) * CONFIG[
                        "REWARD_TOKEN"
                    ]
                break  # Si la lecture réussit, sortez de la boucle
            except Exception as e:
                if show_logs:
                    print(
                        f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                    )
                time.sleep(retry_delay)
    else:
        miner["nb_blocks_mined"] = 0

    return jsonify({"miner": miner})


@BLP_general.route("/change_miner_honesty")
def change_miner_honesty():
    # Get miner from the file Blockchain/miner.json
    for _ in range(max_retries):
        try:
            with open("Blockchain/miner.json") as json_file:
                miner = json.load(json_file)
            break  # Si la lecture réussit, sortez de la boucle
        except Exception as e:
            if show_logs:
                print(
                    f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                )
            time.sleep(retry_delay)

    # Change honesty
    miner["honesty"] = not miner["honesty"]

    # Save in the file
    for _ in range(max_retries):
        try:
            with open("Blockchain/miner.json", "w") as json_file:
                json.dump(miner, json_file, indent=4)
            break  # Si la lecture réussit, sortez de la boucle
        except Exception as e:
            if show_logs:
                print(
                    f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                )
            time.sleep(retry_delay)
    return jsonify({"miner": miner})


@BLP_general.route("/change_miner_activation")
def change_miner_activation():
    # Get miner from the file Blockchain/miner.json
    for _ in range(max_retries):
        try:
            with open("Blockchain/miner.json") as json_file:
                miner = json.load(json_file)
            break  # Si la lecture réussit, sortez de la boucle
        except Exception as e:
            if show_logs:
                print(
                    f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                )
            time.sleep(retry_delay)

    # Change activation
    miner["activated"] = not miner["activated"]

    # Save in the file
    for _ in range(max_retries):
        try:
            with open("Blockchain/miner.json", "w") as json_file:
                json.dump(miner, json_file, indent=4)
            break  # Si la lecture réussit, sortez de la boucle
        except Exception as e:
            if show_logs:
                print(
                    f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                )
            time.sleep(retry_delay)
    return jsonify({"miner": miner})
