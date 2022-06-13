export SERVICE_ADMIN_DOCKER_IMAGE := $(shell jq -r '.dockerImage.admin' ${DOCKER_IMAGES})
export SERVICE_API_DOCKER_IMAGE := $(shell jq -r '.dockerImage.api' ${DOCKER_IMAGES})
export SERVICE_DATASETS_WORKER_DOCKER_IMAGE := $(shell jq -r '.dockerImage.datasetsWorker' ${DOCKER_IMAGES})
export SERVICE_REVERSE_PROXY_DOCKER_IMAGE := $(shell jq -r '.dockerImage.reverseProxy' ${DOCKER_IMAGES})
export SERVICE_SPLITS_WORKER_DOCKER_IMAGE := $(shell jq -r '.dockerImage.splitsWorker' ${DOCKER_IMAGES})

.PHONY: down
down:	
	docker-compose -f $(DOCKER_COMPOSE) down -v --remove-orphans

.PHONY: up
up:	
	docker-compose -f $(DOCKER_COMPOSE) up -d
