#!/usr/bin/env bash

FORCE_APP_MODE=true;
ROOT_FOLDER="`(cd $(dirname $BASH_SOURCE) ; cd ../ ; pwd)`"
export PYTHONPATH=$PYTHONPATH:$ROOT_FOLDER
py.test
