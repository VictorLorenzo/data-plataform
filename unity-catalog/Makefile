build:
	docker compose build

build-no-cache:
	docker compose build --no-cache

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

# make logs-list SERVICE=service-name
logs-list:
	docker compose logs -f --tail 40 ${SERVICE}

# make console SERVICE=service-name
console:
	docker compose exec ${SERVICE} sh
