#!/usr/bin/env bash

#clean dist
rm -fr dist
#build
python setup.py sdist bdist_wheel

#upload
twine upload --repository pypi dist/*