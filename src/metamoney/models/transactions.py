from abc import ABC
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


class AbstractTransaction(ABC):
    pass


# TODO: Simplify the Transaction class and add a JournalEntry class
# for recording the relationship between two transactions
@dataclass
class GenericTransaction(AbstractTransaction):
    transaction_id: str
    timestamp: datetime
    payee: Optional[str]
    description: Optional[str]
    amount: Decimal
    balance: Optional[Decimal]
    currency: str
    account: str
    institution: Optional[str]


@dataclass
class JournalEntry:
    timestamp: datetime
    narration: str
    transactions: list[GenericTransaction]


@dataclass
class CathayTransaction(AbstractTransaction):
    transaction_id: str
    transaction_date: datetime
    billing_date: datetime
    description: str
    withdraw: Decimal
    deposit: Decimal
    balance: Decimal
    transaction_data: str
    notes: str
