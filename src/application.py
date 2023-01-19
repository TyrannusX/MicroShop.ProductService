from uuid import uuid4
from dependency_injector.wiring import Provide, inject
from domain import BaseHandler, BaseRepository, BaseEventBus, ProductCreated, Product, BaseMediator
from typing import NamedTuple
from container import Container
import logging
from flask import Flask, jsonify, request, Blueprint, Request

#handlers and mediator
class CreateProductCommand(NamedTuple):
    name: str
    price: float
    inventory: int
    category: str


class CreateProductCommandHandler(BaseHandler):
    @inject
    def __init__(self, product_repository: BaseRepository = Provide[Container.product_repository]) -> None:
        self.product_repository = product_repository
        self.supported_commands = [CreateProductCommand]
        self.mediator = Mediator()
        self.logger = logging.getLogger("application")
        pass
    
    def handle(self, create_product_command: CreateProductCommand) -> str:
        self.logger.info("Entering create product command handler")
        new_id = str(uuid4())
        product_to_create = Product(new_id, create_product_command.name, create_product_command.price, create_product_command.inventory, create_product_command.category)
        self.product_repository.create(product_to_create)
        product_created = ProductCreated(product_to_create.name)
        self.mediator.send(product_created)
        self.logger.info("Finished create product command handler")
        return new_id


class ProductCreatedIntegrationEvent(NamedTuple):
    name: str


class ProductCreatedEventHandler(BaseHandler):
    @inject
    def __init__(self, event_bus: BaseEventBus = Provide[Container.event_bus]) -> None:
        self.supported_commands = [ProductCreated]
        self.event_bus = event_bus
        self.logger = logging.getLogger("application")
    
    def handle(self, command: ProductCreated):
        self.logger.info("Entering product created domain event handler")
        self.event_bus.publish(command)
        self.logger.info("Finished product created domain event handler")



class GetProductsQuery(NamedTuple):
    id: str


class GetProductsQueryHandler(BaseHandler):
    @inject
    def __init__(self, product_repository: BaseRepository = Provide[Container.product_repository]) -> None:
        self.product_repository = product_repository
        self.supported_commands = [GetProductsQuery]
        self.logger = logging.getLogger("application")
        
    def handle(self, command: GetProductsQuery) -> Product:
        self.logger.info("Entering get products query handler")
        product: Product = self.product_repository.read(command.id)
        self.logger.info("Finished get products query handler")
        return product
    
class Mediator(BaseMediator):
    def handle(self, command):
        for handler in BaseHandler.__subclasses__():
            handler_instance = handler()
            if type(command) in handler_instance.supported_commands:
                return handler_instance.handle(command)
            
    def send(self, domain_event):
        for handler in BaseHandler.__subclasses__():
            handler_instance = handler()
            if type(domain_event) in handler_instance.supported_commands:
                handler_instance.handle(domain_event)

#serializers
def create_product_deserializer(request: Request) -> CreateProductCommand:
    json = request.get_json()
    create_product_command = CreateProductCommand(
        json["name"],
        float(json["price"]),
        int(json["inventory"]),
        json["category"]
    )
    return create_product_command

def create_product_serializer(new_id: str):
    return {
        "id": new_id
    }
    
def product_serializer(product: Product):
    return {
        "id": product.id,
        "name": product.name,
        "price": product.price,
        "inventory": product.inventory,
        "category": product.category
    }

#product controller/blueprint
product_controller_blueprint = Blueprint('product_controller', __name__)

logger = logging.getLogger("application")

@product_controller_blueprint.route('/products', methods=['POST'])
@inject
def create_product():
    logger.info("Create product invoked")
    create_product_command: CreateProductCommand = create_product_deserializer(request)
    mediator = Mediator()
    mediator_result = mediator.handle(create_product_command)
    logger.info("Finished create product")
    return jsonify(create_product_serializer(mediator_result))

@product_controller_blueprint.route('/products/<product_id>', methods=['GET'])
@inject
def get_product(product_id: str):
    logger.info("Get product invoked")
    get_products_query: GetProductsQuery = GetProductsQuery(product_id)
    mediator = Mediator()
    mediator_result = mediator.handle(get_products_query)
    logger.info("Finished get product")
    return product_serializer(mediator_result)

#flask application
container = Container()
app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
app.container = container
app.register_blueprint(product_controller_blueprint)
