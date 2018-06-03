# EMACS settings: -*- tab-width: 2; indent-tabs-mode: t -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:          Patrick Lehmann
#
# Bash Script:      Wrapper Script to execute a given Python script
#
# Description:
# ------------------------------------
# This is a bash script (callable) which:
#   - checks for a minimum installed Python version
#   - loads vendor environments before executing the Python programs
#
# License:
# ==============================================================================
# Copyright 2017-2018 Patrick Lehmann - Bötzingen, Germany
# Copyright 2007-2016 Technische Universität Dresden - Germany
#                     Chair of VLSI-Design, Diagnostics and Architecture
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

# script settings
pyIPCMI_RootDirectory="$Library_RootDirectory/$pyIPCMI_Dir"
pyIPCMI_FrontEndPy="$pyIPCMI_RootDirectory/FrontEnd.py"
pyIPCMI_ConfigDir=".pyIPCMI"
pyIPCMI_HookDir="$pyIPCMI_ConfigDir/Hook"
pyIPCMI_HookDirectory="$Library_RootDirectory/$pyIPCMI_HookDir"
pyIPCMI_MinVersion="3.5"

# publish pyIPCMI directories as environment variables
export LibraryRootDirectory="$Library_RootDirectory"
export Library="$Library"
export pyIPCMIRootDirectory="$pyIPCMI_RootDirectory"
export pyIPCMIConfigDirectory="$Library_RootDirectory/.pyIPCMI"
export pyIPCMIFrontEnd="$pyIPCMI_FrontEndPy"

# set default values
pyIPCMI_Debug=0
pyIPCMI_ExitCode=0

# define color escape codes
ANSI_RED='\e[0;31m'       # Red
ANSI_YELLOW='\e[1;33m'    # Yellow
ANSI_NOCOLOR='\e[0m'      # No Color


