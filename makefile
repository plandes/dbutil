## makefile automates the build and deployment for python projects


## Build system
#
PROJ_TYPE =		python
PROJ_MODULES=		python/test python/doc python/package python/deploy
PY_DOC_DIST_NAME =	dbutil


## Includes
#
include ./zenbuild/main.mk
