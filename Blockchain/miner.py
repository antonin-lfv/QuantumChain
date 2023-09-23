import socket
from blockchain import Blockchain
import threading
from config import CONFIG
import random
from datetime import datetime
from block import Block
from transaction import Transaction


class Miner:
    def __init__(self, blockchain, miner):
        self.blockchain = blockchain
        self.miner = miner  # Name of the miner
        self.tokens = 0

    def mine_block(self):
        while True:
            last_block_data = self.blockchain.get_last_block()
            last_block = Block.from_dict(last_block_data.to_dict())  # Create a copy of the last block
            if last_block.miner is not None:
                continue  # skip to the next iteration
            
            self.blockchain.stop_mining_event.clear()
            
            nonce = random.randint(0, 10000000)
            while not self.blockchain.stop_mining_event.is_set():
                last_block.nonce = nonce
                calculated_hash = last_block.calculate_hash()
                
                if calculated_hash.startswith(CONFIG.STARTWITH_HASH):
                    # print(f"{self.miner} has mined the block with nonce: {nonce}")
                    last_block.hash_ = calculated_hash
                    last_block.end_time = datetime.now()
                    last_block.miner = self.miner
                    last_block.transactions.append(Transaction(sender="Blockchain", 
                                                               recipient=self.miner, 
                                                               amount=CONFIG.REWARD_TOKEN))

                    if self.blockchain.finish_block(last_block, self.miner):
                        # print(f"{self.miner} has been rewarded with {CONFIG.REWARD_TOKEN} tokens")
                        self.tokens += CONFIG.REWARD_TOKEN  # Reward for this example
                    
                    break  # break this inner loop, not the outer one
                else:
                    nonce += 1


if __name__ == "__main__":
    blockchain = Blockchain()  # assume this is your blockchain object
    miner1 = Miner(blockchain, "Miner1")
    miner2 = Miner(blockchain, "Miner2")
    miner3 = Miner(blockchain, "Miner3")

    thread1 = threading.Thread(target=miner1.mine_block)
    thread2 = threading.Thread(target=miner2.mine_block)
    thread3 = threading.Thread(target=miner3.mine_block)

    thread1.start()
    thread2.start()
    thread3.start()