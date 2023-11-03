from blockchain import Blockchain
import random
from datetime import datetime
from block import Block
import json
import paho.mqtt.client as mqtt
import time
import threading

# Config for blockchain
with open("config.json", "r") as f:
    CONFIG = json.load(f)

# Config for online miner
with open("app_config.json", "r") as f:
    APP_CONFIG = json.load(f)

# For opening the file, retry if it fails (concurent access)
max_retries = 5  # Max number of retries
retry_delay = 2  # Delay between each retry
show_logs = False  # Show logs in the console


class Miner:
    def __init__(self, miner, mqtt_broker_ip):
        self.blockchain = Blockchain(miner)
        self.miner_name = miner  # Name of the miner
        self.activated = True  # If the miner is activated or not
        self.honesty = True  # If the miner is honest or not
        self.other_miners = []  # List of other miners

        self.discovery_thread = (
            None  # Thread that will send a discovery message periodically
        )

        # MQTT client to communicate with the other miners
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect(
            host=mqtt_broker_ip, port=1883, keepalive=60
        )  # Connect to the broker

        # Notify the other miners that this miner is online
        self.client.publish(
            f"blockchain/discovery/{self.miner_name}",
            json.dumps(
                {
                    "name": self.miner_name,
                    "ip": APP_CONFIG["API_IP_FLASK_MINER"],
                    "port": APP_CONFIG["API_PORT_FLASK_MINER"],
                }
            ),
            retain=True,
        )

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        self.client.subscribe("blockchain/blocks")  # Abonne au topic des blocks
        self.client.subscribe(
            "blockchain/discovery/+"
        )  # Abonne au topic de découverte des autres mineurs

    def on_message(self, client, userdata, msg):
        """
        Callback function when a message is received on the topic "blockchain/blocks".
        The message is a block in JSON format.

        After receiving a block, the miner validates it and adds it to its blockchain depending on the honesty.
        """
        if msg.topic.startswith("blockchain/blocks"):
            # === Receive a block ===
            block_dict = json.loads(msg.payload.decode())
            # If it's the block of himself, skip to the next iteration
            if block_dict["miner"] == self.miner_name:
                return

            # Update activated and honesty
            self.update_activated_honesty()

            if not self.activated:
                # The miner is not activated, he will not validate the block
                return

            if not self.honesty:
                # The miner is not honest, he will not validate the block
                return

            # Create the block object
            received_block = Block.from_dict(block_dict)
            # Validate the block
            is_valid = self.blockchain.validate_and_add_block(received_block)
            if is_valid:
                # The block is valid, stop mining the current block for this miner
                # print(f"Block {received_block.index} mined by another miner, stop mining")
                print(
                    f"[INFO]: Block {received_block.index} of {received_block.miner} received by {self.miner_name} is valid, "
                    f"adding it to the blockchain"
                )
                self.blockchain.stop_mining_event.set()
            else:
                # The block is invalid, continue mining the current block for this miner
                # print(f"Block {received_block.index} mined by another miner is invalid")
                print(
                    f"[INFO]: Block {received_block.index} of {received_block.miner} received by {self.miner_name} is invalid, "
                    f"continue mining the current block"
                )

            # Consensus : if the blockchain of the miner (honest) is 5 blocks behind the longest blockchain,
            # he should start mining on the longest blockchain
            if self.honesty:
                self.blockchain.apply_consensus(self.other_miners)

        elif msg.topic.startswith("blockchain/discovery/"):
            # === Discover a new miner ===
            # A new miner is discovered, add it to the list of other miners
            miner_name = msg.topic.split("/")[-1]
            if miner_name != self.miner_name:
                # Ensure that the miner is not himself after a reconnection
                miner_info = json.loads(msg.payload.decode())
                if not miner_info:
                    # If the miner_info is empty, the miner is offline
                    # Remove the miner from the list of other miners thanks to his name
                    number_of_miners_before = len(self.other_miners)
                    self.other_miners = [
                        miner
                        for miner in self.other_miners
                        if miner["name"] != miner_name
                    ]
                    if len(self.other_miners) < number_of_miners_before:
                        print(f"[INFO]: Miner {miner_name} is offline")
                elif miner_info not in self.other_miners:
                    self.other_miners.append(miner_info)
                    print(f"[INFO]: New miner discovered: {miner_name}")

    def start(self):
        self.client.loop_start()
        # Start the thread that will send a discovery message periodically
        self.publish_discovery_message()  # Appeler une fois au début
        self.discovery_thread = threading.Thread(
            target=self.publish_discovery_periodically
        )
        self.discovery_thread.daemon = (
            True  # Ceci assure que le thread se termine avec le programme
        )
        self.discovery_thread.start()

    def publish_discovery_periodically(self):
        while True:
            self.publish_discovery_message()
            time.sleep(30)  # Wait 30 seconds before sending another discovery message

    def publish_discovery_message(self):
        # Verify if the miner is still activated
        if self.activated:
            # Miner is still activated, publish a message with his info
            discovery_info = {
                "name": self.miner_name,
                "ip": APP_CONFIG["API_IP_FLASK_MINER"],
                "port": APP_CONFIG["API_PORT_FLASK_MINER"],
            }
        else:
            # Miner is not activated, publish an empty message
            discovery_info = None

        # Publish the discovery message
        self.client.publish(
            f"blockchain/discovery/{self.miner_name}",
            json.dumps(discovery_info),
            retain=True,  # To ensure that the message is received by the other miners
        )

    def mine_block(self):
        while True:
            last_block_data = (
                self.blockchain.get_current_block()
            )  # Get the last block being mined
            last_block = Block.from_dict(
                last_block_data.to_dict()
            )  # Create a copy of the last block
            if last_block.miner is not None:
                continue  # skip to the next iteration

            self.blockchain.stop_mining_event.clear()

            nonce = random.randint(0, 10000000000)
            while not self.blockchain.stop_mining_event.is_set():
                if self.activated:
                    last_block.nonce = nonce
                    calculated_hash = last_block.calculate_hash()

                    if calculated_hash.startswith(CONFIG["STARTWITH_HASH"]):
                        # print(f"Block : {last_block.to_dict()} with hash {calculated_hash}")

                        last_block.hash_ = calculated_hash
                        last_block.end_time = datetime.now()
                        last_block.miner = self.miner_name

                        if self.blockchain.finish_block(last_block, self.miner_name):
                            # The block mined is valid, publish it to the other miners

                            # Send the block to the other miners
                            self.blockchain.publish_block(last_block, self.client)

                            # Check if the miner is still activated
                            self.update_activated_honesty()

                        break  # break this inner loop, not the outer one
                    else:
                        nonce += 1
                else:
                    # Wait until the miner is activated
                    self.update_activated_honesty()

    def update_activated_honesty(self) -> None:
        """
        Check if the miner is still activated by reading the file miner.json
        or if the miner is still honest by reading the file miner.json
        """
        for _ in range(max_retries):
            try:
                with open("miner.json") as json_file:
                    miner = json.load(json_file)  # list of miners (dict)
                    if miner["name"] == self.miner_name:
                        self.activated = miner["activated"]
                        self.honesty = miner["honesty"]
                        # Publish an empty discovery message
                        self.publish_discovery_message()
                break  # Si la lecture réussit, sortez de la boucle
            except Exception as e:
                if show_logs:
                    print(
                        f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. Retente dans {retry_delay} secondes..."
                    )
                time.sleep(retry_delay)
