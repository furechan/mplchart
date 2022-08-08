# for use in windows only ...
# requires setuptools build twine
# makefile should be tab indented !

version = 0.0.1
name = stockchart

dist: FORCE
#	python -m build .
#	python setup.py sdist --formats=zip
#	python setup.py bdist_wheel
	python -m build --wheel .

dump: FORCE
	tar -tvf dist/$(name)-$(version).tar.gz
	unzip -l dist/*.whl

install: FORCE
	python setup.py develop

remove: FORCE
	python setup.py develop -u

upload: FORCE
	twine upload --repository testpypi dist/*

FORCE:

