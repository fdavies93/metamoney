from dataclasses import dataclass
import logging

@dataclass
class AppConfig:
    logger: logging.Logger
