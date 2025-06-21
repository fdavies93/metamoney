from metamoney.exporters.beancount import BeancountExporter
from metamoney.exporters.exporter import AbstractExporter
from metamoney.models.exports import ExportFormat

def get_exporter(export_format: ExportFormat):
    match export_format:
        case ExportFormat.BEANCOUNT:
            return BeancountExporter()
