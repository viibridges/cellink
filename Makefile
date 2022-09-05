test:
	pytest -s --disable-warnings tests/test_common
	pytest -s --disable-warnings tests/test_quantum
	pytest -s --disable-warnings tests/test_exception
	pytest -s --disable-warnings tests/test_static