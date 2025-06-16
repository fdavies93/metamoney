import csv
import logging
import re
import sys
from abc import ABC
from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from time import strftime
from typing import Callable, Literal, Optional, TextIO
from metamoney.utils import pascal_to_snake

import click
import yaml

logging.basicConfig(level=logging.DEBUG)


@dataclass
class FieldMatchesCondition:
    field_matches: tuple[str, str] | None

@dataclass
class AllOfCondition:
    all_of: list["MappingCondition"]

@dataclass
class AnyOfCondition:
    any_of: list["MappingCondition"]

type CompoundCondition = AllOfCondition | AnyOfCondition

type MappingCondition = FieldMatchesCondition | CompoundCondition

@dataclass
class Mapping:
    when: MappingCondition
    remap: dict[str, str]


@dataclass
class StreamInfo:
    stream: TextIO
    name: str


@dataclass
class GenericTransaction:
    """
    Note that this is NOT a ledger entry; a ledger entry would contain multiple
    transactions. However making an algorithm to truly combine transactions into
    ledger entries is a significant challenge and unnecessary except for very
    high volumes.
    """

    timestamp: datetime
    payee: str
    description: str
    amount: Decimal
    currency: str
    credit_account: str
    debit_account: str
    institution: str


def check_input_format(
    input_formats: dict[str, dict[str, Callable]], institution: str, format: str
) -> bool:
    if institution not in input_formats:
        return False
    formats = input_formats[institution]
    if format not in formats:
        return False
    return True


def initialize_logger(verbose: bool, quiet: bool) -> logging.Logger:
    if verbose and quiet:
        raise ValueError("Output cannot be both verbose and quiet.")
    log_level = logging.INFO
    if verbose:
        log_level = logging.DEBUG
    elif quiet:
        log_level = logging.CRITICAL

    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    return logger


def initialize_streams(
    input_path: Path | None, output_path: Path | None, overwrite: bool
) -> tuple[StreamInfo, StreamInfo]:
    input_stream: TextIO = sys.stdin
    output_stream: TextIO = sys.stdout
    if input_path is not None:
        if not input_path.exists():
            raise ValueError(f"Could not find input file {str(input_path)}")
        input_stream = input_path.open("r")
        input_name = str(input_path)
    else:
        input_name = "stdin"
    if output_path is not None:
        if overwrite:
            output_stream = output_path.open("w")
        else:
            output_stream = output_path.open("a")
        output_name = str(output_path)
    else:
        output_name = "stdout"

    return StreamInfo(input_stream, input_name), StreamInfo(output_stream, output_name)


def close_streams(input_stream: StreamInfo, output_stream: StreamInfo):
    if input_stream != sys.stdin:
        input_stream.stream.close()
    if output_stream != sys.stdout:
        output_stream.stream.close()


@dataclass
class CathayTransaction:
    transaction_date: datetime
    billing_date: datetime
    description: str
    withdraw: Decimal
    deposit: Decimal
    # balance: Decimal - but this isn't very useful data
    transaction_data: str
    notes: str


def read_cathay_csv_row(row: list[str]) -> CathayTransaction:
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


def read_cathay_csv(
    logger: logging.Logger, input_stream: StreamInfo
) -> list[CathayTransaction]:
    reader = csv.reader(input_stream.stream)
    transactions = []
    count = 0
    for i, row in enumerate(reader):
        count += 1
        try:
            logger.debug(row)
            transactions.append(read_cathay_csv_row(row))
        except Exception as e:
            logger.debug(e)
            logger.info(
                f"Failed to read row {i} of {input_stream.name} in read_cathay_csv."
            )
    logger.debug(f"{len(transactions)} valid transactions found in {count} rows.")
    return transactions


