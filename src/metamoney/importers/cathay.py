import csv
import logging
import sys
import uuid
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Sequence

from playwright.sync_api import sync_playwright

from metamoney.importers.importer import AbstractImporter
from metamoney.models.config import StreamInfo
from metamoney.models.data_sources import (
    DataSource,
    DataSourceFormat,
    DataSourceInstitution,
)
from metamoney.models.transactions import CathayTransaction, GenericTransaction
from metamoney.utils import get_config_module

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
 
    @staticmethod
    def data_format() -> DataSourceFormat:
        return DataSourceFormat.CSV

    @staticmethod
    def data_institution() -> DataSourceInstitution:
        return DataSourceInstitution.CATHAY_BANK_TW

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
            uuid.uuid4().hex,
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
            transaction_id=transaction.transaction_id,
            timestamp=transaction.transaction_date,
            payee=transaction.notes,
            description=f"{transaction.notes} {transaction.description}",
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

    def scrape_cathay(self):
        config = get_config_module()
        if not (config and config.download_root):
            raise ValueError("No download root found in config.")
        download_root = config.download_root
        if not (
            config
            and config.accounts
            and config.accounts.get(DataSourceInstitution.CATHAY_BANK_TW)
        ):
            raise ValueError("Couldn't find account information for Cathay Bank")
        account_info: dict[str, str] = config.accounts.get(
            DataSourceInstitution.CATHAY_BANK_TW
        )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()
            page.goto("https://www.cathaybk.com.tw/mybank")
            page.goto(
                "https://www.cathaybk.com.tw/mybank/quicklinks/home/setmultilanguage?Culture=en-US"
            )

            page.get_by_label("ID Number").fill(account_info["id_number"])
            page.get_by_label("Username").fill(account_info["username"])
            page.get_by_label("Password", exact=True).fill(account_info["password"])

            page.get_by_role("button", name="Login").click()

            # <div class="btn-count-down btn  btn-size-md m-btn-height-sm sent-code-btn  " id="js-otp-send" data-btn-word="Send">
            #     <div class="btn-count-down-bar" style="width: 90%; display: none;">
            #     </div>
            # </div>

            page.locator("#js-otp-send").click()
            # click button "Send"
            # fill out OTP
            print("Please enter OTP from SMS:", file=sys.stderr)
            otp = input()
            # <input class="has-prefix-code" name="OtpPassword" id="OtpPassword" value="" required="" maxlength="6" tabindex="1" autocomplete="off" data-valid="OtpPassword" pattern="[0-9]*" oninput="NumberFilter(this.value,'OtpPassword')" type="text" placeholder="last 6 numbers">
            page.get_by_placeholder("last 6 numbers").fill(otp)

            # click Submit
            page.get_by_role("button", name="OK").click()
            page.get_by_role("button", name="暫時不用").click()
            page.get_by_role("link", name=account_info["account_no"]).click()

            page.get_by_role("button", name="Print/Download").click()

            with page.expect_download() as download_info:
                page.get_by_role("menuitem", name="Download CSV").click()
            download = download_info.value

            ts = datetime.now()
            filename = ts.strftime(
                f"%Y-%m-%d-%H%M%S-cathay-{account_info["account_no"]}.csv"
            )
            file_path = f"{download_root}/{filename}"

            download.save_as(file_path)

            return file_path

    def retrieve(self) -> DataSource:
        file_path = self.scrape_cathay()
        return DataSource(
            DataSourceInstitution.CATHAY_BANK_TW,
            DataSourceFormat.CSV,
            StreamInfo(Path(file_path).open(), file_path),
        )

    def extract(self, data_source: DataSource) -> list[CathayTransaction]:
        return self.read_cathay_csv(data_source.stream)

    def transform(
        self, source_transactions: Sequence[CathayTransaction]
    ) -> list[GenericTransaction]:
        return self.convert_cathay_to_generic(source_transactions)
