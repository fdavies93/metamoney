import csv
import logging
import sys
from datetime import datetime
from decimal import Decimal
from typing import Sequence

from metamoney.importers.importer import AbstractImporter
from metamoney.models.config import StreamInfo
from metamoney.models.data_sources import (
    DataSource,
    DataSourceFormat,
    DataSourceInstitution,
)
from metamoney.models.transactions import CathayTransaction, GenericTransaction


def get_importer(format: DataSourceFormat):
    match format:
        case DataSourceFormat.CSV:
            return CathayCsvImporter()
    raise ValueError()


def clean_number_string(num_string: str) -> Decimal:
    # Use the character code for − because it is NOT an ASCII dash
    clean = num_string.replace(",", "").replace(chr(8722), "")
    if len(clean) > 0:
        return Decimal(clean)
    else:
        return Decimal(0)


class CathayCsvImporter(AbstractImporter[CathayTransaction]):
    logger = logging.getLogger("CathayCsvImporter")

    def read_cathay_csv_row(self, row: list[str]) -> CathayTransaction:
        transaction_date = datetime.strptime(row[0], "%Y/%m/%d\n%H:%M")
        billing_date = datetime.strptime(row[1], "%Y/%m/%d")
        description = row[2].strip()

        withdraw = clean_number_string(row[3])

        deposit = clean_number_string(row[4])

        balance = clean_number_string(row[5])

        transaction_data = row[6]
        notes = row[7].strip()
        return CathayTransaction(
            transaction_date,
            billing_date,
            description,
            withdraw,
            deposit,
            balance,
            transaction_data,
            notes,
        )

    def read_cathay_csv(self, input_stream: StreamInfo) -> list[CathayTransaction]:
        reader = csv.reader(input_stream.stream)
        transactions = []
        count = 0
        for i, row in enumerate(reader):
            count += 1
            try:
                self.logger.debug(row)
                transactions.append(self.read_cathay_csv_row(row))
            except Exception as e:
                self.logger.debug(e)
                self.logger.info(
                    f"Failed to read row {i} of {input_stream.name} in read_cathay_csv."
                )
        self.logger.debug(
            f"{len(transactions)} valid transactions found in {count} rows."
        )
        return transactions

    def convert_one_cathay_to_generic(
        self, transaction: CathayTransaction
    ) -> GenericTransaction:
        if transaction.deposit > 0:
            amount = transaction.deposit
        elif transaction.withdraw > 0:
            amount = -transaction.withdraw
        else:
            amount = Decimal(0)

        generic = GenericTransaction(
            timestamp=transaction.transaction_date,
            payee=transaction.notes,
            description=transaction.description,
            amount=amount,
            balance=transaction.balance,
            currency="NTD",
            account="Assets:Checking:Cathay",
            institution=DataSourceInstitution.CATHAY_BANK_TW,
        )

        self.logger.debug(generic)

        return generic

    def convert_cathay_to_generic(
        self, transactions: Sequence[CathayTransaction]
    ) -> list[GenericTransaction]:
        generics = []
        for transaction in transactions:
            generics.append(self.convert_one_cathay_to_generic(transaction))
        return generics[::-1]

    def retrieve(self) -> DataSource:
        raise NotImplementedError()

    def extract(self, data_source: DataSource) -> list[CathayTransaction]:
        return self.read_cathay_csv(data_source.stream)

    def transform(
        self, source_transactions: Sequence[CathayTransaction]
    ) -> list[GenericTransaction]:
        return self.convert_cathay_to_generic(source_transactions)
