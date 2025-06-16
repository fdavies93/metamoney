from metamoney.importers.importer import AbstractImporter
import logging

from metamoney.models.data_sources import DataSource

class CathayImporter(AbstractImporter):
    logger = logging.getLogger("CathayImporter")

    def retrieve(self) -> DataSource:
        pass
