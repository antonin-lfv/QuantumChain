import json
import hashlib
from datetime import datetime
from transaction import Transaction


class Block:
    def __init__(
        self,
        index,
        previous_hash,
        hash_=None,
        transactions=None,
        nonce=None,
        start_time=None,
        end_time=None,
        miner=None,
    ):
        """Constructor for Block

        Args:
            index (int): index of the block
            transactions (list of dict): list of Transaction objects
            previous_hash (str): hash of the previous block
        """
        self.index = index
        self.previous_hash = previous_hash
        self.hash_ = hash_ if hash_ else None
        self.transactions = transactions if transactions else []
        self.nonce = nonce if nonce else None
        self.start_time = (
            datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            if start_time
            else datetime.now()
        )
        self.end_time = (
            datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S") if end_time else None
        )  # Time when the block was mined
        self.miner = miner if miner else None  # Name of the miner who mined the block

    def calculate_hash(self):
        """
        Calculate the hash of the block using the SHA256 algorithm.
        Fields to hash:
        index, transactions, previous_hash, nonce, start_time
        """
        block = self.to_dict()
        # remove hash, end_time and miner from the dict
        del block["hash"]
        del block["end_time"]
        del block["miner"]
        # sort the dict by keys
        block_string = json.dumps(block, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    @classmethod
    def from_dict(cls, data):
        transactions = [Transaction.from_dict(t) for t in data["transactions"]]
        return cls(
            index=data["index"],
            previous_hash=data["previous_hash"],
            transactions=transactions,
            nonce=data["nonce"],
            start_time=data["start_time"],
            end_time=data["end_time"],
            miner=data["miner"],
            hash_=data["hash"],
        )

    def __str__(self) -> str:
        return f"Block {self.index}; Miner: {self.miner}; hash: {self.hash_}; previous_hash: {self.previous_hash}; nonce: {self.nonce}"

    def to_dict(self):
        return {
            "index": self.index,
            "transactions": [t.to_dict() for t in self.transactions]
            if self.transactions
            else [],
            "previous_hash": self.previous_hash,
            "hash": self.hash_ if self.hash_ else None,
            "nonce": self.nonce,
            "start_time": self.start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "end_time": self.end_time.strftime("%Y-%m-%d %H:%M:%S")
            if self.end_time
            else None,
            "miner": self.miner if self.miner else None,
        }
