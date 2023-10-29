import json
import networkx as nx
import plotly.graph_objects as go
from plotly.offline import plot
import os

# Charger les données
all_blocks = []
json_files = [
    f for f in os.listdir("Blockchain/miners_blockchain") if f.endswith(".json")
]

for json_file in json_files:
    with open(f"Blockchain/miners_blockchain/{json_file}", "r") as f:
        data = json.load(f)
        # remove block being mined (hash = None)
        data = [block for block in data if block["hash"] is not None]
        all_blocks.extend(data)

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

edge_x = []
edge_y = []
for edge in G.edges():
    x0, y0 = pos[edge[0]]
    x1, y1 = pos[edge[1]]
    edge_x.extend([x0, x1, None])
    edge_y.extend([y0, y1, None])

# Créez le tracé avec Plotly
node_trace = go.Scatter(
    x=node_x,
    y=node_y,
    mode="markers",
    hoverinfo="text",
    text=[
        f"Hash: {h}<br>Miner: {m}<br>Block index: {i}"
        for h, m, i in zip(hashes, miner_names, block_indexes)
    ],
    showlegend=False,
)
edge_trace = go.Scatter(
    x=edge_x,
    y=edge_y,
    line=dict(width=0.5, color="#888"),
    hoverinfo="none",
    mode="lines",
    showlegend=False,
)

fig = go.Figure(data=[edge_trace, node_trace])
fig.update_layout(
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(b=20, l=5, r=5, t=40),
    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
)
plot(fig)
