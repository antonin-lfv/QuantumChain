from datetime import datetime


class Transaction:
    def __init__(self, sender, recipient, amount):
        """Constructor for Transaction

        Args:
            sender (str): sender of the transaction
            recipient (str): recipient of the transaction
            amount (int): amount of the transaction
        """
        self.sender = sender
        self.recipient = recipient
        self.amount = amount
        self.timestamp = datetime.now()

    def __str__(self):
        return f"{self.sender} -> {self.recipient}: {self.amount}"

    def to_dict(self):
        return {
            'sender': self.sender,
            'recipient': self.recipient,
            'amount': self.amount,
            'timestamp': self.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }

    @classmethod
    def from_dict(cls, data):
        return cls(data['sender'], data['recipient'], data['amount'])
