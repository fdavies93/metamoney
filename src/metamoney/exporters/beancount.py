from typing import Sequence

from metamoney.exporters.exporter import AbstractExporter
from metamoney.models.stream_info import StreamInfo
from metamoney.models.transactions import JournalEntry


class BeancountExporter(AbstractExporter):

    @staticmethod
    def data_format() -> str:
        return "beancount"

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

        print("\n".join(lines), file=output_stream.stream, end="")

    def write_generic_to_beancount(
        self,
        output_stream: StreamInfo,
        journal_entries: Sequence[JournalEntry],
    ):
        if len(journal_entries) == 0:
            return

        cur_date = journal_entries[0].timestamp
        prev_date = journal_entries[0].timestamp

        for i, entry in enumerate(journal_entries):

            cur_date = entry.timestamp

            if (
                cur_date.day > prev_date.day
                or cur_date.month > prev_date.month
                or cur_date.year > prev_date.year
            ):

                balanced_transactions = list(
                    filter(lambda t: t.balance, journal_entries[i - 1].transactions)
                )

                lines = list(
                    map(
                        lambda t: f"{cur_date.strftime('%Y-%m-%d')} balance {t.account} {t.balance} {t.currency}",
                        balanced_transactions,
                    )
                )
                lines.append("\n")

                print("\n".join(lines), file=output_stream.stream, end="")

            self.write_one_generic_to_beancount(output_stream, entry)

            prev_date = cur_date

    def export(
        self, output_stream: StreamInfo, journal_entries: Sequence[JournalEntry]
    ):
        self.write_generic_to_beancount(output_stream, journal_entries)
