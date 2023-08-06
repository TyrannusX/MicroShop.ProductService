from uuid import uuid4
from dependency_injector.wiring import Provide, inject
import requests
from domain import BaseHandler, BaseRepository, BaseEventBus, ProductCreated, Product, BaseMediator
from typing import NamedTuple
from container import Container
import logging
from flask import Flask, jsonify, request, Blueprint, Request
from authlib.oauth2.rfc7662 import IntrospectTokenValidator
from authlib.integrations.flask_oauth2 import ResourceProtector
import config

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
        self.events_to_emit = []
        self.logger = logging.getLogger("application")
        pass
    
    def handle(self, create_product_command: CreateProductCommand) -> str:
        self.logger.info("Entering create product command handler")
        new_id = str(uuid4())
        product_to_create = Product(new_id, create_product_command.name, create_product_command.price, create_product_command.inventory, create_product_command.category)
        self.product_repository.create(product_to_create)
        product_created = ProductCreated(product_to_create.id, product_to_create.name, product_to_create.price)
        self.events_to_emit.append(product_created)
        self.logger.info("Finished create product command handler")
        return new_id


class ProductCreatedIntegrationEvent(NamedTuple):
    name: str


class ProductCreatedEventHandler(BaseHandler):
    @inject
    def __init__(self, event_bus: BaseEventBus = Provide[Container.event_bus]) -> None:
        self.supported_commands = [ProductCreated]
        self.events_to_emit = []
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
        self.events_to_emit = []
        self.logger = logging.getLogger("application")
        
    def handle(self, command: GetProductsQuery) -> Product:
        self.logger.info("Entering get products query handler")
        product: Product = self.product_repository.read(command.id)
        self.logger.info("Finished get products query handler")
        return product

#mediator
class Mediator(BaseMediator):
    def handle(self, command):
        for handler in BaseHandler.__subclasses__():
            handler_instance = handler()
            if type(command) in handler_instance.supported_commands:
                result = handler_instance.handle(command)
                if len(handler_instance.events_to_emit) > 0:
                    for event in handler_instance.events_to_emit:
                        self.send(event)
                    handler_instance.events_to_emit.clear()
                return result
            
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

#JWT Validator
class MyJWTValidator(IntrospectTokenValidator):
    def introspect_token(self, token_string):
        url = config.ISSUER_BASE_URL + '/oauth2/introspect'
        data = {'token': token_string, 'token_type_hint': 'access_token'}
        auth = (config.CLIENT_ID, config.CLIENT_SECRET)
        resp = requests.post(url, data=data, auth=auth)
        return resp.json()

authenticate_this = ResourceProtector()
authenticate_this.register_token_validator(MyJWTValidator())

#product controller/blueprint
product_controller_blueprint = Blueprint('product_controller', __name__)

logger = logging.getLogger("application")

@product_controller_blueprint.route('/products', methods=['POST'])
@authenticate_this()
@inject
def create_product():
    logger.info("Create product invoked")
    create_product_command: CreateProductCommand = create_product_deserializer(request)
    mediator = Mediator()
    mediator_result = mediator.handle(create_product_command)
    logger.info("Finished create product")
    return jsonify(create_product_serializer(mediator_result))

@product_controller_blueprint.route('/products/<product_id>', methods=['GET'])
@authenticate_this()
@inject
def get_product(product_id: str):
    logger.info("Get product invoked")
    get_products_query: GetProductsQuery = GetProductsQuery(product_id)
    mediator = Mediator()
    mediator_result = mediator.handle(get_products_query)
    logger.info("Finished get product")
    return product_serializer(mediator_result)

#flask application with OAuth2 integration
container = Container()
app = Flask(__name__)
app.logger.setLevel(logging.DEBUG)
app.container = container
app.register_blueprint(product_controller_blueprint)