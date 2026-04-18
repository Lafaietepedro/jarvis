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

.PHONY: ui-state
ui-state:
	cd backend && python -m app.cli ui-state

.PHONY: desktop-launcher
desktop-launcher:
	cd backend && python -m app.cli desktop-launcher

.PHONY: dependencies
dependencies:
	cd backend && python -m app.cli dependencies

.PHONY: install-dependencies
install-dependencies:
	cd backend && python -m app.cli install-dependencies

.PHONY: confirm-checkpoint
confirm-checkpoint:
	cd backend && python -m app.cli confirm-checkpoint "$(ID)"

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
