import logging
import sys
from pathlib import Path
from typing import Sequence

import click

from metamoney.mappers.mapper import GeneralMapper, InitialMapper
from metamoney.models.app_data import AppData
from metamoney.models.data_sources import DataSource, DataSourceFormat
from metamoney.models.exports import ExportFormat
from metamoney.models.stream_info import StreamInfo
from metamoney.models.transactions import GenericTransaction, JournalEntry

logging.basicConfig(level=logging.DEBUG)


app_data = AppData()


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
    type=str,
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
    "--input-format", "input_format", type=click.Choice(app_data.importer_file_types)
)
@click.option("--output-format", type=click.Choice(app_data.exporter_file_types))
def transactions(
    institution: str,
    source: str,
    input_format: str | None,
    output_format: str | None,
):
    # TODO: Write file type inference function
    input_type = DataSourceFormat.CSV
    output_type = ExportFormat.BEANCOUNT

    importer = app_data.get_importer(institution, input_type)
    if not importer:
        print(
            f"Couldn't find an importer for data type {input_type} and institution {institution}",
            file=sys.stderr,
        )
        exit(1)

    exporter = app_data.get_exporter(output_type)
    if not exporter:
        print(
            f"Couldn't find an exporter for data type {output_type}",
            file=sys.stderr,
        )
        exit(1)

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

    general_mapper = GeneralMapper(app_data.mappings)
    entries = general_mapper.map(generic_transactions, entries)

    # TODO: Add a filter option for dates

    exporter.export(app_data.output_stream, entries)


if __name__ == "__main__":
    metamoney()
