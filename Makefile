all: lint test

lint:
	python3 -m pylint ysp4000 tests

test:
	python3 -m pytest tests
