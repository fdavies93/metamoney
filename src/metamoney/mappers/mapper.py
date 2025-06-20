from abc import ABC, abstractmethod
from typing import Sequence

from metamoney.models.transactions import GenericTransaction, JournalEntry


class AbstractMapper(ABC):
    @abstractmethod
    def map(self, transactions: Sequence[GenericTransaction]) -> Sequence[JournalEntry]:
        raise NotImplementedError()


class FallbackMapper(AbstractMapper):
    """
    The fallback mapper is called if no other mappers produce a result.
    It always maps one transaction to one journal entry, leading to a deliberately
    unbalanced journal entry. This must then be manually reconciled.
    """

    def map(self, transactions: Sequence[GenericTransaction]) -> Sequence[JournalEntry]:
        return [
            JournalEntry(transaction.timestamp, transaction.description, [transaction])
            for transaction in transactions
        ]
