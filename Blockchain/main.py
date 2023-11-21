import numpy as np

from miner import Miner
import threading
import json
import os


def create_and_start_miners(num_miners, focused_dishonesty=False):
    miners = []
    threads = []

    if focused_dishonesty:
        # test the integrity of the config for the focused dishonesty
        with open("config.json", "r") as f:
            CONFIG = json.load(f)

            # test if the target miner to avoid is in the list of miners to avoid
            assert (
                CONFIG["TARGET_MINER_ID_TO_AVOID"] not in CONFIG["MINERS_IDS_AVOIDING"]
            ), (
                f"The target miner id to avoid {CONFIG['TARGET_MINER_ID_TO_AVOID']} is in the list of miners to avoid. "
                f"Check the config.json file."
            )

            # test if the ids are in the range of the number of miners
            assert 0 < CONFIG["TARGET_MINER_ID_TO_AVOID"] <= num_miners, (
                f"The target miner id to avoid '{CONFIG['TARGET_MINER_ID_TO_AVOID']}' is not in the range of "
                f"the number of miners : ]0, {num_miners}]. "
                f"Check the config.json file."
            )

            for miner_id in CONFIG["MINERS_IDS_AVOIDING"]:
                assert 0 < miner_id <= num_miners, (
                    f"Index '{miner_id}' in MINERS_IDS_AVOIDING is not in the range of the number of miners : "
                    f"]0, {num_miners}]. "
                    f"Check the config.json file."
                )

    # Create the directory Blockchain/miners_blockchain if it doesn't exist
    if not os.path.isdir("miners_blockchain"):
        os.mkdir("miners_blockchain")

    for i in range(num_miners):
        print(f"Creating miner {i+1}")
        miner_name = f"Miner{i+1}"

        if focused_dishonesty and i + 1 in CONFIG["MINERS_IDS_AVOIDING"]:
            # Adding a focused dishonesty to the miner
            TARGET_MINER_ID_TO_AVOID = CONFIG["TARGET_MINER_ID_TO_AVOID"]
            miner = Miner(miner_name, num_miners, TARGET_MINER_ID_TO_AVOID)
        else:
            miner = Miner(miner_name, num_miners)

        miners.append(miner)

        # Start the MQTT client for each miner
        miner.start()

    print("----------------------------------------------")

    for miner in miners:
        # Start the mining thread for each miner after the MQTT client is started
        # and after all the miners are created
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
            "activated": True,
        }
        miners_data.append(new_miner)

    with open("miners.json", "w") as f:
        json.dump(miners_data, f, indent=4)

    return miners, threads


if __name__ == "__main__":
    # num_miners = int(input("Enter the number of miners: "))  # Or set this number some other way
    num_miners = 10
    focused_dishonesty = True
    print(f"[IMPORTANT] The number of miners is set to {num_miners}.")
    if focused_dishonesty:
        print("[IMPORTANT] THE FOCUSED DISHONESTY IS ACTIVATED.")

    print("----------------------------------------------")

    miners, threads = create_and_start_miners(num_miners, focused_dishonesty)