# Aldec tools
declare -A Env_Aldec=(
	["PreHookFile"]="Aldec.pre.sh"
	["PostHookFile"]="Aldec.post.sh"
	["Tools"]="ActiveHDL RevieraPRO"
)
declare -A Env_Aldec_ActiveHDL=(
	["Load"]=0
	["Commands"]="asim"
	["BashModule"]="Aldec.ActiveHDL.sh"
	["PreHookFile"]="Aldec.ActiveHDL.pre.sh"
	["PostHookFile"]="Aldec.ActiveHDL.post.sh"
)
declare -A Env_Aldec_RevieraPRO=(
	["Load"]=0
	["Commands"]="rpro"
	["BashModule"]="Aldec.RevieraPRO.sh"
	["PreHookFile"]="Aldec.RevieraPRO.pre.sh"
	["PostHookFile"]="Aldec.RevieraPRO.post.sh"
)
# Altera tools
declare -A Env_Altera=(
	["PreHookFile"]="Altera.pre.sh"
	["PostHookFile"]="Altera.post.sh"
	["Tools"]="Quartus"
)
declare -A Env_Altera_Quartus=(
	["Load"]=0
	["Commands"]="quartus"
	["BashModule"]="Altera.Quartus.sh"
	["PreHookFile"]="Altera.Quartus.pre.sh"
	["PostHookFile"]="Altera.Quartus.post.sh"
)
# GHDL + GTKWave
declare -A Env_GHDL=(
	["PreHookFile"]=""
	["PostHookFile"]=""
	["Tools"]="GHDL GTKWave"
)
declare -A Env_GHDL_GHDL=(
	["Load"]=0
	["Commands"]="ghdl"
	["BashModule"]="GHDL.sh"
	["PreHookFile"]="GHDL.pre.sh"
	["PostHookFile"]="GHDL.post.sh"
)
declare -A Env_GHDL_GTKWave=(
	["Load"]=0
	["Commands"]="ghdl"
	["BashModule"]="GTKWave.sh"
	["PreHookFile"]="GTKWave.pre.sh"
	["PostHookFile"]="GTKWave.post.sh"
)
# Intel tools
declare -A Env_Intel=(
	["PreHookFile"]="Intel.pre.sh"
	["PostHookFile"]="Intel.post.sh"
	["Tools"]="Quartus"
)
declare -A Env_Intel_Quartus=(
	["Load"]=0
	["Commands"]="quartus"
	["BashModule"]="Intel.Quartus.sh"
	["PreHookFile"]="Intel.Quartus.pre.sh"
	["PostHookFile"]="Intel.Quartus.post.sh"
)
# Lattice tools
declare -A Env_Lattice=(
	["PreHookFile"]="Lattice.pre.sh"
	["PostHookFile"]="Lattice.post.sh"
	["Tools"]="Diamond ActiveHDL"
)
declare -A Env_Lattice_Diamond=(
	["Load"]=0
	["Commands"]="lse"
	["BashModule"]="Lattice.Diamond.sh"
	["PreHookFile"]="Lattice.Diamond.pre.sh"
	["PostHookFile"]="Lattice.Diamond.post.sh"
)
declare -A Env_Lattice_ActiveHDL=(
	["Load"]=0
	["Commands"]="asim"
	["BashModule"]="Lattice.ActiveHDL.sh"
	["PreHookFile"]="Lattice.ActiveHDL.pre.sh"
	["PostHookFile"]="Lattice.ActiveHDL.post.sh"
)
# Mentor Graphics tools
declare -A Env_Mentor=(
	["PreHookFile"]="Mentor.pre.sh"
	["PostHookFile"]="Mentor.post.sh"
	["Tools"]="PrecisionRTL ModelSim QuestaSim"
)
declare -A Env_Mentor_PrecisionRTL=(
	["Load"]=0
	["Commands"]="prtl"
	["BashModule"]="Mentor.PrecisionRTL.sh"
	["PreHookFile"]="Mentor.PrecisionRTL.pre.sh"
	["PostHookFile"]="Mentor.PrecisionRTL.post.sh"
)
declare -A Env_Mentor_ModelSim=(
	["Load"]=0
	["Commands"]="vsim msim"
	["BashModule"]="Mentor.ModelSim.sh"
	["PreHookFile"]="Mentor.ModelSim.pre.sh"
	["PostHookFile"]="Mentor.ModelSim.post.sh"
)
declare -A Env_Mentor_QuestaSim=(
	["Load"]=0
	["Commands"]="qsim"
	["BashModule"]="Mentor.QuestaSim.sh"
	["PreHookFile"]="Mentor.QuestaSim.pre.sh"
	["PostHookFile"]="Mentor.QuestaSim.post.sh"
)
# Sphinx documentation system
declare -A Env_Sphinx=(
	["PreHookFile"]=""
	["PostHookFile"]=""
	["Tools"]="Sphinx"
)
declare -A Env_Sphinx_Sphinx=(
	["Load"]=0
	["Commands"]="docs"
	["BashModule"]="Sphinx.sh"
	["PreHookFile"]="Sphinx.pre.sh"
	["PostHookFile"]="Sphinx.post.sh"
)
# Xilinx tools
declare -A Env_Xilinx=(
	["PreHookFile"]="Xilinx.pre.sh"
	["PostHookFile"]="Xilinx.post.sh"
	["Tools"]="ISE Vivado"
)
declare -A Env_Xilinx_ISE=(
	["Load"]=0
	["Commands"]="isim xst coregen ise"
	["BashModule"]="Xilinx.ISE.sh"
	["PreHookFile"]="Xilinx.ISE.pre.sh"
	["PostHookFile"]="Xilinx.ISE.post.sh"
)
declare -A Env_Xilinx_Vivado=(
	["Load"]=0
	["Commands"]="xsim vivado"
	["BashModule"]="Xilinx.Vivado.sh"
	["PreHookFile"]="Xilinx.Vivado.pre.sh"
	["PostHookFile"]="Xilinx.Vivado.post.sh"
)
# Cocotb
declare -A Env_Cocotb=(
	["PreHookFile"]="Cocotb.pre.sh"
	["PostHookFile"]="Cocotb.post.sh"
	["Tools"]="QuestaSim"
)
declare -A Env_Cocotb_QuestaSim=(
	["Load"]=0
	["Commands"]="cocotb"
	["BashModule"]="Cocotb.QuestaSim.sh"
	["PreHookFile"]="Cocotb.QuestaSim.pre.sh"
	["PostHookFile"]="Cocotb.QuestaSim.post.sh"
)


