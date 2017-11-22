#!/usr/bin/env bash

ROOT_FOLDER="`(cd $(dirname $BASH_SOURCE) ; cd ../ ; pwd)`"
export PYTHONPATH=$PYTHONPATH:$ROOT_FOLDER
py.test
