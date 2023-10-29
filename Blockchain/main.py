from miner import Miner
import threading
import json


# TODO : verify the verification of a block because for example, miner 3 was stuck at block 25 but mined the block 35


def create_and_start_miners(num_miners, num_dishonest_miners):
    miners = []
    threads = []

    for i in range(num_miners):
        print(f"Creating miner {i+1}")
        miner_name = f"Miner{i+1}"
        miner = Miner(miner_name, num_miners)
        miners.append(miner)

        # Start the MQTT client for each miner
        miner.start()

        # Start the mining thread for each miner
        thread = threading.Thread(target=miner.mine_block)
        threads.append(thread)
        thread.start()

    # Set activated to "yes" in miners.json for the num_miners first miners
    with open("miners.json", "r") as f:
        miners_data = json.load(f)

    # Activate or deactivate miners
    for i in range(len(miners_data)):
        if i < num_miners:
            miners_data[i]["activated"] = True
        else:
            miners_data[i]["activated"] = False

    # Add new miners if needed
    while len(miners_data) < num_miners:
        new_miner = {
            "name": f"Miner{len(miners_data) + 1}",
            "tokens": 0.0,
            "nb_blocks_mined": 0,
            "activated": True,
        }
        miners_data.append(new_miner)

    with open("miners.json", "w") as f:
        json.dump(miners_data, f, indent=4)

    return miners, threads


if __name__ == "__main__":
    # num_miners = int(input("Enter the number of miners: "))  # Or set this number some other way
    num_miners = 5
    num_dishonest_miners = 1
    assert num_dishonest_miners < num_miners

    miners, threads = create_and_start_miners(num_miners, num_dishonest_miners)
