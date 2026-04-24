.PHONY: help install setup up down logs test lint format migrations

help:
	@echo "FlowOS Backend Commands"
	@echo "======================="
	@echo "make install      - Install dependencies"
	@echo "make setup        - Setup dev environment (.env, alembic)"
	@echo "make up           - Start docker-compose"
	@echo "make down         - Stop docker-compose"
	@echo "make logs         - Tail docker logs"
	@echo "make migrate      - Run alembic migrations"
	@echo "make test         - Run pytest"
	@echo "make lint         - Run ruff"
	@echo "make format       - Format code with black"
	@echo "make verify       - Verify build sanity"

install:
	pip install -r requirements.txt

setup: install
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@if [ ! -d alembic/versions ]; then mkdir -p alembic/versions; fi

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f app

migrate:
	alembic upgrade head

test:
	pytest tests/ -v

lint:
	ruff check app/

format:
	black app/

verify:
	python verify_build.py