# List all vendors
Env_Vendors="Aldec Altera GHDL Intel Lattice Mentor Sphinx Xilinx Cocotb"

# search script parameters for known commands
BreakIt=0
for param in $Wrapper_Parameters; do
	if [ "$param" = "-D" ]; then
		pyIPCMI_Debug=1
		continue
	fi
	# compare registered commands from all vendor tools
	for VendorName in $Env_Vendors; do
		declare -n VendorIndex="Env_$VendorName"
		for ToolName in ${VendorIndex["Tools"]}; do
			declare -n ToolIndex="Env_${VendorName}_${ToolName}"
			for Command in ${ToolIndex["Commands"]}; do
				if [ "$param" = "$Command" ]; then
					ToolIndex["Load"]=1
					BreakIt=1
					break
				fi
			done  # Commands
		done  # ToolNames
	done  # VendorNames
	# break is a known command was detected
	if [ $BreakIt -eq 1 ]; then break; fi
done  # Parameters


# find suitable python version or abort execution
Python_VersionTest="import sys; sys.exit(not (0x0${pyIPCMI_MinVersion:0:1}0${pyIPCMI_MinVersion:2:1}0000 < sys.hexversion < 0x04000000))"
Python_Message=""
python -c "$Python_VersionTest" 2>/dev/null
if [ $? -eq 0 ]; then
	Python_Interpreter=$(which python 2>/dev/null)
	test $pyIPCMI_Debug -eq 1 && Python_Message=" (standard interpreter)"
else
	# standard python interpreter is not suitable, try to find a suitable version manually
	for pyVersion in 3.9 3.8 3.7 3.6 3.5 3.4; do
		Python_Interpreter=$(which python$pyVersion 2>/dev/null)
		# if ExitCode = 0 => version found
		if [ $? -eq 0 ]; then
			# redo version test
			$Python_Interpreter -c "$Python_VersionTest" 2>/dev/null
			if [ $? -eq 0 ]; then break; fi
		fi
	done
fi
# if no interpreter was found => exit
if [ -z "$Python_Interpreter" ]; then
	echo 1>&2 -e "${ANSI_RED}No suitable Python interpreter found.${ANSI_NOCOLOR}"
	echo 1>&2 -e "${ANSI_RED}The script requires Python >= $pyIPCMI_MinVersion${ANSI_NOCOLOR}"
	pyIPCMI_ExitCode=1
fi

if [[ ($pyIPCMI_ExitCode -eq 0) && ($pyIPCMI_Debug -eq 1) ]]; then
	echo -e "${ANSI_YELLOW}This is the pyIPCMI Library script wrapper operating in debug mode.${ANSI_NOCOLOR}"
	echo
	echo -e "${ANSI_YELLOW}Directories:${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}  Library root:    $Library_RootDirectory${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}  pyIPCMI root:    $pyIPCMI_RootDirectory${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}  working:         $Wrapper_WorkingDirectory${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}Python:${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}  Interpreter:     $Python_Interpreter$Python_Message${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}Script:${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}  Filename:        $pyIPCMI_FrontEndPy${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}  Library:         $Library${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}  Solution:        $Solution${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}  Project:         $Project${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}  Parameters:      $Wrapper_Parameters${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}Load Environment:  ${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}  Lattice Diamond: ${Env_Lattice_Diamond["Load"]}${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}  Xilinx ISE:      ${Env_Xilinx_ISE["Load"]}${ANSI_NOCOLOR}"
	echo -e "${ANSI_YELLOW}  Xilinx VIVADO:   ${Env_Xilinx_Vivado["Load"]}${ANSI_NOCOLOR}"
	echo
