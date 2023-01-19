from abc import ABC, abstractmethod
from typing import NamedTuple

#base classes
class BaseEventBus(ABC):
    @abstractmethod
    def publish(self, integration_event):
        pass

class BaseHandler(ABC):
    supported_commands: list
    
    @abstractmethod
    def handle(self, command):
        pass
    
class BaseMediator(ABC):    
    @abstractmethod
    def handle(self, command):
        pass
    
    @abstractmethod
    def send(self, domain_event):
        pass
    
class BaseRepository(ABC):
    @abstractmethod
    def create(self, model):
        pass
    
    @abstractmethod
    def read(self, id):
        pass

    @abstractmethod
    def update(self, id, model):
        pass
    
    @abstractmethod
    def delete(self, id):
        pass    

#domain model
class Product:
    def __init__(self, id: str, name: str, price: float, inventory: int, category: str) -> None:
        self.id = id
        self.name = name
        self.price = price
        self.inventory = inventory
        self.category = category

#domain events
class ProductCreated(NamedTuple):
    name: str