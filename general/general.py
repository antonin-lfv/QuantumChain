from flask import Blueprint, render_template, jsonify
import json
import os
import datetime
import networkx as nx
import plotly.graph_objects as go
import plotly
import requests
import time

BLP_general = Blueprint("BLP_general", __name__, template_folder="templates/general")

# For opening the file, retry if it fails (concurent access)
max_retries = 2  # Max number of retries
retry_delay = 1  # Delay between each retry
show_logs = False  # Show logs in the console

# Blockchain config
with open("Blockchain/config.json", "r") as f:
    CONFIG = json.load(f)

# App config
with open("Blockchain/app_config.json", "r") as f:
    APP_CONFIG = json.load(f)


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
                        miner["nb_tokens_earned"] = max(
                            (miner["nb_blocks_mined"] - 1) * CONFIG["REWARD_TOKEN"], 0
                        )
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


@BLP_general.route("/blockchains_overview")
def blockchains_overview():
    # Get other miners blockchains
    # First, get the list of connected miners with api : "/get_connected_miners"
    connected_miners = []
    try:
        r = requests.get(
            f"http://{APP_CONFIG['API_IP_FLASK_MINER']}:{APP_CONFIG['API_PORT_FLASK_MINER']}/get_connected_miners"
        )
        if r.status_code == 200:
            connected_miners = r.json()
            print(f"Connected miners : {connected_miners} in 200")
    except Exception as e:
        if show_logs:
            print(
                f"[API LOGS]: Erreur lors de la récupération des mineurs connectés: {e}"
            )

    # Now, each element of connected_miners is a dict with the following keys:
    # - "name"
    # - "ip"
    # - "port"

    # Get the blockchain of each miner using the api : "/chain"
    all_blocks = []
    for miner in connected_miners:
        try:
            r = requests.get(f"http://{miner['ip']}:{miner['port']}/chain")
            if r.status_code == 200:
                blockchain = r.json()
                data = [block for block in blockchain if block["hash"] is not None]
                all_blocks.extend(data)
        except Exception as e:
            if show_logs:
                print(
                    f"[API LOGS]: Erreur lors de la récupération de la blockchain du mineur {miner['name']}: {e}"
                )
    # Add the current block being mined from the file Blockchain/blockchain_data.json
    for _ in range(max_retries):
        try:
            with open(f"Blockchain/blockchain_data.json") as json_file:
                blockchain = json.load(json_file)
                if blockchain:
                    # Get the last block being mined
                    data = [block for block in blockchain if block["hash"] is not None]
                    all_blocks.extend(data)
            break  # Si la lecture réussit, sortez de la boucle
        except Exception as e:
            if show_logs:
                print(
                    f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                )
            time.sleep(retry_delay)

    try:
        # Créez un graphe à partir des blocs
        G = nx.DiGraph()

        for block in all_blocks:
            G.add_node(block["hash"], label=block["index"])
            G.add_edge(block["previous_hash"], block["hash"])

        # Utilisez la mise en page pydot pour obtenir une structure d'arbre
        pos = nx.drawing.nx_pydot.pydot_layout(G, prog="dot")

        # Obtenez les positions pour les nœuds et les arêtes
        node_x = []
        node_y = []
        hashes = []
        miner_names = []
        block_indexes = []
        end_dates = []
        for node in G.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            hashes.append(node)
            # From node (that is the previous hash field) get the block index and miner name
            miner_names.append(
                [block["miner"] for block in all_blocks if block["hash"] == node][0]
                if [block["miner"] for block in all_blocks if block["hash"] == node]
                else "First block"
            )
            block_indexes.append(
                [block["index"] for block in all_blocks if block["hash"] == node][0]
                if [block["index"] for block in all_blocks if block["hash"] == node]
                else "First block"
            )
            end_dates.append(
                [block["end_time"] for block in all_blocks if block["hash"] == node][0]
                if [block["end_time"] for block in all_blocks if block["hash"] == node]
                else "First block"
            )
        edge_x = []
        edge_y = []
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([-y0, -y1, None])

        # Create a color for each miner
        miner_color = []
        for name in miner_names:
            # Extract the miner id from the name
            miner_id = name.split("_")[1] if name != "First block" else 0
            # Use the hash to get a unique integer for the string
            hashed_id = hash(miner_id)
            # Then take the modulo of the number of color to fit the color range
            color = hashed_id % (len(connected_miners) + 1)
            miner_color.append(color)
        # Create figure
        node_trace = go.Scatter(
            y=node_x,
            x=[-n for n in node_y],
            mode="markers",
            hoverinfo="text",
            # Color depending on the miner, discrete colors
            marker=dict(
                showscale=False,
                colorscale="Rainbow",
                reversescale=True,
                # Color is the number of the miner
                color=[c for c in miner_color],
                size=5,
                colorbar=dict(
                    thickness=15,
                    title="Miners",
                    xanchor="left",
                    titleside="right",
                ),
                line_width=1,
            ),
            text=[
                f"Hash: {h}<br>Miner: {m}<br>Block index: {i}<br>Validation date: {v}"
                for h, m, i, v in zip(hashes, miner_names, block_indexes, end_dates)
            ],
            showlegend=False,
        )
        edge_trace = go.Scatter(
            y=edge_x,
            x=edge_y,
            line=dict(width=0.5, color="#888"),
            hoverinfo="none",
            mode="lines",
            showlegend=False,
        )
        fig = go.Figure(data=[edge_trace, node_trace])
        # Add annotation for genesis block in plotly with arrow
        fig.add_annotation(
            x=-node_y[1],
            y=node_x[1],
            xref="x",
            yref="y",
            text="Genesis block",
            showarrow=True,
            arrowhead=1,
            ax=0,
            ay=-40,
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        )
        # to json
        fig_forks_blockchain = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    except Exception as e:
        if show_logs:
            print(f"[ERROR]: Erreur lors de la création du graph: {e}")
        fig_forks_blockchain = None

    return render_template(
        "blockchains_overview.html",
        fig_forks_blockchain=fig_forks_blockchain,
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
