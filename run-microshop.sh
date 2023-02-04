docker run -d --hostname product-service --name product-service --network microshop-network -p 5000:5000 microshop-product-service:latest
docker run -d --hostname my-rabbit --name rabbit-mq-server --network microshop-network -p 5672:5672 -p 15672:15672 rabbitmq:management 
docker run -d --hostname my-keycloak --name keycloak-server --network microshop-network -p 8082:8080 -e KEYCLOAK_ADMIN=admin -e KEYCLOAK_ADMIN_PASSWORD=admin -v keycloak-volume quay.io/keycloak/keycloak:20.0.3 start-dev
