from abc import ABC, abstractmethod

from metamoney.models.config import AppConfig
from metamoney.models.data_sources import DataSource
from metamoney.models.transactions import AbstractTransaction, GenericTransaction
from typing import Iterable, Sequence, Generic, TypeVar

T = TypeVar("T")

class AbstractImporter(ABC, Generic[T]):

    @abstractmethod
    def retrieve(self) -> DataSource:
        pass

    @abstractmethod
    def extract(self, data_source: DataSource) -> Sequence[T]:
        pass

    @abstractmethod
    def transform(self, source_transactions: Sequence[T]) -> Sequence[GenericTransaction]:
        pass

    def ingest(self) -> Sequence[GenericTransaction]:
        data_source: DataSource = self.retrieve()
        transactions: Sequence = self.extract(data_source)
        return self.transform(transactions)
