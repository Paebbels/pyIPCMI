#! /usr/bin/env bash

# define color escape codes
RED='\e[0;31m'			# Red
GREEN='\e[1;32m'		# Green
MAGENTA='\e[1;35m'	# Magenta
CYAN='\e[1;36m'			# Cyan
NOCOLOR='\e[0m'			# No Color


# -> LastExitCode
# -> Error message
ExitIfError() {
	if [ $1 -ne 0 ]; then
		echo 1>&2 -e $2
		exit 1
	fi
}

echo -e "${MAGENTA}========================================${NOCOLOR}"
echo -e "${MAGENTA}           Configuring pyIPCMI          ${NOCOLOR}"
echo -e "${MAGENTA}========================================${NOCOLOR}"

echo -e "${CYAN}Copy config.private.ini into ./.pyIPCMI directory${NOCOLOR}"
mkdir -p ./.pyIPCMI
ExitIfError $? "${RED}Creating directory ./.pyIPCMI [FAILED]${NOCOLOR}"
cp ./tools/Travis-CI/config.private.ini ./.pyIPCMI
ExitIfError $? "${RED}Copying of ./tools/Travis-CI/config.private.ini [FAILED]${NOCOLOR}"


echo -e "${CYAN}Copy modelsim.ini into ./temp/precompiled/vsim directory${NOCOLOR}"
mkdir -p ./temp/precompiled/vsim
ExitIfError $? "${RED}Creating directory ./temp/precompiled/vsim [FAILED]${NOCOLOR}"
cp ./tools/Travis-CI/modelsim.ini ./temp/precompiled/vsim
ExitIfError $? "${RED}Copying of ./tools/Travis-CI/modelsim.ini [FAILED]${NOCOLOR}"

echo -e "${CYAN}Test pyIPCMI front-end script.${NOCOLOR}"
./pyIPCMI.sh info
ExitIfError $? "${RED}Testing pyIPCMI front-end script [FAILED]${NOCOLOR}"


echo -e "Configuring pyIPCMI ${GREEN}[FINISHED]${NOCOLOR}"
exit 0
