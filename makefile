# requires setuptools build twine
# makefile should be tab indented !

name = mplchart

build: FORCE
	python extras/process-readme.py
	python -m build --wheel .

dump: FORCE
	unzip -l dist/*.whl

install: FORCE
	python setup.py develop

remove: FORCE
	python setup.py develop -u

upload: FORCE
#	twine upload --repository testpypi dist/*
	twine upload dist/*

FORCE:

