.PHONY: backend frontend test build

backend:
	uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

frontend:
	npm run dev

test:
	uv run pytest
	npm run build

build:
	npm run build
