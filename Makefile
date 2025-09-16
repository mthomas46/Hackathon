PYTHON ?= python3

.PHONY: test docs docs-serve timeline

test:
	$(PYTHON) -m pytest -q

docs:
	mkdocs build -q

docs-serve:
	mkdocs serve -a 0.0.0.0:8000

timeline:
	$(PYTHON) scripts/generate_timeline.py
