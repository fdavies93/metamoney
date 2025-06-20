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

import click
import yaml

from metamoney.exporters import BeancountExporter, get_exporter
from metamoney.importers import CathayCsvImporter, get_importer
from metamoney.mappers.mapper import FallbackMapper
from metamoney.models.config import StreamInfo
from metamoney.models.data_sources import (
    DataSource,
    DataSourceFormat,
    DataSourceInstitution,
)
from metamoney.models.exports import ExportFormat
from metamoney.models.mappings import Mapping
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
    mapper = FallbackMapper()
    entries: Sequence[JournalEntry] = mapper.map(generic_transactions)

    exporter = get_exporter(output_type)
    exporter.export(output_stream, entries)
    # print(data_source.stream.stream.read())


if __name__ == "__main__":
    metamoney()
