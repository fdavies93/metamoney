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
from typing import Callable, Literal, Sequence, TextIO
from uuid import uuid4

import click
import yaml

from metamoney.exporters import BeancountExporter, get_exporter
from metamoney.importers import CathayCsvImporter, get_importer
from metamoney.mappers.mapper import (
    AddCounterTransactionRemap,
    AllCondition,
    GeneralMapper,
    InitialMapper,
    Mapping,
    SetNarrationRemap,
    TransactionFieldMatchesCondition,
)
from metamoney.models.config import StreamInfo
from metamoney.models.data_sources import (
    DataSource,
    DataSourceFormat,
    DataSourceInstitution,
)
from metamoney.models.exports import ExportFormat
from metamoney.models.transactions import (
    CathayTransaction,
    GenericTransaction,
    JournalEntry,
)
from metamoney.utils import pascal_to_snake

logging.basicConfig(level=logging.DEBUG)


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


@click.group()
def metamoney():
    pass


@metamoney.command()
# this should be sourced from the names set in the importers
@click.option(
    "--institution",
    type=click.Choice(list(DataSourceInstitution)),
    required=True,
    help="The institution that you want to import data from.",
)
# either stdin, remote, or file path
@click.option(
    "--source",
    type=str,
    required=True,
    help="The data source to import from. Valid choices are stdin, remote, or a file path.",
)
# no default, because we will infer it from the source and/or institution
@click.option(
    "--input-format", "input_format", type=click.Choice(list(DataSourceFormat))
)
@click.option("--output-format", type=click.Choice(("beancount",)))
def transactions(
    institution: DataSourceInstitution,
    source: str,
    input_format: DataSourceFormat | None,
    output_format: str | None,
):

    # lock these until we have a scheme for inference
    input_type = DataSourceFormat.CSV
    output_type = ExportFormat.BEANCOUNT
    output_stream = StreamInfo(sys.stdout, "stdout")

    importer = get_importer(institution, input_type)

    generic_transactions: Sequence[GenericTransaction]

    if source == "remote":
        data_source = importer.retrieve()
    elif source == "stdin":
        stream = StreamInfo(sys.stdin, "stdin")
        data_source = DataSource(institution, input_type, stream)
    else:
        source_as_path: Path = Path(source)
        if not (source_as_path.exists() and source_as_path.is_file()):
            print("--source must be 'remote', 'stdin', or a valid path to a file.")
            exit(1)
        stream = StreamInfo(source_as_path.open(), str(source_as_path.resolve()))
        data_source = DataSource(institution, input_type, stream)

    institution_transactions = importer.extract(data_source)
    generic_transactions = importer.transform(institution_transactions)

    # TODO: Make this a proper workflow which calls multiple mappers
    initial_mapper = InitialMapper()
    entries: Sequence[JournalEntry] = initial_mapper.map(generic_transactions, [])

    # TODO: Figure out whether a dynamic Python mapper might be better - yes,
    # for sure, it lets you do stuff with arguments for free.

    my_mapping = Mapping(
        AllCondition(
            TransactionFieldMatchesCondition("account", "^Assets.*"),
            TransactionFieldMatchesCondition("payee", "AGODA.COM"),
        ),
        (
            AddCounterTransactionRemap("Expenses:Living:Hotel"),
            SetNarrationRemap("Agoda"),
        ),
    )

    general_mapper = GeneralMapper([my_mapping])
    entries = general_mapper.map(generic_transactions, entries)

    # TODO: Add a filter option for dates

    exporter = get_exporter(output_type)
    exporter.export(output_stream, entries)


if __name__ == "__main__":
    metamoney()
