#!/bin/bash
rm .coverage
flake8 taiga
nosetests --with-coverage --cover-package=taiga