from sys import path
from os import getcwd
path.append(getcwd() + "/src/")
print(path)
import application
import infrastructure
import domain
from unittest.mock import MagicMock

#command handler tests
class TestCreateProductCommandHandler:
    def test_handle_creates_product(self):
        #arrange
        product_repo: infrastructure.ProductSqlAlchemyRepository = infrastructure.ProductSqlAlchemyRepository()
        product_repo.create = MagicMock()
        create_product_command_handler: application.CreateProductCommandHandler = application.CreateProductCommandHandler(product_repository=product_repo)
        command: application.CreateProductCommand = application.CreateProductCommand("name", 5.43, 100, "category")
        
        #act
        product_id: str = create_product_command_handler.handle(command)
        
        #assert
        assert product_id != ""
        product_repo.create.assert_called_once()
        