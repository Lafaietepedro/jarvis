VENV=.venv
PY=.

.PHONY: start
start:
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

.PHONY: panel
panel:
	cd backend && python -m app.cli panel

.PHONY: checkpoints
checkpoints:
	cd backend && python -m app.cli checkpoints

.PHONY: ask
ask:
	cd backend && python -m app.cli ask "$(TEXT)"

.PHONY: chat
chat:
	cd backend && python -m app.cli chat

.PHONY: test
test:
	cd backend && python -m unittest discover -s tests

.PHONY: install
install:
	cd backend && python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
