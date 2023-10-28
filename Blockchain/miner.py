from blockchain import Blockchain
import random
from datetime import datetime
from block import Block

# Get config from config.json
import json
import paho.mqtt.client as mqtt

with open("config.json", "r") as f:
    CONFIG = json.load(f)


class Miner:
    def __init__(self, miner, num_miners):
        self.blockchain = Blockchain(miner)
        self.miner_name = miner  # Name of the miner
        self.num_miners = (
            num_miners  # Number of miners in the network (for generating transactions)
        )
        # MQTT client to publish and receive blocks
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        self.client.connect("localhost", 1883, 60)  # Connecte au broker sur localhost

    def on_connect(self, client, userdata, flags, rc):
        print(f"Connected with result code {rc}")
        self.client.subscribe("blockchain/blocks")  # Abonne au topic

    def on_message(self, client, userdata, msg):
        """
        Callback function when a message is received on the topic "blockchain/blocks".
        The message is a block in JSON format.

        After receiving a block, the miner validates it and adds it to its blockchain depending on the honesty.
        """
        block_dict = json.loads(msg.payload.decode())
        # If it's the block of himself, skip to the next iteration
        if block_dict["miner"] == self.miner_name:
            return
        # print(f"[TEST]: {self.miner_name} received block: {block_dict}")
        # Create the block object
        received_block = Block.from_dict(block_dict)
        # Validate the block
        is_valid = self.blockchain.validate_and_add_block(
            received_block, self.num_miners
        )
        if is_valid:
            # The block is valid, stop mining the current block for this miner
            # print(f"Block {received_block.index} mined by another miner, stop mining")
            print(
                f"[INFO]: Block {received_block.index} of {received_block.miner} received by {self.miner_name} is valid, "
                f"adding it to the blockchain"
            )
            self.blockchain.stop_mining_event.set()

    def start(self):
        self.client.loop_start()

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
                last_block.nonce = nonce
                calculated_hash = last_block.calculate_hash()

                if calculated_hash.startswith(CONFIG["STARTWITH_HASH"]):
                    # print(f"Block : {last_block.to_dict()} with hash {calculated_hash}")

                    last_block.hash_ = calculated_hash
                    last_block.end_time = datetime.now()
                    last_block.miner = self.miner_name

                    if self.blockchain.finish_block(
                        last_block, self.miner_name, self.num_miners
                    ):
                        # The block mined is valid, publish it to the other miners

                        # Send the block to the other miners
                        self.blockchain.publish_block(last_block, self.client)

                        # Update miner info in the file
                        self.blockchain.update_miner_info(
                            self.miner_name, CONFIG["REWARD_TOKEN"], 1
                        )

                    break  # break this inner loop, not the outer one
                else:
                    nonce += 1
