#!/bin/bash

function quit {
    exit $1
}

test ! -e .coverage || rm .coverage
flake8 taiga || quit 1
nosetests --with-coverage --cover-package=taiga || quit 1
quit 0