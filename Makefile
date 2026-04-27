.PHONY: dev test build

dev:
	@echo 'Starting web + server in separate terminals is recommended.'
	@echo 'Server: cd server && uvicorn trace_replay_server.app:app --reload --app-dir src'
	@echo 'Web: cd web && npm run dev'

test:
	cd sdk && PYTHONPATH=src pytest
	cd server && PYTHONPATH=src:../sdk/src pytest

build:
	cd sdk && python -m build
	cd server && python -m build
	cd web && npm run build
