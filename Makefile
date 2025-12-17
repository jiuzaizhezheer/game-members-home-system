.PHONY: install dev-install test format lint run

install:
	poetry install

dev-install:
	poetry install --with dev

test:
	poetry run pytest

format:
	poetry run black .
	poetry run isort .

lint:
	poetry run flake8 .

run:
	poetry run uvicorn app.main:app --reload

migrate:
	poetry run alembic upgrade head

makemigrations:
	poetry run alembic revision --autogenerate -m "Auto migration"