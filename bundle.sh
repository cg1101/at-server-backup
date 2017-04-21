#!/bin/bash

function abspath() {
	python -c 'import os,sys;print os.path.abspath(sys.argv[1])' $1
}

function usage() {
	echo "Usage: ${0##*/} { dev | [ prod ] }" >&2
	exit 2
}

if (( $# > 1 )); then usage; fi

if (( $# == 0 )); then
	BUILD_TYPE='prod'
elif [ "$1" = "prod" ]; then
	BUILD_TYPE='prod'
elif [ "$1" = "dev" ]; then
	BUILD_TYPE='dev'
else
	echo "${0##*/}: invalid build type: $1" >&2
	usage;
fi

echo -e "Starting building bundle of type \033[1;32m${BUILD_TYPE}\033[0m"

BUNDLE=$(abspath ../gnx_app_bundle.zip)

if [ -e "$BUNDLE" ]; then
	echo -n "Removing bundle file from previous build ... "
	rm "$BUNDLE"
	echo "done"
fi

echo -n "Building new bundle file ... "

# set -o xtrace
if [ -e "exclude.lst" ]; then
	zip -r "$BUNDLE" . -x@exclude.lst >/dev/null
else
	zip -r "$BUNDLE" . -x venv\* ./.\* \*__pycache\* \*.pyc ./doc/\* ./bundle.sh >/dev/null
	zip -r "$BUNDLE" ./.ebextensions -x \*~ >/dev/null
fi
echo "done"

if [ "${BUILD_TYPE}" = "prod" ]; then
	# build client files for prod
	if [ ! -e "app/index.html" ]; then
		echo "${0##*/}: can't see index.html in app folder" >&2
		exit 1
	fi
	link=$(readlink app/index.html)
	if [ "${link:0:1}" = "/" ]; then
		client_repo_dir=$(dirname "$link")
	else
		client_repo_dir=$(dirname "app/$link")
	fi
	client_repo_dir=$(abspath "$client_repo_dir/..")
	while :; do
		read -t 2 -p "Please input client repo path (Enter for $client_repo_dir) -> "
		if [ -z "$REPLY" ]; then
			echo
			break
		else
			user_provided_dir=$(abspath "$REPLY")
			if [ -d "${user_provided_dir}" ]; then
				client_repo_dir="${user_provided_dir}"
				break
			else
				echo "${0##*/}: not a valid dir: ${user_provided_dir}, try again ..."
			fi
		fi
	done
	pushd ${client_repo_dir} >/dev/null
	# echo "Changing current working directory to $PWD ..."
	echo "Building files for prod bundle ..."
	grunt prod >/dev/null
	result=$?
	if [ "$result" = "0" ]; then
		cd build
		[ -e app ] && rm -rf app
		mkdir -p app/static
		cp prod/index.html app
		cp -r prod/css prod/js app/static
		cp -r ../bower_components/font-awesome*/fonts app/static
		zip -d "$BUNDLE" app/index.html app/static/css/\* app/static/js/\* app/static/fonts/\* >/dev/null
		zip -r "$BUNDLE" app >/dev/null
	fi
	echo "Distribution bundle updated"
	popd >/dev/null
	if [ $result != "0" ]; then
		echo "${0##*/}: Grunt failed with an error code $result" >&1
		exit "$result"
	fi
fi

echo "Checking eb environment ... "

envs=$(eb list)
current_env=$(echo "$envs"|awk -F" " '$1=="*"{print $2}')

if [ -z "${current_env}" ]; then
	echo -e "\033[1;36mNote:\033[0m You don't have a default environment, please use \`eb use\` to set one."
else
	echo -e "\033[1;36mNote:\033[0m Your current environment is \033[1;32m${current_env}\033[0m, please make sure this is correct before you run \`eb deploy\`."
fi
