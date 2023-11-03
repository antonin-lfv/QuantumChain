# Clean the simulation to restart from scratch
# Delete blockchain_data.json if it exists

if [ -f blockchain_data.json ]; then
    rm blockchain_data.json
fi

# Set miner.json to {} if it exists

if [ -f miner.json ]; then
    echo "{}" > miner.json
fi
