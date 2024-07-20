all: lint tests

lint:
	PYTHONPATH=. ./.venv/bin/pylint ysp4000 tests

test:
	PYTHONPATH=. ./.venv/bin/pytest tests