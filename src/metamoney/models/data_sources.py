from enum import Enum, StrEnum, auto
from dataclasses import dataclass

from metamoney.models.config import StreamInfo

class DataSourceInstitution(StrEnum):
    CATHAY_BANK_TW = "cathay_tw"

class DataSourceFormat(StrEnum):
    CSV = "csv"

@dataclass
class DataSource:
    institution: DataSourceInstitution
    format: DataSourceFormat
    stream: StreamInfo
