DC = docker compose
REDIS_COMPOSE_FILE = compose_files/redis.yaml

.PHONY: redis
redis: 
	${DC} -f ${REDIS_COMPOSE_FILE} up -d

.PHONY: redis-down
redis-down:
	${DC} -f ${REDIS_COMPOSE_FILE} down

.PHONY: test-app
test-app:
	uvicorn app:app --reload