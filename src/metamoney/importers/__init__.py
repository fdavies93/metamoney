import metamoney.importers.cathay as cathay
from metamoney.importers.cathay import CathayCsvImporter
from metamoney.models.data_sources import DataSourceFormat, DataSourceInstitution

def get_importer(institution: DataSourceInstitution, format: DataSourceFormat):
    match (institution):
        case DataSourceInstitution.CATHAY_BANK_TW:
            return cathay.get_importer(format)
