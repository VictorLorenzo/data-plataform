build:
	docker compose build

build-service:
	docker compose build ${SERVICE}

build-no-cache:
	docker compose build --no-cache

build-service-no-cache:
	docker compose build --no-cache ${SERVICE}

pull:
	docker compose pull

up:
	docker compose up -d

up-service:
	docker compose up -d ${SERVICE} 

down:
	docker compose down 

down-service:
	docker compose down ${SERVICE}

# make logs SERVICE=service-name
logs:
	docker compose logs -f --tail 40 ${SERVICE}

# make network-create NETWORK=external-network-name
network-create:
	docker network create ${NETWORK}

# make network-remove NETWORK=external-network-name
network-remove:
	docker network rm ${NETWORK}

# make console SERVICE=service-name
console:
	docker compose exec ${SERVICE} bash

server-list:
	docker compose exec spark-notebook jupyter server list

# make generate-synthetic-data USERS=200
generate-synthetic-data:
	docker compose exec spark-notebook papermill -p users ${USERS} work/synthetic-data-generator.ipynb work/synthetic-data-generator-output.ipynb

# make generate-synthetic-data-loop USERS=200 INTERVAL=3600
generate-synthetic-data-loop:
	nohup sh -c 'while true; do \
		$(MAKE) generate-synthetic-data USERS=${USERS}; \
		sleep ${INTERVAL}; \
	done' & echo $$! > generate-synthetic-data-loop.pid

# make stop-generate-synthetic-data-loop
stop-generate-synthetic-data-loop:
	@if [ -f generate-synthetic-data-loop.pid ]; then \
		kill `cat generate-synthetic-data-loop.pid`; \
		rm generate-synthetic-data-loop.pid; \
	else \
		echo "No running generate-synthetic-data-loop process found."; \
	fi