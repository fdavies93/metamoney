import metamoney.importers.cathay as cathay
from metamoney.importers.cathay import CathayCsvImporter
from metamoney.importers.importer import AbstractImporter
from metamoney.models.data_sources import DataSourceFormat, DataSourceInstitution
from metamoney.registry import importers

def get_importer(institution: str, data_format: str):
    def filter_fn(importer: AbstractImporter) -> bool:
        return importer.data_institution() == institution and importer.data_format() == data_format
    importer_list = importers.filter_services(filter_fn)
    if not importer_list:
        raise ValueError()
    return importer_list[0]
