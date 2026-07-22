.PHONY: install run test lint evaluate docker

install:
	python -m pip install -r requirements-dev.txt

run:
	uvicorn app.main:app --reload

test:
	pytest

lint:
	ruff check .

evaluate:
	python evaluation/run.py

docker:
	docker compose up --build
