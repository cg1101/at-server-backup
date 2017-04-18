#!/bin/bash

createdb -U postgres atdb_test
psql -c "create schema q" atdb_test
