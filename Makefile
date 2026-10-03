.PHONY: dev test lint format build docker-up

dev:
	uvicorn saath.api.main:app --reload --port 8000

test:
	pytest tests -v

lint:
	ruff check api/saath
	mypy --strict api/saath/domain api/saath/application

format:
	ruff format api/saath

docker-up:
	docker compose up --build
