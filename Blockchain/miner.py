import socket
from blockchain import Blockchain
import threading
import random
from datetime import datetime
from block import Block
from transaction import Transaction

# Get config from config.json
import json
with open('config.json', 'r') as f:
    CONFIG = json.load(f)


class Miner:
    def __init__(self, miner):
        self.blockchain = Blockchain(miner)
        self.miner = miner  # Name of the miner

    def mine_block(self):
        while True:
            last_block_data = self.blockchain.get_last_block()
            last_block = Block.from_dict(last_block_data.to_dict())  # Create a copy of the last block
            if last_block.miner is not None:
                continue  # skip to the next iteration
            
            self.blockchain.stop_mining_event.clear()
            
            nonce = random.randint(0, 10000000000)
            while not self.blockchain.stop_mining_event.is_set():
                last_block.nonce = nonce
                calculated_hash = last_block.calculate_hash()
                
                if calculated_hash.startswith(CONFIG["STARTWITH_HASH"]):
                    # print(f"{self.miner} has mined the block with nonce: {nonce}")
                    last_block.hash_ = calculated_hash
                    last_block.end_time = datetime.now()
                    last_block.miner = self.miner

                    if self.blockchain.finish_block(last_block, self.miner):
                        # print(f"{self.miner} has been rewarded with {CONFIG.REWARD_TOKEN} tokens")
                        
                        # Update miner info in the file
                        self.blockchain.update_miner_info(self.miner, CONFIG["REWARD_TOKEN"], 1)
              
                    break  # break this inner loop, not the outer one
                else:
                    nonce += 1
