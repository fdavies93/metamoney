from typing import Sequence
from metamoney.importers.importer import AbstractImporter
import logging
from datetime import datetime
from decimal import Decimal

import csv
from metamoney.models.data_sources import DataSource, DataSourceFormat
from metamoney.models.transactions import CathayTransaction, GenericTransaction
from metamoney.models.config import StreamInfo

def get_importer(format: DataSourceFormat):
    match format:
        case DataSourceFormat.CSV:
            return CathayCsvImporter()
    raise ValueError()

class CathayCsvImporter(AbstractImporter[CathayTransaction]):
    logger = logging.getLogger("CathayCsvImporter")

    def read_cathay_csv_row(self, row: list[str]) -> CathayTransaction:
        transaction_date = datetime.strptime(row[0], "%Y/%m/%d\n%H:%M")
        billing_date = datetime.strptime(row[1], "%Y/%m/%d")
        description = row[2].strip()

        clean_withdraw = row[3].replace(",", "").replace("−", "")
        if len(clean_withdraw) > 0:
            withdraw = Decimal(clean_withdraw)
        else:
            withdraw = Decimal(0)

        clean_deposit = row[4].replace(",", "").replace("−", "")
        if len(clean_deposit) > 0:
            deposit = Decimal(clean_deposit)
        else:
            deposit = Decimal(0)
        # no balance as it's not part of the transaction
        transaction_data = row[6]
        notes = row[7].strip()
        return CathayTransaction(
            transaction_date,
            billing_date,
            description,
            withdraw,
            deposit,
            transaction_data,
            notes,
        )


    def read_cathay_csv(self, input_stream: StreamInfo
    ) -> list[CathayTransaction]:
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
        self.logger.debug(f"{len(transactions)} valid transactions found in {count} rows.")
        return transactions

    
    def convert_one_cathay_to_generic(
        self,
        transaction: CathayTransaction
    ) -> GenericTransaction:
        if transaction.deposit > 0:
            amount = transaction.deposit
            credit_account = "Assets:Cathay"
            debit_account = "Income:Unknown"
        elif transaction.withdraw > 0:
            amount = transaction.withdraw
            credit_account = "Expenses:Unknown"
            debit_account = "Assets:Cathay"
        else:
            amount = Decimal(0)
            credit_account = "Expenses:Unknown"
            debit_account = "Income:Unknown"

        generic = GenericTransaction(
            timestamp=transaction.transaction_date,
            payee=transaction.notes,
            description=transaction.description,
            amount=amount,
            currency="NTD",
            credit_account=credit_account,
            debit_account=debit_account,
            institution="cathay",
        )

        self.logger.debug(generic)

        return generic


    def convert_cathay_to_generic(
        self, transactions: Sequence[CathayTransaction]
    ) -> list[GenericTransaction]:
        generics = []
        for transaction in transactions:
            generics.append(self.convert_one_cathay_to_generic(transaction))
        return generics


    def retrieve(self) -> DataSource:
        pass

    def extract(self, data_source: DataSource) -> list[CathayTransaction]:
        return self.read_cathay_csv(data_source.stream)

    def transform(self, source_transactions: Sequence[CathayTransaction]) -> list[GenericTransaction]:
        return self.convert_cathay_to_generic(source_transactions)
