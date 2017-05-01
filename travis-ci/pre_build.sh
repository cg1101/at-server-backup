#!/bin/bash

# /home/travis/build/Appen/at_server

CLIENT_DIR=$HOME/build/Appen/appen_next_client

git clone --depth=50 --branch=qa git@github.com:Appen/appen_next_client.git ${CLIENT_DIR}

pushd ${CLIENT_DIR} >/dev/null
echo -e "\033[0;32msetting up client repo in \033[1;34m$PWD\033[0m"
npm install    >/dev/null 2>&1
bower install  >/dev/null 2>&1

# create symlinks inside lib
pushd lib >/dev/null
echo -ne "\033[0;32mcreating symlinks inside \033[1;34m$PWD\033[0m ... "
for i in ../bower_components/*; do
	ln -sf "$i"
done
ln -sf jquery jquery-2.2.3
popd >/dev/null
# double check result
echo done
echo "Content of $PWD/lib"
ls -l $PWD/lib
echo

# prepare app folder
echo -e "\033[0;32msetting up folders for \033[1;34mapp, build\033[0m"
mkdir -p app build/dev/static
echo "<h1>Index</h1>" > build/dev/index.html
pushd build/dev/static >/dev/null
ln -sf ../../../lib
ln -sf ../../../src/img
popd >/dev/null
pushd app >/dev/null
echo -ne "\033[0;32msetting up symlinks in \033[1;34m$PWD\033[0m ... "
ln -sf ../build/dev/index.html
ln -sf ../build/dev/static
popd >/dev/null
echo done
echo "Content of $PWD/app"
ls -l $PWD/app

echo "Content of $PWD/build"
ls -l $PWD/build

echo "Content of $PWD"
ls -l $PWD
echo
gem install sass
echo "sass has been installed as `which sass`"
#npm rebuild node-sass
grunt

popd >/dev/null
echo -ne "\033[0;32msetting up server repo: \033[1;34m$PWD\033[0m ... "
ln -sf "${CLIENT_DIR}/app/index.html" app
ln -sf "${CLIENT_DIR}/app/static" app
echo done
echo "Content of $PWD/app"
ls -l $PWD/app
echo
echo "app/index.html => $(readlink app/index.html)"
echo "app/static => $(readlink app/static)"
ls -l app/index.html $(readlink app/index.html) $(readlink $(readlink app/index.html))
ls -l app/static $(readlink app/static) $(readlink $(readlink app/static))
cat app/index.html
ls -l app/static
if [ -e "app/index.html" ]; then
	echo "app/index.html exists"
else
	echo "app/index.html not found"
fi