from decimal import Decimal
from datetime import datetime
from abc import ABC
from dataclasses import dataclass

class AbstractTransaction(ABC):
    pass


@dataclass
class GenericTransaction(AbstractTransaction):
    """
    Note that this is NOT a ledger entry; a ledger entry would contain multiple
    transactions. However making an algorithm to truly combine transactions into
    ledger entries is a significant challenge and unnecessary except for very
    high volumes.
    """

    timestamp: datetime
    payee: str
    description: str
    amount: Decimal
    currency: str
    credit_account: str
    debit_account: str
    institution: str


@dataclass
class CathayTransaction(AbstractTransaction):
    transaction_date: datetime
    billing_date: datetime
    description: str
    withdraw: Decimal
    deposit: Decimal
    # balance: Decimal - but this isn't very useful data
    transaction_data: str
    notes: str
