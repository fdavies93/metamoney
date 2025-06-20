from abc import ABC, abstractmethod
from typing import Sequence

from metamoney.models.config import StreamInfo
from metamoney.models.transactions import JournalEntry


class AbstractExporter(ABC):

    @abstractmethod
    def export(
        self, output_stream: StreamInfo, journal_entries: Sequence[JournalEntry]
    ):
        pass
