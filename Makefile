lint:
	black plaintextfeeds.py
	mypy --strict plaintextfeeds.py
	pylint plaintextfeeds.py

.PHONY: lint
