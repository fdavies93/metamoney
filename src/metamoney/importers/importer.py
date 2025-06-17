from abc import ABC

from metamoney.models.config import AppConfig
from metamoney.models.data_sources import DataSource
from metamoney.models.transactions import AbstractTransaction, GenericTransaction
from typing import Sequence

class AbstractImporter(ABC):

    def retrieve(self) -> DataSource:
        raise NotImplementedError()


    def extract(self, data_source: DataSource) -> Sequence[AbstractTransaction]:
        raise NotImplementedError()


    def transform(self, source_transactions: Sequence) -> Sequence[GenericTransaction]:
        raise NotImplementedError()


    def ingest(self) -> Sequence[GenericTransaction]:
        data_source: DataSource = self.retrieve()
        transactions: Sequence[AbstractTransaction] = self.extract(data_source)
        return self.transform(transactions)
