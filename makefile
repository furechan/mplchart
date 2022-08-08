# for use in windows only ...
# requires setuptools build twine
# makefile should be tab indented !

version = 0.0.1
name = stockchart

dist: FORCE
	python -m build --wheel .

dump: FORCE
	unzip -l dist/*.whl

install: FORCE
	python setup.py develop

remove: FORCE
	python setup.py develop -u

upload: FORCE
	twine upload --repository testpypi dist/*

FORCE:

