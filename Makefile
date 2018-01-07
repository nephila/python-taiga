.PHONY: clean-pyc clean-build docs deb

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "testall - run tests on every Python version with tox"
	@echo "coverage - check code coverage quickly with the default Python"
	@echo "release - package and upload a release"
	@echo "sdist - package"
	@echo "deb - build debian package"

clean: clean-build clean-pyc

clean-build:
	python setup.py clean --all
	rm -fr docs/build/
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

lint:
	flake8 taiga tests

test:
	python setup.py test

test-all:
	tox

docs:
	cd docs && make html

coverage:
	coverage erase
	coverage run setup.py test
	coverage report -m

release: clean
	python setup.py sdist bdist_wheel
	twine upload dist/*

sdist: clean
	python setup.py sdist
	ls -l dist

deb:
	debuild -us -uc -b
