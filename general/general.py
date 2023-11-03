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


# TODO : Ajouter un bouton pour stopper le minage des miners un à un pour arreter le réseau sans casser les
# fichiers json (comme ça le status des miners est sauvegardé et est toujours visible sur le dashboard et à jour)


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
    # === Get main blochain data ===
    # Liste des fichiers JSON dans le dossier
    json_files = [
        f for f in os.listdir("Blockchain/miners_blockchain") if f.endswith(".json")
    ]

    # Variables for the graph and wigets
    max_len = 0
    max_file = ""
    all_blocks = []

    # If no file, return empty data
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
            fig_forks_blockchain=None,
        )

    # Find the file with the most elements
    for json_file in json_files:
        for _ in range(max_retries):
            try:
                with open(f"Blockchain/miners_blockchain/{json_file}", "r") as f:
                    data = json.load(f)
                    if len(data) > max_len:
                        max_len = len(data)
                        max_file = json_file

                    # For the graph, only keep the blocks that have been mined
                    # remove block being mined (hash = None)
                    data = [block for block in data if block["hash"] is not None]
                    all_blocks.extend(data)

                break  # Si la lecture réussit, sortez de la boucle
            except Exception as e:
                if show_logs:
                    print(
                        f"Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                    )
                time.sleep(retry_delay)

    for _ in range(max_retries):
        try:
            # Take the 10 last elements of the file with the most elements
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

            break  # Si la lecture réussit, sortez de la boucle
        except Exception as e:
            if show_logs:
                print(
                    f"Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                )
            time.sleep(retry_delay)

    # Only keep the element with a Nonce, to keep only the mined blocks
    data_longest_blockchain = [block for block in data if block["nonce"] is not None]
    number_blocks = len(data)
    first_block_mined_date = data[0]["end_time"]
    last_block_mined_date = data[-1]["end_time"]

    # === Get miners from the file Blockchain/miners.json ===
    for _ in range(max_retries):
        try:
            with open("Blockchain/miners.json") as json_file:
                miners = json.load(json_file)
                # Get activated miners
                number_miners = len([miner for miner in miners if miner["activated"]])
            break  # Si la lecture réussit, sortez de la boucle
        except Exception as e:
            if show_logs:
                print(
                    f"Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                )
            time.sleep(retry_delay)

    # === Get config from the file Blockchain/config.json ===
    with open("Blockchain/config.json") as json_file:
        config = json.load(json_file)
        reward_per_block = config["REWARD_TOKEN"]

    # === Get all hashes and miner_name from all blochchain files to view forks ===
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

        # Create discrete color for each miner
        miner_color = []
        for i in range(len(node_x)):
            # Add the number of the miner
            # print(miner_names[i].split("Miner"))
            miner_color.append(
                int(miner_names[i].split("Miner")[1])
                if len(miner_names[i].split("Miner")) > 1
                else 0
            )
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
                size=8,
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
        "index.html",
        title="Dashboard",
        number_blocks=number_blocks,
        number_miners=number_miners,
        first_block_mined_date=first_block_mined_date,
        last_block_mined_date=last_block_mined_date,
        reward_per_block=reward_per_block,
        average_time_between_blocks=average_time_between_blocks,
        data_longest_blockchain=data_longest_blockchain[-10:],
        fig_forks_blockchain=fig_forks_blockchain,
    )


@BLP_general.route("/miners")
def miners():
    if os.path.exists("Blockchain/miners.json"):
        for _ in range(max_retries):
            try:
                # Get all miners from the file Blockchain/miners.json
                with open("Blockchain/miners.json") as json_file:
                    miners = json.load(json_file)
                break  # Si la lecture réussit, sortez de la boucle
            except Exception as e:
                if show_logs:
                    print(
                        f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                    )
                time.sleep(retry_delay)
    else:
        miners = []

    # Get, for all miners, the number of blocks in their blockchain
    # The number of mined blocks (Block.miner = miner_name)
    # The number of tokens earned by reward (multiply by the number of blocks mined)
    for miner in miners:
        if os.path.exists(
            f"Blockchain/miners_blockchain/blockchain_data_{miner['name']}.json"
        ):
            for _ in range(max_retries):
                try:
                    with open(
                        f"Blockchain/miners_blockchain/blockchain_data_{miner['name']}.json"
                    ) as json_file:
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
                        miner["nb_tokens_earned"] = (
                            miner["nb_blocks_mined"] * CONFIG["REWARD_TOKEN"]
                        )
                    break  # Si la lecture réussit, sortez de la boucle
                except Exception as e:
                    if show_logs:
                        print(
                            f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                        )
                    time.sleep(retry_delay)
        else:
            miner["nb_blocks_mined"] = 0

    return render_template("miners.html", title="Miners", miners=miners)


@BLP_general.route("/view_blockchain/<miner_name>")
def view_blockchain(miner_name):
    # WARNING: For now, the number of tokens is only the ones earned by mining blocks not the ones
    # earned by transactions

    # Get miner from the file Blockchain/miners.json
    for _ in range(max_retries):
        try:
            with open("Blockchain/miners.json") as json_file:
                miners = json.load(json_file)
                miner = [miner for miner in miners if miner["name"] == miner_name][0]
            break  # Si la lecture réussit, sortez de la boucle
        except Exception as e:
            if show_logs:
                print(
                    f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                )
            time.sleep(retry_delay)

    # Get blockchain from the file Blockchain/miners_blockchain/<miner_name>.json
    for _ in range(max_retries):
        try:
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
                # Get the number of blocks in the blockchain of the miner
                miner["nb_blocks_blockchain"] = (
                    len(blockchain) - 1
                )  # -1 for the current block being mined
                # Get the number of blocks mined by the miner
                miner["nb_blocks_mined"] = len(
                    [block for block in blockchain if block["miner"] == miner["name"]]
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

    return render_template(
        "view_blockchain.html",
        title="View Blockchain",
        miner=miner,
        miner_name=miner_name,
        miners_last_20_transactions=miners_last_20_transactions,
        last_10_blocks=last_10_blocks,
        beautify_transaction=beautify_transaction,
    )


# === API ===


@BLP_general.route("/get_miners")
def get_miners():
    for _ in range(max_retries):
        try:
            with open("Blockchain/miners.json") as json_file:
                miners = json.load(json_file)
            break  # Si la lecture réussit, sortez de la boucle
        except Exception as e:
            if show_logs:
                print(
                    f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                )
            time.sleep(retry_delay)

    # Get the number of blocks in in the blockchain of each miner
    for miner in miners:
        if os.path.exists(
            f"Blockchain/miners_blockchain/blockchain_data_{miner['name']}.json"
        ):
            for _ in range(max_retries):
                try:
                    with open(
                        f"Blockchain/miners_blockchain/blockchain_data_{miner['name']}.json"
                    ) as json_file:
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
        else:
            miner["nb_blocks_mined"] = 0

    return jsonify({"miners": miners})


@BLP_general.route("/change_miner_honesty/<miner_name>")
def change_miner_honesty(miner_name):
    # Get miner from the file Blockchain/miners.json
    for _ in range(max_retries):
        try:
            with open("Blockchain/miners.json") as json_file:
                miners = json.load(json_file)
                miner = [miner for miner in miners if miner["name"] == miner_name][0]
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
            with open("Blockchain/miners.json", "w") as json_file:
                json.dump(miners, json_file, indent=4)
            break  # Si la lecture réussit, sortez de la boucle
        except Exception as e:
            if show_logs:
                print(
                    f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                )
            time.sleep(retry_delay)
    return jsonify({"miner": miner})


@BLP_general.route("/change_miner_activation/<miner_name>")
def change_miner_activation(miner_name):
    # Get miner from the file Blockchain/miners.json
    for _ in range(max_retries):
        try:
            with open("Blockchain/miners.json") as json_file:
                miners = json.load(json_file)
                miner = [miner for miner in miners if miner["name"] == miner_name][0]
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
            with open("Blockchain/miners.json", "w") as json_file:
                json.dump(miners, json_file, indent=4)
            break  # Si la lecture réussit, sortez de la boucle
        except Exception as e:
            if show_logs:
                print(
                    f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                )
            time.sleep(retry_delay)
    return jsonify({"miner": miner})
