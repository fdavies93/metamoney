import sys
from dataclasses import dataclass
from typing import Iterable, Sequence, TextIO

from metamoney.exporters import BeancountExporter
from metamoney.exporters.exporter import AbstractExporter
from metamoney.importers import CathayCsvImporter
from metamoney.importers.importer import AbstractImporter
from metamoney.mappers.mapper import Mapping
from metamoney.models.stream_info import StreamInfo
from metamoney.registry import Registry
from metamoney.utils import get_config_module


class AppData:
    def __init__(self):
        config = get_config_module()
        self.config = config
        self._importer_file_types: list[str] = []
        self._importer_institutions: list[str] = []
        self._exporter_file_types: list[str] = []
        self.importers = Registry[AbstractImporter]()
        self.exporters = Registry[AbstractExporter]()

        file_importers = [CathayCsvImporter()]
        for file_importer in file_importers:
            self.importers.register(file_importer)
            self._importer_file_types.append(file_importer.data_format())
            self._importer_institutions.append(file_importer.data_institution())

        file_exporters = [BeancountExporter()]
        for file_exporter in file_exporters:
            self.exporters.register(file_exporter)
            self._exporter_file_types.append(file_exporter.data_format())

        if config and isinstance(config.importers, Iterable):
            for file_importer in config.importers:
                if isinstance(file_importer, AbstractImporter):
                    existing_importer = self.get_importer(
                        file_importer.data_institution(), file_importer.data_format()
                    )
                    if existing_importer:
                        self.importers.unregister(existing_importer.__class__)
                    self.importers.register(file_importer)

        if config and isinstance(config.exporters, Iterable):
            for file_exporter in config.exporters:
                if isinstance(file_exporter, AbstractExporter):
                    existing_exporter = self.get_exporter(file_exporter.data_format())
                    if existing_exporter:
                        self.exporters.unregister(existing_exporter.__class__)
                    self.exporters.register(file_exporter)

        self.output_stream = StreamInfo(sys.stdout, "stdout")

    def get_importer(
        self, institution: str, data_format: str
    ) -> AbstractImporter | None:
        def filter_fn(importer: AbstractImporter) -> bool:
            return (
                importer.data_institution() == institution
                and importer.data_format() == data_format
            )

        importer_list = self.importers.filter_services(filter_fn)
        if not importer_list:
            return None
        return importer_list[0]

    def get_exporter(self, export_format: str) -> AbstractExporter | None:

        exporter_list = self.exporters.filter_services(
            lambda ex: ex.data_format() == export_format
        )
        if not exporter_list:
            return None
        return exporter_list[0]

    @property
    def importer_file_types(self) -> Sequence[str]:
        return self._importer_file_types

    @property
    def importer_institutions(self) -> Sequence[str]:
        return self._importer_institutions

    @property
    def exporter_file_types(self) -> Sequence[str]:
        return self._exporter_file_types

    @property
    def mappings(self) -> Sequence[Mapping]:
        mappings = []
        if not self.config or not self.config.mappings:
            return mappings
        mappings.extend(self.config.mappings)
        return mappings