def convert_one_cathay_to_generic(
    logger: logging.Logger, transaction: CathayTransaction
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

    logger.debug(generic)

    return generic


def convert_cathay_to_generic(
    logger: logging.Logger, transactions: list[CathayTransaction]
) -> list[GenericTransaction]:
    generics = []
    for transaction in transactions:
        generics.append(convert_one_cathay_to_generic(logger, transaction))
    return generics


def write_one_generic_to_beancount(
    logger: logging.Logger, output_stream: StreamInfo, transaction: GenericTransaction
):
    output_stream.stream.writelines(
        (
            f"{transaction.timestamp.strftime('%Y-%m-%d')} * \"{transaction.payee}\" \"{transaction.description}\"\n",
            f"\t{transaction.credit_account} {transaction.amount} {transaction.currency}\n",
            f"\t{transaction.debit_account} {-transaction.amount} {transaction.currency}\n\n",
        )
    )


def write_generic_to_beancount(
    logger: logging.Logger,
    output_stream: StreamInfo,
    transactions: list[GenericTransaction],
):
    for transaction in transactions:
        write_one_generic_to_beancount(logger, output_stream, transaction)

def load_map(logger: logging.Logger, path: Path) -> dict[str, list[Mapping]]:
    output_map: dict[str, list[Mapping]] = {}
    if not path.exists():
        raise ValueError()
    with path.open("r") as f:
        loaded_map: dict = yaml.load(f, yaml.Loader)

    logger.debug(loaded_map)
    # May be worth switching to Pydantic etc for better handling in the future
    # but this version is already implemented, so whatever
    for k, v in loaded_map.items():
        # v is a list of mappings
        output_list: list[Mapping] = []
        for mapping in v:
            remap: dict = mapping["Remap"]
            output_remap = {}
            for k1, v1 in remap.items():
                output_remap[pascal_to_snake(k1)] = v1

            field_matches = mapping["When"].get("FieldMatches")
            field_matches[0] = pascal_to_snake(field_matches[0])

            output_mapping = Mapping(
                FieldMatchesCondition(field_matches=tuple(field_matches)),
                remap=output_remap,
            )
            output_list.append(output_mapping)
        output_map[pascal_to_snake(k)] = output_list
    return output_map


def get_mapping_result(
    logger: logging.Logger, mapping: Mapping, transaction: GenericTransaction
) -> GenericTransaction:
    output_transaction = deepcopy(transaction)
    for field, new_value in mapping.remap.items():
        setattr(output_transaction, field, new_value)
    return output_transaction


def check_mapping_applies(
    logger: logging.Logger, mapping: Mapping, transaction: GenericTransaction
) -> bool:
    if mapping.when.field_matches is None:
        return False
    target_field, match_pattern = mapping.when.field_matches
    target_field_value = getattr(transaction, target_field)
    if re.match(match_pattern, target_field_value):
        return True
    return False


def process_one_mapping(
    logger: logging.Logger,
    mappings: dict[str, list[Mapping]],
    transaction: GenericTransaction,
) -> GenericTransaction:
    working_transaction = transaction
    if transaction.institution in mappings:
        for mapping in mappings[transaction.institution]:
            if check_mapping_applies(logger, mapping, working_transaction):
                working_transaction = get_mapping_result(
                    logger, mapping, working_transaction
                )
    all_mappings: list[Mapping] | None = mappings.get("all")
    if all_mappings is not None:
        for mapping in all_mappings:
            if check_mapping_applies(logger, mapping, working_transaction):
                working_transaction = get_mapping_result(
                    logger, mapping, working_transaction
                )
    return working_transaction


def process_map(
    logger: logging.Logger,
    mappings: dict[str, list[Mapping]],
    transactions: list[GenericTransaction],
) -> list[GenericTransaction]:
    return [
        process_one_mapping(logger, mappings, transaction)
        for transaction in transactions
    ]


@click.command
@click.option("--input-path", "-i", type=Path)
@click.option("--output-path", "-o", type=Path)
@click.option("--institution", "-I", type=click.Choice(["cathay"]), required=True)
@click.option("--input-format", default="csv")
@click.option("--output-format", default="beancount")
@click.option("--quiet", "-q", count=True)
@click.option("--verbose", "-v", count=True)
@click.option("--overwrite", "-w", is_flag=True, default=False)
@click.option("--map-path", "-m", type=Path)
@click.option("--dry-run", is_flag=True, default=False)
def main(
    input_path: Path | None,
    output_path: Path | None,
    institution: Literal["cathay"],
    input_format: Literal["csv"],
    output_format: Literal["beancount"],
    verbose: int,
    quiet: int,
    overwrite: bool,
    map_path: Path | None,
    dry_run: bool,
):

    input_formats = {"cathay": {"csv": read_cathay_csv}}

    convert_to_generic = {"cathay": convert_cathay_to_generic}

    logger = initialize_logger(verbose > 0, quiet > 0)
    input_stream, output_stream = initialize_streams(input_path, output_path, overwrite)

    if not check_input_format(input_formats, institution, input_format):
        logger.error(
            f"No importer exists for institution {institution} and input format {input_format}"
        )
        sys.exit(1)

    logger.debug(f"Converting from {input_stream.name} to {output_stream.name}.")

    transactions = input_formats[institution][input_format](logger, input_stream)

    generic_transactions = convert_to_generic[institution](logger, transactions)

    generic_transactions = sorted(generic_transactions, key=lambda t: t.timestamp)

    # post-processing steps

    # sort

    # remap
    if map_path is not None:
        map_data = load_map(logger, map_path)
        logger.debug(map_data)
        generic_transactions = process_map(logger, map_data, generic_transactions)

    # logger.debug(generic_transactions)

    if not dry_run:
        write_generic_to_beancount(logger, output_stream, generic_transactions)

    close_streams(input_stream, output_stream)


if __name__ == "__main__":
    main()
