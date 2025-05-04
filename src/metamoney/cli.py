import logging
import sys
from enum import StrEnum
from pathlib import Path
from typing import Literal, TextIO

import click

logging.basicConfig(level=logging.DEBUG)


@click.command
@click.option("--input-path", "-i", type=Path)
@click.option("--output-path", "-o", type=Path)
@click.option("--institution", "-I", type=click.Choice(["cathay"]), required=True)
@click.option("--input-format", default="csv")
@click.option("--output-format", default="beancount")
@click.option("--verbose", "-v", count=True)
@click.option("--overwrite", "-w", is_flag=True, default=False)
def main(
    input_path: Path | None,
    output_path: Path | None,
    institution: Literal["cathay"],
    input_format: Literal["csv"],
    output_format: Literal["beancount"],
    verbose: int,
    overwrite: bool,
):
    input_name: str
    output_name: str

    log_level = logging.INFO
    if verbose > 0:
        log_level = logging.DEBUG

    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)

    input_stream: TextIO = sys.stdin
    output_stream: TextIO = sys.stdout
    if input_path is not None:
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

    logger.info(f"Converting from {input_name} to {output_name}.")

    if input_stream != sys.stdin:
        input_stream.close()
    if output_stream != sys.stdout:
        output_stream.close()


if __name__ == "__main__":
    main()
