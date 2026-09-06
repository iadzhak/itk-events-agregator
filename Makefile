.PHONY: dev lint lint-fix test

dev:
	uv run uvicorn app.main:app --reload

lint:
	ruff check --fix