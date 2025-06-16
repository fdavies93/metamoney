from abc import ABC

from metamoney.cli import GenericTransaction
from metamoney.models.config import AppConfig
from metamoney.models.data_sources import DataSource
from metamoney.models.transactions import AbstractTransaction, GenericTransaction

class AbstractImporter(ABC):

    def retrieve(self) -> DataSource:
        raise NotImplementedError()


    def extract(self, data_source: DataSource) -> list[AbstractTransaction]:
        raise NotImplementedError()


    def transform(self, source_transactions: list[AbstractTransaction]) -> list[GenericTransaction]:
        raise NotImplementedError()


    def ingest(self) -> list[GenericTransaction]:
        data_source: DataSource = self.retrieve()
        transactions: list[AbstractTransaction] = self.extract(data_source)
        return self.transform(transactions)
