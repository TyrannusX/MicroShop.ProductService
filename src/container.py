from dependency_injector import containers, providers
from infrastructure import ProductSqlAlchemyRepository, RabbitMqEventBus, Base

#dependency injection container
class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=["application"])
    
    #repositories
    product_repository = providers.Factory(ProductSqlAlchemyRepository)
    
    #event broker
    event_bus = providers.Factory(
        RabbitMqEventBus
    )