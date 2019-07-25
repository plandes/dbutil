## makefile automates the build and deployment for python projects

# type of project
PROJ_TYPE =		python

PY_SRC_TEST_FILTER =	$(wildcard $(PY_SRC_TEST)/*_flymake.py $(PY_SRC_TEST)/config.py)

include ./zenbuild/main.mk

.PHONY:	testsqlite
testsqlite:
	make PY_SRC_TEST_PKGS=test_sqlite.TestSqlLite test
