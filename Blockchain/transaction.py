from datetime import datetime


class Transaction:
    def __init__(self, sender, recipient, amount, timestamp=None):
        """Constructor for Transaction

        Args:
            sender (str): sender of the transaction
            recipient (str): recipient of the transaction
            amount (int): amount of the transaction
            timestamp (datetime): timestamp of the transaction
        """
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        if not timestamp:
            self.timestamp = datetime.now()
        else:
            self.timestamp = timestamp

    def __str__(self):
        return f"{self.sender} -> {self.recipient}: {self.amount}"

    def to_dict(self):
        return {
            "sender": self.sender,
            "recipient": self.recipient,
            "amount": self.amount,
            "timestamp": self.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def __eq__(self, other):
        return (
            self.sender == other.sender
            and self.recipient == other.recipient
            and self.amount == other.amount
            and self.timestamp == other.timestamp
        )

    @classmethod
    def from_dict(cls, data):
        return cls(
            data["sender"],
            data["recipient"],
            data["amount"],
            datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S"),
        )
