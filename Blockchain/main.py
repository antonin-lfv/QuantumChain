from miner import Miner
import threading


def create_and_start_miners(num_miners):
    miners = []
    threads = []

    for i in range(num_miners):
        print(f"Creating miner {i+1}")
        miner_name = f"Miner{i+1}"
        miner = Miner(miner_name)
        miners.append(miner)

        thread = threading.Thread(target=miner.mine_block)
        threads.append(thread)
        thread.start()

    return miners, threads


if __name__ == "__main__":
    # num_miners = int(input("Enter the number of miners: "))  # Or set this number some other way
    num_miners = 4

    miners, threads = create_and_start_miners(num_miners)
