## makefile automates the build and deployment for python projects

# type of project
PROJ_TYPE =		python
PROJ_MODULES=	git python-doc

include ./zenbuild/main.mk

.PHONY:			testparse
testparse:
			make PY_SRC_TEST_PAT=test_parse.py test

.PHONY:			testsqlite
testsqlite:
			make PY_SRC_TEST_PAT=test_sqlite.py test
