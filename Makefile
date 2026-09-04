.PHONY: dev lint lint-fix

dev:
	uv run uvicorn app.main:app --reload

lint:
	ruff check

lint-fix:
	ruff check --fix