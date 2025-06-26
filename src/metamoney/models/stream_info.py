from dataclasses import dataclass
from typing import TextIO


@dataclass
class StreamInfo:
    stream: TextIO
    name: str
