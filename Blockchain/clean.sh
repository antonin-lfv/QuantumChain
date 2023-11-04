# Set miners.json to empty array if it exists
if [ -f "miners.json" ]; then
    echo "[]" > miners.json
fi

# Empty the miners_blockchain folder if it exists
if [ -d "miners_blockchain" ]; then
    rm -rf miners_blockchain
    mkdir miners_blockchain
fi