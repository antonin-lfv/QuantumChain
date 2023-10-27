from block import Block
import threading
from datetime import datetime
from transaction import Transaction
import random

# Get config from config.json
import json
import os

with open("config.json", "r") as f:
    CONFIG = json.load(f)


class Blockchain:
    def __init__(self, miner_name):
        self.lock = threading.Lock()  # For thread-safe operations
        self.miner_name = miner_name
        self.register_miner()
        self.chain = self.load_from_file()
        self.save_blockchain()  # Save
        self.stop_mining_event = threading.Event()
        # State of the blockchain
        self.number_of_blocks = len(self.chain)
        self.number_of_transactions = sum([len(b.transactions) for b in self.chain])
        self.number_of_tokens = sum(
            [t.amount for b in self.chain for t in b.transactions]
        )
        self.mean_time_to_mine = sum(
            [
                (b.end_time - b.start_time).total_seconds()
                for b in self.chain
                if b.end_time
            ]
        ) / len(self.chain)

    def load_from_file(self):
        if not os.path.exists(
            f"miners_blockchain/blockchain_data_{self.miner_name}.json"
        ):
            # If the file doesn't exist, create a new blockchain
            return self.genesis_block()
        else:
            # Load the blockchain from the file
            with open(
                f"miners_blockchain/blockchain_data_{self.miner_name}.json", "r+"
            ) as f:
                chain_data = json.load(f)

            chain = []
            for block_data in chain_data:
                block = Block.from_dict(block_data)
                chain.append(block)

            return chain

    @staticmethod
    def genesis_block():
        genesis_block = Block(index=0, previous_hash="0000000000")
        return [genesis_block]

    def get_last_block(self):
        return self.chain[-1]

    def finish_block(self, block, miner_name):
        with self.lock:
            last_block = self.get_last_block()

            if block.index < last_block.index or last_block.miner is not None:
                # Conflict, block already exists, do nothing
                # print("Block already exists, block rejected")
                return False

            print(f"Block {block.index} accepted for miner {miner_name}")
            # print("Block accepted")
            self.stop_mining_event.set()  # Notify other miners to stop mining this block
            # TODO : envoyer le block aux autres mineurs pour qu'ils arrêtent de miner ce block s'ils le minent
            # et qu'ils l'ajoutent à leur blockchain s'ils ne l'ont pas déjà

            # replace the last block with the new block
            self.chain[-1] = block
            # Update the state of the blockchain
            self.number_of_transactions += len(block.transactions)
            self.number_of_tokens += sum([t.amount for t in block.transactions])
            self.mean_time_to_mine = (
                self.mean_time_to_mine * self.number_of_blocks
                + (block.end_time - block.start_time).total_seconds()
            ) / (self.number_of_blocks + 1)
            # Generate a new block
            self.generate_new_block(hash_=block.hash_, winner_name=miner_name)

            return True

    def generate_new_block(self, hash_, winner_name):
        # print(f"Generating new block, hash: {hash_}")
        # Create a new block and append it to the chain
        new_block = Block(index=len(self.chain), previous_hash=hash_)
        # Reward the miner in the new block
        new_block.transactions = [
            Transaction(
                sender="Blockchain",
                recipient=winner_name,
                amount=CONFIG["REWARD_TOKEN"],
            )
        ]
        # Add random transactions to the new block
        new_block.transactions.append(
            Transaction(
                sender=self.miner_name,
                recipient=f"Miner_random",
                amount=random.randint(1, 10),
                timestamp=datetime(2023, 10, 26, 16, 26, 52, 91342),
            )
        )
        # print(f"New block: {new_block}")
        self.chain.append(new_block)
        self.save_blockchain()
        self.number_of_blocks += 1

    def save_blockchain(self):
        with open(
            f"miners_blockchain/blockchain_data_{self.miner_name}.json", "w"
        ) as f:
            json.dump([b.to_dict() for b in self.chain], f, indent=4)

    def save_miners(self, miners_data):
        with open("miners.json", "w") as f:
            json.dump(miners_data, f, indent=4)

    def __str__(self) -> str:
        return f"Blockchain: {[str(b) for b in self.chain]}"

    def register_miner(self):
        print(f"Registering miner {self.miner_name}")
        with self.lock:
            try:
                with open("miners.json", "r") as f:
                    miners_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                miners_data = []

            # Check if the miner already exists
            if any(miner["name"] == self.miner_name for miner in miners_data):
                return  # The miner is already registered

            new_miner_data = {
                "name": self.miner_name,
                "tokens": 0,
                "nb_blocks_mined": 0,
                "activated": "yes",
                "honesty": True,
            }

            miners_data.append(new_miner_data)

            self.save_miners(miners_data)

    def update_miner_info(self, miner_name, tokens, blocks_mined):
        with self.lock:
            try:
                with open("miners.json", "r") as f:
                    miners_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                miners_data = []

            for miner in miners_data:
                if miner["name"] == miner_name:
                    miner["tokens"] += tokens
                    miner["tokens"] = round(miner["tokens"], 3)
                    miner["nb_blocks_mined"] += blocks_mined
                    break
            else:
                return  # Miner not found

            self.save_miners(miners_data)


if __name__ == "__main__":
    blockchain = Blockchain("Miner1")
    print(blockchain)
