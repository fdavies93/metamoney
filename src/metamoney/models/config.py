from dataclasses import dataclass
from typing import TextIO
import logging

@dataclass
class AppConfig:
    logger: logging.Logger

@dataclass
class StreamInfo:
    stream: TextIO
    name: str
