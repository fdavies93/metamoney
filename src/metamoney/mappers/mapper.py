import re
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

import yaml

from metamoney.models.transactions import GenericTransaction, JournalEntry
from metamoney.utils import pascal_to_snake


@dataclass
class Mapping:
    condition: Callable[[JournalEntry], bool]
    apply: Callable[[JournalEntry], JournalEntry]


class AbstractMapper(ABC):
    @abstractmethod
    def map(
        self,
        transactions: Sequence[GenericTransaction],
        journal_entries: Sequence[JournalEntry],
    ) -> Sequence[JournalEntry]:
        raise NotImplementedError()


class InitialMapper(AbstractMapper):
    """
    Prepares a plain list of transactions for further processing by converting
    them into journal entries.
    """

    def map(
        self,
        transactions: Sequence[GenericTransaction],
        journal_entries: Sequence[JournalEntry],
    ) -> Sequence[JournalEntry]:
        return [
            JournalEntry(transaction.timestamp, transaction.description, [transaction])
            for transaction in transactions
        ]


class GeneralMapper(AbstractMapper):

    def __init__(self, mappings: Sequence[Mapping]):
        super(GeneralMapper, self).__init__()
        self.mappings = mappings

    def map(
        self,
        transactions: Sequence[GenericTransaction],
        journal_entries: Sequence[JournalEntry],
    ) -> Sequence[JournalEntry]:
        entries = list(journal_entries)
        for mapping in self.mappings:
            for i in range(len(entries)):
                if not mapping.condition(entries[i]):
                    continue
                entries[i] = mapping.apply(entries[i])
        return entries
