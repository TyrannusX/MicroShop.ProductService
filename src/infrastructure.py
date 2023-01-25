import pika
import logging
from domain import BaseRepository, BaseEventBus, Product
from sqlalchemy.orm import declarative_base, Session, sessionmaker
from sqlalchemy import Column, Integer, Float, String, create_engine
import json
import config

#ORM
Base = declarative_base()

class PersistedProduct(Base):
    __tablename__ = "products"
    
    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Float, nullable=False)
    inventory = Column(Integer, nullable=False)
    category = Column(String, nullable=False)

engine = create_engine(config.DATABASE_URI, echo=True, future=True)
session_maker = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

#repositories
class ProductSqlAlchemyRepository(BaseRepository):
    def create(self, model: Product):
        session = session_maker()
        persisted_product = PersistedProduct()
        persisted_product.id = model.id
        persisted_product.name = model.name
        persisted_product.price = model.price
        persisted_product.inventory = model.inventory
        persisted_product.category = model.category
        session.add(persisted_product)
        session.commit()
        session.close()
    
    def read(self, id):
        session = session_maker()
        persisted_product: PersistedProduct = session.query(PersistedProduct).filter_by(id=id).first()
        domain_preoduct = Product(persisted_product.id, persisted_product.name, persisted_product.price, persisted_product.inventory, persisted_product.category)
        session.close()
        return domain_preoduct

    def update(self, id, model):
        pass
    
    def delete(self, id):
        pass
        
#service buses
class RabbitMqEventBus(BaseEventBus):
    def __init__(self) -> None:
        self.logger = logging.getLogger("application")
        
    def publish(self, integration_event):
        self.logger.info(f"Publishing integration event {type(integration_event)}")
        self.logger.info(f"Message Broker URI: {config.MESSAGE_BROKER_URI}")
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=config.MESSAGE_BROKER_URI, port=5672))
        channel = connection.channel()
        channel.queue_declare(queue=str(type(integration_event).__name__))
        channel.basic_publish(exchange="", routing_key=str(type(integration_event).__name__), body=json.dumps(integration_event))
        self.logger.info(f"Published integration event {type(integration_event)}")