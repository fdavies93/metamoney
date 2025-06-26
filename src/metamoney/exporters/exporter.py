from abc import ABC, abstractmethod
from typing import Sequence

from metamoney.models.stream_info import StreamInfo
from metamoney.models.transactions import JournalEntry


class AbstractExporter(ABC):

    @staticmethod
    @abstractmethod
    def data_format() -> str:
        pass

    @abstractmethod
    def export(
        self, output_stream: StreamInfo, journal_entries: Sequence[JournalEntry]
    ):
        pass
