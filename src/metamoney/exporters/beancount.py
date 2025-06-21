import sys
from typing import Sequence

from metamoney.exporters.exporter import AbstractExporter
from metamoney.models.config import StreamInfo
from metamoney.models.transactions import GenericTransaction, JournalEntry


class BeancountExporter(AbstractExporter):

    def write_one_generic_to_beancount(
        self, output_stream: StreamInfo, entry: JournalEntry
    ):

        head = f"{entry.timestamp.strftime('%Y-%m-%d')} * \"{entry.narration}\""
        lines = [head]

        for transaction in entry.transactions:
            line = (
                f"\t{transaction.account} {transaction.amount} {transaction.currency}"
            )
            lines.append(line)
        lines.append("\n")

        print("\n".join(lines), file=output_stream.stream)

    def write_generic_to_beancount(
        self,
        output_stream: StreamInfo,
        journal_entries: Sequence[JournalEntry],
    ):
        for entry in journal_entries:
            self.write_one_generic_to_beancount(output_stream, entry)

    def export(
        self, output_stream: StreamInfo, journal_entries: Sequence[JournalEntry]
    ):
        self.write_generic_to_beancount(output_stream, journal_entries)
