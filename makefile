## makefile automates the build and deployment for python projects

# type of project
PROJ_TYPE =		python

include ./zenbuild/main.mk

.PHONY:			testsqlite
testsqlite:
			make PY_SRC_TEST_PKGS=test_sqlite test
