.PHONY: test test-verbose

test:
	pytest tests

test-verbose:
	pytest tests -v