fi


# execute vendor and tool pre-hook files if present
if [ $pyIPCMI_ExitCode -eq 0 ]; then
	for VendorName in $Env_Vendors; do
		declare -n VendorIndex="Env_$VendorName"
		for ToolName in ${VendorIndex["Tools"]}; do
			declare -n ToolIndex="Env_${VendorName}_${ToolName}"
			if [ ${ToolIndex["Load"]} -eq 1 ]; then
				# if exists, source the vendor pre-hook file
				VendorPreHookFile=$pyIPCMIRootDirectory/$pyIPCMI_HookDirectory/${VendorIndex["PreHookFile"]}
				test -f $VendorPreHookFile && source $VendorPreHookFile

				# if exists, source the tool pre-hook file
				ToolPreHookFile=$pyIPCMIRootDirectory/$pyIPCMI_HookDirectory/${ToolIndex["PreHookFile"]}
				test -f $ToolPreHookFile && source $ToolPreHookFile

				# if exists, source the BashModule file
				ModuleFile=$pyIPCMIRootDirectory/$pyIPCMI_WrapperDirectory/${ToolIndex["BashModule"]}
				if [ -f $ModuleFile ]; then
					source $ModuleFile
					OpenEnvironment $Python_Interpreter $pyIPCMI_FrontEnd
					pyIPCMI_ExitCode=$?
				fi

				break 2
			fi
		done  # ToolNames
	done  # VendorNames
fi

# execute script with appropriate python interpreter and all given parameters
if [ $pyIPCMI_ExitCode -eq 0 ]; then
	if [ -z $Wrapper_Solution ]; then
		Python_ScriptParameters=$Wrapper_Parameters
	else
		Python_ScriptParameters="--sln=$Wrapper_Solution $Wrapper_Parameters"
	fi

	if [ $pyIPCMI_Debug -eq 1 ]; then
		echo -e "${ANSI_YELLOW}Launching: '$Python_Interpreter $pyIPCMI_FrontEndPy $Python_ScriptParameters'${ANSI_NOCOLOR}"
		echo -e "${ANSI_YELLOW}------------------------------------------------------------${ANSI_NOCOLOR}"
	fi

	# launching python script
	set -f
	"$Python_Interpreter" $Python_Script $Python_ScriptParameters
	pyIPCMI_ExitCode=$?
fi

# execute vendor and tool post-hook files if present
for VendorName in $Env_Vendors; do
	declare -n VendorIndex="Env_$VendorName"
	for ToolName in ${VendorIndex["Tools"]}; do
		declare -n ToolIndex="Env_${VendorName}_${ToolName}"
		if [ ${ToolIndex["Load"]} -eq 1 ]; then
			# if exists, source the tool Post-hook file
			ToolPostHookFile=$pyIPCMI_RootDir/$pyIPCMI_HookDirectory/${ToolIndex["PostHookFile"]}
			test -f $ToolPostHookFile && source $ToolPostHookFile

			# if exists, source the vendor post-hook file
			VendorPostHookFile=$pyIPCMI_RootDir/$pyIPCMI_HookDirectory/${VendorIndex["PostHookFile"]}
			test -f $VendorPostHookFile && source $VendorPostHookFile

			# if exists, source the BashModule file
			ModuleFile=$pyIPCMI_RootDir/$pyIPCMI_WrapperDirectory/${ToolIndex["BashModule"]}
			if [ -f $ModuleFile ]; then
				# source $ModuleFile
				CloseEnvironment $Python_Interpreter $pyIPCMI_FrontEnd
				pyIPCMI_ExitCode=$?
			fi
			break 2
		fi
	done  # ToolNames
done  # VendorNames

# clean up environment variables
unset pyIPCMIRootDirectory
unset pyIPCMIWorkingDirectory
