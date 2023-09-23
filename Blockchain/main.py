from blockchain import Blockchain
from miner import Miner
import threading

def create_and_start_miners(num_miners, blockchain):
    miners = []
    threads = []

    for i in range(num_miners):
        miner_name = f"Miner{i+1}"
        miner = Miner(blockchain, miner_name)
        miners.append(miner)
        
        # Register the miner
        blockchain.register_miner(miner_name)

        thread = threading.Thread(target=miner.mine_block)
        threads.append(thread)
        thread.start()

    return miners, threads


if __name__ == "__main__":
    num_miners = int(input("Enter the number of miners: "))  # Or set this number some other way
    blockchain = Blockchain()

    miners, threads = create_and_start_miners(num_miners, blockchain)