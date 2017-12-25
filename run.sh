#!/bin/sh -x

# prerequisite
# git clone git@github.com:uchan-nos/pykintone.git
# pip3 install pyyaml pytz tzlocal requests

PYTHONPATH=$PWD/../pykintone python3 src/main.py
