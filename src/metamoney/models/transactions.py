from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


class AbstractTransaction(ABC):
    pass


# TODO: Simplify the Transaction class and add a JournalEntry class
# for recording the relationship between two transactions
@dataclass
class GenericTransaction(AbstractTransaction):
    timestamp: datetime
    payee: str
    description: str
    amount: Decimal
    balance: Decimal
    currency: str
    account: str
    institution: str


@dataclass
class JournalEntry:
    timestamp: datetime
    narration: str
    transactions: list[GenericTransaction]


@dataclass
class CathayTransaction(AbstractTransaction):
    transaction_date: datetime
    billing_date: datetime
    description: str
    withdraw: Decimal
    deposit: Decimal
    balance: Decimal
    transaction_data: str
    notes: str
