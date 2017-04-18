#!/bin/bash

createdb -U postgres
psql -c "create schema q"
