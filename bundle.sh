#!/bin/bash

BUNDLE=../gnx_app_bundle.zip

if [ -e "$BUNDLE" ]; then
	echo -n "Removing bundle file from previous build ... "
	rm "$BUNDLE"
	echo "done"
fi

echo -n "Building new bundle file ... "
# set -o xtrace
zip -r "$BUNDLE" . -x venv\* ./.\* \*__pycache\* \*.pyc dumpstr dump_str\* ./bundle.sh ./doc/\* >/dev/null
zip -r "$BUNDLE" ./.ebextensions >/dev/null
echo "done"

echo "Checking eb environment ... "

envs=$(eb list)
current_env=$(echo "$envs"|awk -F" " '$1=="*"{print $2}')

if [ -z "${current_env}" ]; then
	echo -e "\033[1;36mNote:\033[0m You don't have a default environment, please use \`eb use\` to set one."
else
	echo -e "\033[1;36mNote:\033[0m Your current environment is \033[1;32m${current_env}\033[0m, please make sure this is correct before you run \`eb deploy\`."
fi