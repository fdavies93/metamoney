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

class CathayCsvImporter(AbstractImporter):
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


    def read_cathay_csv(self, 
        logger: logging.Logger, input_stream: StreamInfo
    ) -> list[CathayTransaction]:
        reader = csv.reader(input_stream.stream)
        transactions = []
        count = 0
        for i, row in enumerate(reader):
            count += 1
            try:
                logger.debug(row)
                transactions.append(self.read_cathay_csv_row(row))
            except Exception as e:
                logger.debug(e)
                logger.info(
                    f"Failed to read row {i} of {input_stream.name} in read_cathay_csv."
                )
        logger.debug(f"{len(transactions)} valid transactions found in {count} rows.")
        return transactions

    def retrieve(self) -> DataSource:
        pass

    def extract(self, data_source: DataSource) -> list[CathayTransaction]:
        pass

    def transform(self, source_transactions: list[CathayTransaction]) -> list[GenericTransaction]:
        pass
