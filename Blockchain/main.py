import os.path

import numpy as np
from api import run_api
from miner import Miner
import threading
import json
import time
from stopControl import StopControl

stop_control = StopControl()


# get app config from app_config.json
with open("app_config.json") as json_file:
    APP_CONFIG = json.load(json_file)


def generate_random_string(length):
    """Generate a random string of fixed length"""
    valid_char = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    return "".join(np.random.choice(list(valid_char), length))


def create_and_start_miner(mqtt_broker_ip):
    global stop_control

    # Get miner data
    with open("miner.json", "r") as f:
        # if empty, miner_data = {}
        if os.path.getsize("miner.json") == 0:
            miner_data = {}
        else:
            miner_data = json.load(f)

    if not miner_data:
        print(f"Creating miner")
        # The name of the miner is "Miner" + a random string of 10 characters
        miner_name = f"Miner_{generate_random_string(10)}"
        miner = Miner(miner_name, mqtt_broker_ip)
        miner_data["name"] = miner_name
        miner_data["activated"] = True
        miner_data["honesty"] = True
    else:
        print(f"Loading miner")
        miner = Miner(miner_data["name"], mqtt_broker_ip)

    # Start the MQTT client
    miner.start()

    # Start the mining thread
    mining_thread = threading.Thread(
        target=miner.mine_block, args=(stop_control,), daemon=True
    )
    mining_thread.start()

    # Start the miner API thread
    api_thread = threading.Thread(target=run_api, args=(miner,), daemon=True)
    api_thread.start()

    # miner.json looks like this:
    # {
    #     "name": "Miner_aidj87Yhq4",
    #     "activated": true,
    #     "honesty": true
    # }

    # Activate miner
    if "activated" in miner_data and not miner_data["activated"]:
        miner_data["activated"] = True
        miner.activated = True

    # Set miner honesty
    if "honesty" in miner_data and not miner_data["honesty"]:
        miner_data["honesty"] = True
        miner.honesty = True

    # Save the miner data
    with open("miner.json", "w") as f:
        json.dump(miner_data, f, indent=4)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        miner.stop()
        stop_control.request_stop()
        mining_thread.join()
        print("[INFO] Miner stopped")

    return


if __name__ == "__main__":
    mqtt_broker_ip = APP_CONFIG[
        "MQTT_BROKER_IP"
    ]  # APP_CONFIG["MQTT_BROKER_IP"] or "localhost"

    create_and_start_miner(mqtt_broker_ip)
