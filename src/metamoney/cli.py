from enum import StrEnum
import logging
import sys
from pathlib import Path
from typing import Iterable, Sequence

import click

from metamoney import utils
from metamoney.exporters import BeancountExporter, get_exporter
from metamoney.importers import CathayCsvImporter, get_importer
from metamoney.importers.importer import AbstractImporter
from metamoney.registry import importers
from metamoney.mappers.mapper import (
    GeneralMapper,
    InitialMapper,
)
from metamoney.models.config import StreamInfo
from metamoney.models.data_sources import (
    DataSource,
    DataSourceFormat,
    DataSourceInstitution,
)
from metamoney.models.exports import ExportFormat
from metamoney.models.transactions import GenericTransaction, JournalEntry

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
    institution: str,
    source: str,
    input_format: str | None,
    output_format: str | None,
):

    config = utils.get_config_module()
    # lock these until we have a scheme for inference
    input_type = DataSourceFormat.CSV
    output_type = ExportFormat.BEANCOUNT
    output_stream = StreamInfo(sys.stdout, "stdout")

    file_importers = [
        CathayCsvImporter()
    ]
    for file_importer in file_importers:
        importers.register(file_importer)

    if config and isinstance(config.importers, Iterable):
        for file_importer in config.importers:
            if isinstance(file_importer, AbstractImporter):
                existing_importer = get_importer(file_importer.data_institution(), file_importer.data_format())
                if existing_importer:
                    importers.unregister(existing_importer.__class__)
                importers.register(file_importer)

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

    # TODO: Make this less fragile
    if config:
        mappings = config.mappings
        general_mapper = GeneralMapper(mappings)
        entries = general_mapper.map(generic_transactions, entries)

    # TODO: Add a filter option for dates

    exporter = get_exporter(output_type)
    exporter.export(output_stream, entries)


if __name__ == "__main__":
    metamoney()
