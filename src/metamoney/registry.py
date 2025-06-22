from typing import Sequence, TypeVar, Callable
from metamoney.importers.importer import AbstractImporter
from metamoney.exporters.exporter import AbstractExporter

T = TypeVar("T")

class Registry[T]():

    def __init__(self):
        self.services = {}
    
    def register(self, service: T):
        self.services[service.__class__] = service

    def get_service(self, class_name: str) -> T | None:
        return self.services.get(class_name)

    def filter_services(self, filter_fn: Callable[[T],bool]) -> Sequence[T]:
        return list(filter(filter_fn, self.services.values()))

    def unregister(self, service_type: type):
        # May crash if service doesn't exist, but that's probably fine
        del self.services[service_type]

importers = Registry[AbstractImporter]()
exporters = Registry[AbstractExporter]()
