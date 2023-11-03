from block import Block
import threading
from datetime import datetime
from transaction import Transaction
import random
import json
import os
import hashlib
import time

with open("config.json", "r") as f:
    CONFIG = json.load(f)

# For opening the file, retry if it fails (concurent access)
max_retries = 5  # Max number of retries
retry_delay = 2  # Delay between each retry


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
        self.mean_time_to_mine = sum(
            [
                (b.end_time - b.start_time).total_seconds()
                for b in self.chain
                if b.end_time
            ]
        ) / len(self.chain)

    def load_from_file(self):
        if not os.path.exists(f"blockchain_data.json"):
            # If the file doesn't exist, create a new blockchain
            return self.genesis_block()
        else:
            # Load the blockchain from the file
            with open(f"blockchain_data.json", "r+") as f:
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

    def get_last_mined_block(self):
        # return the last block mined by a miner
        for block in reversed(self.chain):
            if block.miner is not None:
                return block

    def get_current_block(self):
        # return the last block
        return self.chain[-1]

    def finish_block(self, block, miner_name):
        """
        Finish the block by adding the hash, the end_time and the miner.
        :param block: The block to finish
        :param miner_name: The name of the miner who mined the block
        """
        with self.lock:
            last_block = self.get_current_block()

            if block.index < last_block.index or last_block.miner is not None:
                # Conflict, block already exists, do nothing
                # print("Block already exists, block rejected")
                return False

            print(f"Block {block.index} accepted for {miner_name}")
            # print("Block accepted")

            # replace the last block with the new block
            self.chain[-1] = block
            # Update the stats of the blockchain
            self.number_of_transactions += len(block.transactions)
            self.mean_time_to_mine = (
                self.mean_time_to_mine * self.number_of_blocks
                + (block.end_time - block.start_time).total_seconds()
            ) / (self.number_of_blocks + 1)
            # Generate a new block
            self.generate_new_block(hash_=block.hash_, winner_name=miner_name)

            return True

    @staticmethod
    def publish_block(block, client):
        client.publish("blockchain/blocks", json.dumps(block.to_dict()))

    def validate_and_add_block(self, received_block):
        """
        Verify the block and add it to the blockchain if it's valid.
        The block comes from another miner.
        Parameters:
        - block_dict: Block object to validate and add to the blockchain
        - num_miners: Number of miners in the network (for generating transactions)

        The fields to keep for the hash are : transactions, previous_hash, nonce, start_time
        To compare with the field "hash" of the block received.
        """
        last_block = self.get_current_block()

        # print(f"[TEST]: {self.miner_name} get block: {received_block}")
        # print(f"[TEST]: Last block of {self.miner_name}: {last_block}")

        # Verification of the index
        if received_block.index != last_block.index:
            print(
                f"[TEST]: Invalid index: {received_block.index} != {last_block.index}"
            )
            return False

        # Verification of the hash
        if not self.valid_proof_of_work(received_block):
            # Test if the block is valid by comparing the hash of the block with the calculated hash
            # and check if the hash starts with CONFIG["STARTWITH_HASH"]
            # and check if the previous_hash is equal to the hash of the last last block
            return False

        # Verify the transactions (not implemented yet)
        # if not self.valid_transactions(received_block):
        # return False

        # Add the block to the blockchain
        self.chain[-1] = received_block

        # Update the stats of the blockchain
        self.number_of_transactions += len(received_block.transactions)
        self.mean_time_to_mine = (
            self.mean_time_to_mine * self.number_of_blocks
            + (received_block.end_time - received_block.start_time).total_seconds()
        ) / (self.number_of_blocks + 1)

        # Generate a new block and keep the transactions of the block not mined
        # only if the transaction is not already in the blockchain (and if it's not a reward transaction)
        remaining_transactions = []
        # Transform all transactions to dict to compare them (from a copy of the block)
        received_block_transactions_dict = [
            t.to_dict() for t in received_block.transactions
        ]
        last_block_transactions_dict = [t.to_dict() for t in last_block.transactions]
        for transaction in last_block_transactions_dict:
            if (
                transaction not in received_block_transactions_dict
                and transaction["sender"] != "Blockchain"
            ):
                remaining_transactions.append(transaction)

        self.generate_new_block(
            hash_=received_block.hash_,
            winner_name=received_block.miner,
            transactions=remaining_transactions,
        )

        return True

    def valid_proof_of_work(self, received_block):
        # ==== Check if the hash of the block starts with CONFIG["STARTWITH_HASH"]
        if not received_block.hash_.startswith(CONFIG["STARTWITH_HASH"]):
            print(f"[TEST]: Invalid hash condition: {received_block.hash_}")
            return False

        # ==== Check if the previous_hash is equal to the hash of the last last block
        # ONLY IF IT'S NOT THE GENESIS BLOCK
        last_verified_block = self.get_last_mined_block()
        if last_verified_block is not None:
            if last_verified_block.hash_ != received_block.previous_hash:
                print(
                    f"[TEST]: Invalid previous hash: {last_verified_block.hash_} != {received_block.previous_hash}"
                )
                return False

        # ==== Check if the hash of the block is valid
        # Calculate the hash of the block, keeping only the fields needed for the hash
        hash_to_check = received_block.hash_
        received_block = received_block.to_dict()
        del received_block["hash"]
        del received_block["end_time"]
        del received_block["miner"]
        received_block_string = json.dumps(received_block, sort_keys=True)
        # Compare the hash of the block with the calculated hash
        calculated_hash = hashlib.sha256(received_block_string.encode()).hexdigest()
        if calculated_hash != hash_to_check:
            print(
                f"[TEST]: Invalid hash: {calculated_hash} != {hash_to_check} for block {received_block_string}"
            )
            return False

        return True

    def apply_consensus(self):
        """
        Apply the consensus algorithm to the blockchain.

        If the blockchain of the miner (he is honest in this method) is 3 blocks behind the longest blockchain,
        he should start mining on the longest blockchain.

        Steps :
            - Get the longest blockchain
            - Compare the length of the blockchain of the miner with the longest blockchain
            - If the blockchain of the miner is 3 blocks behind the longest blockchain, copy the longest blockchain and
                replace the blockchain of the miner
            - update the stats of the blockchain (in miners_blockchain/blockchain_data_{self.miner_name}.json)
            - update the stats of the miner (in miners.json)
        """

        # Get the longest blockchain
        longest_blockchain = self.get_longest_blockchain_from_miners()
        # Transform to Blockchain object
        longest_blockchain = [Block.from_dict(b) for b in longest_blockchain]

        # Compare the length of the blockchain of the miner with the longest blockchain
        if len(self.chain) < len(longest_blockchain) - 3:
            print(f"[INFO]: Applying consensus for {self.miner_name}")
            # If the blockchain of the miner is 5 blocks behind the longest blockchain, copy the longest blockchain and
            # replace the blockchain of the miner
            self.chain = longest_blockchain
            self.save_blockchain()
            self.number_of_blocks = len(self.chain)
            self.number_of_transactions = sum([len(b.transactions) for b in self.chain])
            self.mean_time_to_mine = sum(
                [
                    (b.end_time - b.start_time).total_seconds()
                    for b in self.chain
                    if b.end_time
                ]
            ) / len(self.chain)

    def valid_transactions(self, received_block):
        """
        Verify if all the transactions of the block are valid. Thus, if the sender has enough tokens for each
        transaction.
        """
        raise NotImplementedError

    def generate_new_block(self, hash_, winner_name, transactions=None):
        """
        Generate a new block and append it to the chain.
        :param hash_: hash of the last block
        :param winner_name: name of the miner who mined the block
        :param transactions: list of transactions to add to the new block (if the miner have some unmined transactions)
        """
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
        if transactions:
            # Add the transactions of the last block not mined
            # (there are only transactions not already in the blockchain)
            for transaction in transactions:
                # print(f"[INFO]: Adding transaction {transaction}")
                new_transaction = Transaction.from_dict(transaction)
                new_block.transactions.append(new_transaction)

        # print(f"New block: {new_block}")
        self.chain.append(new_block)
        self.save_blockchain()
        self.number_of_blocks += 1

    def save_blockchain(self):
        with open(f"blockchain_data.json", "w") as f:
            json.dump([b.to_dict() for b in self.chain], f, indent=4)

    def save_miners(self, miner_data):
        with open("miner.json", "w") as f:
            json.dump(miner_data, f, indent=4)

    def __str__(self) -> str:
        return f"Blockchain: {[str(b) for b in self.chain]}"

    def register_miner(self):
        print(f"Registering miner {self.miner_name}")
        with self.lock:
            try:
                with open("miner.json", "r") as f:
                    miner_data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                miner_data = {}

            # Check if the miner already exists
            if miner_data:
                return  # The miner is already registered

            new_miner_data = {
                "name": self.miner_name,
                "activated": "yes",
                "honesty": True,
            }

            self.save_miners(new_miner_data)

    @staticmethod
    def get_longest_blockchain_from_miners():
        """
        Get the longest blockchain from the miners.
        """
        for _ in range(max_retries):
            try:
                with open("miner.json", "r") as f:
                    miner_data = json.load(f)
                    break
            except Exception as e:
                print(
                    f"[FILE LOGS]: Erreur lors de la lecture du fichier: {e}. "
                    f"Retente dans {retry_delay} secondes..."
                )
                time.sleep(retry_delay)

        longest_blockchain = None

        # TODO: implement the API to get the blockchain of the miners

        return longest_blockchain


if __name__ == "__main__":
    blockchain = Blockchain("Miner1")
    print(blockchain)
