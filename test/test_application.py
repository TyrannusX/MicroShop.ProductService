import sys
sys.path.append('../src')
import application
import infrastructure
import domain
from unittest import mock

#command handler tests
class TestCreateProductCommandHandler:
    def test_handle_creates_product(self):
        #arrange
        def mocked_repository_create(self, model) -> domain.Product:
            return model
        
        with mock.patch.object(infrastructure.ProductSqlAlchemyRepository, "create", new=mocked_repository_create):
        
            create_product_command_handler: application.CreateProductCommandHandler = application.CreateProductCommandHandler(product_repository=infrastructure.ProductSqlAlchemyRepository())
            
            command: application.CreateProductCommand = application.CreateProductCommand("name", 5.43, 100, "category")
            
            #act
            product_id: str = create_product_command_handler.handle(command)
            
            #assert
            assert product_id != ""
        
        