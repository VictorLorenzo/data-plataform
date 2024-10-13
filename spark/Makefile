COMPOSE_FILE ?= docker-compose.yml

build:
	docker compose -f $(COMPOSE_FILE) build

build-service:
	docker compose -f $(COMPOSE_FILE) build ${SERVICE}

build-no-cache:
	docker compose -f $(COMPOSE_FILE) build --no-cache

build-service-no-cache:
	docker compose -f $(COMPOSE_FILE) build --no-cache ${SERVICE}

pull:
	docker compose -f $(COMPOSE_FILE) pull

up:
	docker compose -f $(COMPOSE_FILE) up -d

up-service:
	docker compose -f $(COMPOSE_FILE) up -d ${SERVICE} 

down:
	docker compose -f $(COMPOSE_FILE) down

down-service:
	docker compose -f $(COMPOSE_FILE) down ${SERVICE}

# make logs SERVICE=service-name
logs:
	docker compose -f $(COMPOSE_FILE) logs -f --tail 40 ${SERVICE}

# make network-create NETWORK=external-network-name
network-create:
	docker network create ${NETWORK}

# make network-remove NETWORK=external-network-name
network-remove:
	docker network rm ${NETWORK}

# make console SERVICE=service-name
console:
	docker compose -f $(COMPOSE_FILE) exec ${SERVICE} bash

# make spark-submit SCRIPT=csv_to_delta.py
spark-submit:
	docker compose -f $(COMPOSE_FILE) exec spark-master bash spark-submit /opt/spark-apps/${SCRIPT}

down-spark-ssh:
	docker compose -f docker-compose-ssh.yml down

up-spark-ssh:
	docker compose -f docker-compose-ssh.yml up -d

build-no-cache-spark-ssh:
	docker build -f Dockerfile_ssh .

build-spark-ssh:
	docker build --no-cache -f Dockerfile_ssh .