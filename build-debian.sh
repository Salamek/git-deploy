#!/bin/bash
rm -rf "./deb_dist"
python setup-init.py --command-packages=stdeb.command bdist_deb
