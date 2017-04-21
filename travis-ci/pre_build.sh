#!/bin/bash

# /home/travis/build/Appen/at_server

CLIENT_DIR=$HOME/build/Appen/appen_next_client

git clone --depth=50 --branch=qa git@github.com:Appen/appen_next_client.git ${CLIENT_DIR}
pushd ${CLIENT_DIR}
npm install
bower install
pushd lib
for i in ../bower_components/*; do
	ln -sf "$i"
done
ln -sf jquery jquery-2.2.3
popd
mkdir -p app build
ln -sf "../build/dev/index.html" app
ln -sf "../build/dev/static" app
popd
ln -sf "$CLIENT_DIR/app/index.html" app
ln -sf "$CLIENT_DIR/app/static" app
ls -l app
