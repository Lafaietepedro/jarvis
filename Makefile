VENV=.venv
PY=.

.PHONY: start
start:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: install
install:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
