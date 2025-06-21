import re
from abc import ABC, abstractmethod
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence
from uuid import uuid4

import yaml

from metamoney.models.transactions import GenericTransaction, JournalEntry
from metamoney.utils import pascal_to_snake


@dataclass
class Mapping:
    condition: Callable[[JournalEntry], bool]
    apply: Sequence[Callable[[JournalEntry], JournalEntry]]


def AllCondition(
    *args: Callable[[JournalEntry], bool]
) -> Callable[[JournalEntry], bool]:
    # i.e. execute all of them with the entry provided, check that all return true
    return lambda e: all(map(lambda c: c(e), args))


def AnyCondition(
    *args: Callable[[JournalEntry], bool]
) -> Callable[[JournalEntry], bool]:
    # i.e. execute all of them with the entry provided, check that all return true
    return lambda e: any(map(lambda c: c(e), args))


def TransactionFieldMatchesCondition(
    field: str, regexp: str
) -> Callable[[JournalEntry], bool]:
    def fn(entry: JournalEntry):
        for transaction in entry.transactions:
            field_val = getattr(transaction, field)
            if field_val is None:
                continue
            elif not isinstance(field_val, str):
                raise TypeError()
            if re.match(regexp, field_val):
                return True
        return False

    return fn


def SetNarrationRemap(new_narration: str) -> Callable[[JournalEntry], JournalEntry]:
    def remap(entry: JournalEntry) -> JournalEntry:
        new_entry = deepcopy(entry)
        new_entry.narration = new_narration
        return new_entry

    return remap


def AddCounterTransactionRemap(
    counter_transaction_category: str,
) -> Callable[[JournalEntry], JournalEntry]:
    def remap(entry: JournalEntry) -> JournalEntry:
        new_entry = deepcopy(entry)
        asset_transactions = list(
            filter(lambda t: re.match("^Assets.*", t.account), entry.transactions)
        )
        if not asset_transactions:
            raise ValueError()
        asset_transaction = asset_transactions[0]
        counter_transaction = GenericTransaction(
            uuid4().hex,
            asset_transaction.timestamp,
            None,
            None,
            -asset_transaction.amount,
            None,
            asset_transaction.currency,
            counter_transaction_category,
            None,
        )
        new_entry.transactions.append(counter_transaction)
        return new_entry

    return remap


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
            JournalEntry(
                transaction.timestamp, transaction.description or "", [transaction]
            )
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
                for apply_fn in mapping.apply:
                    entries[i] = apply_fn(entries[i])
        return entries
