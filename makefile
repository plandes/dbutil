## makefile automates the build and deployment for python projects


## Build system
#
PROJ_TYPE =		python
PROJ_MODULES=		git python-doc python-doc-deploy python-resources


## Includes
#
include ./zenbuild/main.mk


## Targets
#
.PHONY:			testdeps
testdeps:		deps
			pip install jsonpickle
