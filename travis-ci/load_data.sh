#!/bin/bash

DATA_DIR=$(cd `dirname ${0}`;pwd)/data

for i in ${DATA_DIR}/*.sql; do
	echo "loading data from $i ...";
	psql <"$i" atdb_test
done
