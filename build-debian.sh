#!/bin/bash
rm -rf "./deb_dist"
echo "initd" > .target
python setup.py --command-packages=stdeb.command bdist_deb
rm .target
