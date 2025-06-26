from dataclasses import dataclass
from enum import StrEnum

from metamoney.models.stream_info import StreamInfo


class DataSourceInstitution(StrEnum):
    CATHAY_BANK_TW = "cathay_tw"


class DataSourceFormat(StrEnum):
    CSV = "csv"


@dataclass
class DataSource:
    institution: str
    format: str
    stream: StreamInfo
