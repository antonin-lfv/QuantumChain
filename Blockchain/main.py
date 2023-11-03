import numpy as np

from miner import Miner
import threading
import json


def generate_random_string(length):
    """Generate a random string of fixed length"""
    valid_char = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(np.random.choice(list(valid_char), length))


def create_and_start_miner():
    print(f"Creating miner")
    # The name of the miner is "Miner" + a random string of 10 characters
    miner_name = f"Miner_{generate_random_string(10)}"
    miner = Miner(miner_name)

    # Start the MQTT client
    miner.start()

    # Start the mining thread
    thread = threading.Thread(target=miner.mine_block)
    thread.start()

    # miner.json looks like this:
    # {
    #     "name": "Miner_aidj87Yhq4",
    #     "activated": true,
    #     "honesty": true
    # }

    # Get miner data
    with open("miner.json", "r") as f:
        miner_data = json.load(f)

    # Activate miner
    if not miner_data["activated"]:
        miner_data["activated"] = True
        miner.activated = True

    # Set miner honesty
    if not miner_data["honesty"]:
        miner_data["honesty"] = True
        miner.honesty = True

    # Save the miner data
    with open("miners.json", "w") as f:
        json.dump(miner_data, f, indent=4)

    return miners, threads


if __name__ == "__main__":
    # num_miners = int(input("Enter the number of miners: "))  # Or set this number some other way

    miners, threads = create_and_start_miner()
