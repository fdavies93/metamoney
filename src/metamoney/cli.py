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

logging.basicConfig(level=logging.INFO)


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

@metamoney.group(name="list")
def metamoney_list():
    pass

@metamoney_list.command(help="List allowable pairs of institutions and file formats for input.", name="inputs")
def metamoney_list_inputs():
    for pair in app_data.importer_pairs:
        print(pair[0], pair[1])

@metamoney_list.command(help="List allowable file types to export to.", name="outputs")
def metamoney_list_outputs():
    for output in app_data.exporter_file_types:
        print(output)

@metamoney.command(help="Create journal / ledger entries from a data source and export them in a given data format.")
# this should be sourced from the names set in the importers
@click.option(
    "--institution",
    "-I",
    type=click.Choice(app_data.importer_institutions),
    required=True,
    help="The institution that you want to import data from.",
)
# either stdin, remote, or file path
@click.option(
    "--source",
    "-s",
    type=str,
    required=True,
    help="The data source to import from. Valid choices are stdin, remote, or a file path.",
)
# no default, because we will infer it from the source and/or institution
@click.option(
    "--input-format",
    "-i",
    "input_format",
    type=click.Choice(app_data.importer_file_types),
    help="The format of the data source. Default is CSV if stdin or remote, or inferred from the file path if --source is a path."
)
@click.option(
    "--output-format",
    "-o",
    type=click.Choice(app_data.exporter_file_types),
    default=ExportFormat.BEANCOUNT,
    help="The format to export to."
)
def journal(
    institution: str,
    source: str,
    input_format: str | None,
    output_format: str,
    verbose: int,
    quiet: int
):
    if not input_format and source != "stdin" and source != "remote":
        input_type = Path(source).suffix[1:]
    elif input_format:
        input_type = input_format
    else:
        input_type = DataSourceFormat.CSV

    output_type = output_format

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
