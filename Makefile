.PHONY: install dev test run docker

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest -q

run:
	uvicorn rag_starterkit.main:app --reload --port 8000

docker:
	docker compose up --build
