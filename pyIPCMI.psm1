# EMACS settings: -*-	tab-width: 2; indent-tabs-mode: t -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:						Patrick Lehmann
#
# PowerShell Script:	Wrapper Script to execute
#
# Description:
# ------------------------------------
# This is a PowerShell wrapper script (executable) which:
#   -
#
# License:
# ==============================================================================
# Copyright 2017-2019 Patrick Lehmann - Bötzingen, Germany
# Copyright 2007-2016 Technische Universität Dresden - Germany
#                      Chair of VLSI-Design, Diagnostics and Architecture
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
#
# Module parameters
[CmdletBinding()]
param(
	[Parameter(Mandatory=$true)][string]	$Library_RootDirectory,
	[Parameter(Mandatory=$true)][string]	$Library,
	[Parameter(Mandatory=$true)][string]	$pyIPCMI_Dir,
	[Parameter(Mandatory=$true)][string]	$pyIPCMI_PSModule
)
#
# ==============================================================================
# find suitable python version for pyIPCMI
$PythonVersion_Major, $PythonVersion_Minor =	(3, 5)

$Py_exe =		"py.exe"
$Command =	"$Py_exe -{0} -c `"import sys; sys.exit(not (0x{0:00}{1:00}0000 < sys.hexversion < 0x04000000))`"" -f ($PythonVersion_Major, $PythonVersion_Minor)
Invoke-Expression $Command | Out-Null
if ($LastExitCode -eq 0)
{	$Python_Interpreter = $Py_exe
	$Python_Parameters =	(,"-$PythonVersion_Major")
}
else
{	Write-Host "[ERROR]: No suitable Python interpreter found." -ForegroundColor Red
	Write-Host "The script requires Python $PythonMinVersion." -ForegroundColor Yellow
	return 1
}

Export-ModuleMember -Variable "Python_Interpreter"
Export-ModuleMember -Variable "Python_Parameters"

# ==============================================================================
$pyIPCMI_RootDirectory =      "$Library_RootDirectory\$pyIPCMI_Dir"
$pyIPCMI_FrontEndPy =         "$pyIPCMI_RootDirectory\FrontEnd.py"
$pyIPCMI_ConfigDir =          ".pyIPCMI"
$pyIPCMI_HookDir =            "$pyIPCMI_ConfigDir\Hook"
$pyIPCMI_HookDirectory =      "$Library_RootDirectory\$pyIPCMI_HookDir"

$env:LibraryRootDirectory =   "$Library_RootDirectory"
$env:Library =                "$Library"
$env:pyIPCMIRootDirectory =   "$pyIPCMI_RootDirectory"
$env:pyIPCMIConfigDirectory = "$Library_RootDirectory\.pyIPCMI"
$env:pyIPCMIFrontEnd =        "$pyIPCMI_FrontEndPy"

Export-ModuleMember -Variable "Library_RootDirectory"
Export-ModuleMember -Variable "pyIPCMI_RootDirectory"
Export-ModuleMember -Variable "pyIPCMI_HookDirectory"
Export-ModuleMember -Variable "pyIPCMI_FrontEndPy"
Export-ModuleMember -Variable "pyIPCMI_PSModule"

# ==============================================================================
$pyIPCMI_Environments =	@{
	"Aldec" =							@{
		"PreHookFile" =			"Aldec.pre.ps1";
		"PostHookFile" =		"Aldec.post.ps1";
		"Tools" =						@{
			"ActiveHDL" =			@{
				"Load" =				$false;
				"Commands" =		@("asim");
				"PSModule" =			"Aldec.ActiveHDL.psm1";
				"PreHookFile" =		"Aldec.ActiveHDL.pre.ps1";
				"PostHookFile" =	"Aldec.ActiveHDL.post.ps1"
			# };
			# "RevieraPRO" =		@{
				# "Load" =				$false;
				# "Commands" =		@("rpro");
				# "PSModule" =			"Aldec.RevieraPRO.psm1";
				# "PreHookFile" =		"Aldec.RevieraPRO.pre.ps1";
				# "PostHookFile" =	"Aldec.RevieraPRO.post.ps1"
			}
		}};
	"Altera" =						@{
		"PreHookFile" =			"Altera.pre.ps1";
		"PostHookFile" =		"Altera.post.ps1";
		"Tools" =						@{
			"Quartus" =				@{
				"Load" =				$false;
				"Commands" =		@("quartus");
				"PSModule" =			"Altera.Quartus.psm1";
				"PreHookFile" =		"Altera.Quartus.pre.ps1";
				"PostHookFile" =	"Altera.Quartus.post.ps1"
			}
		}};
	"GHDL_GTKWave" =			@{
		"PreHookFile" =			"";
		"PostHookFile" =		"";
		"Tools" =						@{
			"GHDL" =					@{
				"Load" =				$false;
				"Commands" =		@("ghdl");
				"PSModule" =			"GHDL.psm1";
				"PreHookFile" =		"GHDL.pre.ps1";
				"PostHookFile" =	"GHDL.post.ps1"};
			"GTKWave" =				@{
				"Load" =				$false;
				"Commands" =		@("ghdl");
				"PSModule" =			"GTKWave.psm1";
				"PreHookFile" =		"GTKWave.pre.ps1";
				"PostHookFile" =	"GTKWave.post.ps1"}
		}};
	"Intel" =						@{
		"PreHookFile" =			"Intel.pre.ps1";
		"PostHookFile" =		"Intel.post.ps1";
		"Tools" =						@{
			"Quartus" =				@{
				"Load" =				$false;
				"Commands" =		@("quartus");
				"PSModule" =			"Intel.Quartus.psm1";
				"PreHookFile" =		"Intel.Quartus.pre.ps1";
				"PostHookFile" =	"Intel.Quartus.post.ps1"
			}
		}};
	"Lattice" =						@{
		"PreHookFile" =			"Lattice.pre.ps1";
		"PostHookFile" =		"Lattice.post.ps1";
		"Tools" =						@{
			"Diamond" =				@{
				"Load" =				$false;
				"Commands" =		@("lse");
				"PSModule" =			"Lattice.Diamond.psm1";
				"PreHookFile" =		"Lattice.Diamond.pre.ps1";
				"PostHookFile" =	"Lattice.Diamond.post.ps1"
			};
			"ActiveHDL" =			@{
				"Load" =				$false;
				"Commands" =		@("asim");
				"PSModule" =			"Lattice.ActiveHDL.psm1";
				"PreHookFile" =		"Lattice.ActiveHDL.pre.ps1";
				"PostHookFile" =	"Lattice.ActiveHDL.post.ps1"
			}
		}};
	"Mentor" =						@{
		"PreHookFile" =			"Mentor.pre.ps1";
		"PostHookFile" =		"Mentor.post.ps1";
		"Tools" =						@{
			"PrecisionRTL" =	@{
				"Load" =				$false;
				"Commands" =		@("prtl");
				"PSModule" =			"Mentor.PrecisionRTL.psm1";
				"PreHookFile" =		"Mentor.PrecisionRTL.pre.ps1";
				"PostHookFile" =	"Mentor.PrecisionRTL.post.ps1"};
			"ModelSim" =		  @{
				"Load" =				$false;
				"Commands" =		@("vsim", "msim");
				"PSModule" =			"Mentor.ModelSim.psm1";
				"PreHookFile" =		"Mentor.ModelSim.pre.ps1";
				"PostHookFile" =	"Mentor.ModelSim.post.ps1"};
			"QuestaSim" =			@{
				"Load" =				$false;
				"Commands" =		@("qsim");
				"PSModule" =			"Mentor.QuestaSim.psm1";
				"PreHookFile" =		"Mentor.QuestaSim.pre.ps1";
				"PostHookFile" =	"Mentor.QuestaSim.post.ps1"
			}
		}};
	"PowerShell" =				@{
		"PreHookFile" =			"";
		"PostHookFile" =		"";
		"Tools" =						@{
			"PowerShell" =		@{
				"Load" =				$false;
				"Commands" =		@("ps");
				"PSModule" =			"PowerShell.psm1";
				"PreHookFile" =		"PowerShell.pre.ps1";
				"PostHookFile" =	"PowerShell.post.ps1"}
		}};
	"Sphinx" =						@{
		"PreHookFile" =			"";
		"PostHookFile" =		"";
		"Tools" =						@{
			"Sphinx" =				@{
				"Load" =				$false;
				"Commands" =		@("docs");
				"PSModule" =			"Sphinx.psm1";
				"PreHookFile" =		"Sphinx.pre.ps1";
				"PostHookFile" =	"Sphinx.post.ps1"}
		}};
	"Xilinx" =						@{
		"PreHookFile" =			"Xilinx.pre.ps1";
		"PostHookFile" =		"Xilinx.post.ps1";
		"Tools" =						@{
			"ISE" =						@{
				"Load" =				$false;
				"Commands" =		@("ise", "isim", "xst", "coregen");
				"PSModule" =			"Xilinx.ISE.psm1";
				"PreHookFile" =		"Xilinx.ISE.pre.ps1";
				"PostHookFile" =	"Xilinx.ISE.post.ps1"
			};
			"Vivado" =				@{
				"Load" =				$false;
				"Commands" =		@("xsim", "vivado");
				"PSModule" =			"Xilinx.Vivado.psm1";
				"PreHookFile" =		"Xilinx.Vivado.pre.ps1";
				"PostHookFile" =	"Xilinx.Vivado.post.ps1"
			};
		} # Tools
	}	# Xilinx
}
# ==============================================================================
function Invoke-BatchFile
{	param(
		[string]$Path,
		[string]$Parameters
	)
	$environmentVariables = cmd.exe /c " `"$Path`" $Parameters && set "
	foreach ($line in $environmentVariables)
	{	if ($_ -match "^(.*?)=(.*)$")
		{	Set-Content "env:\$($matches[1])" $matches[2]		}
		else
		{	$_																							}
	}
}

# ==============================================================================
function Get-pyIPCMIEnvironmentArray
{	<#
		.SYNOPSIS
		undocumented
		.DESCRIPTION
		undocumented
	#>
	[CmdletBinding()]
	param(
		[Parameter(Mandatory=$true)]	$Values
	)

	# set default values
	$Debug =      $false
	$pyIPCMIEnv = $pyIPCMI_Environments

	# search parameters for specific options like '-D' to enable batch script debug mode
	# TODO: restrict to first n=2? parameters
	foreach ($param in $Values)
	{	if (-not $Debug -and ($param -cmatch "^-\w*D\w*"))
		{	$Debug = $true; continue	}

		$breakIt = $false
		foreach ($VendorName in $pyIPCMIEnv.Keys)
		{	foreach ($ToolName in $pyIPCMIEnv[$VendorName]['Tools'].Keys)
			{	foreach ($Command in $pyIPCMIEnv[$VendorName]['Tools'][$ToolName]['Commands'])
				{	if ($param -ceq $Command)
					{	$pyIPCMIEnv[$VendorName]['Tools'][$ToolName]['Load']	= $true
						return $Debug, $pyIPCMIEnv
					}
				}	# Command
			}	# ToolName
		}	# VendorName
	}	# param
	return $Debug, $pyIPCMIEnv
}

# TODO: build an overload of Get-pyIPCMIEnvironmentArray
function Set-pyIPCMIEnvironmentArray
{	<#
		.SYNOPSIS
		undocumented
		.DESCRIPTION
		undocumented
	#>
	[CmdletBinding()]
	param(
		[Parameter(Mandatory=$true)]	$Value
	)
	# copy the array and set load to true
	$pyIPCMIEnv =		$pyIPCMI_Environments
	$VendorName, $ToolName = $Value.Split(".")
	$pyIPCMIEnv[$VendorName]['Tools'][$ToolName]['Load'] = $true
	return $pyIPCMIEnv
}

Export-ModuleMember -Function "Get-pyIPCMIEnvironmentArray"
Export-ModuleMember -Function "Set-pyIPCMIEnvironmentArray"

# ==============================================================================
function Invoke-OpenEnvironment
{	<#
		.SYNOPSIS
		undocumented
		.DESCRIPTION
		undocumented
	#>
	[CmdletBinding()]
	param(
		[Parameter(Mandatory=$true)]	$LoadEnv
	)
	$Debug = $false	# $true

	# execute vendor and tool pre-hook files if present
	foreach ($VendorName in $LoadEnv.Keys)
	{	foreach ($ToolName in $LoadEnv[$VendorName]['Tools'].Keys)
		{	if ($LoadEnv[$VendorName]['Tools'][$ToolName]['Load'])
			{	if ($Debug -eq $true) {	Write-Host "Loading $VendorName.$ToolName environment..." -ForegroundColor Yellow		}

				# if exists, source the vendor pre-hook file
				$VendorPreHookFile = "$pyIPCMI_HookDir\$($LoadEnv[$VendorName]['PreHookFile'])"
				if (Test-Path $VendorPreHookFile -PathType Leaf)
				{	if ($Debug -eq $true) {	Write-Host "  Loading Vendor pre-hook file: $VendorPreHookFile" -ForegroundColor Yellow	}
					. ($VendorPreHookFile)
				}

				# if exists, source the tool pre-hook file
				$ToolPreHookFile = "$pyIPCMI_HookDir\$($LoadEnv[$VendorName]['Tools'][$ToolName]['PreHookFile'])"
				if (Test-Path $ToolPreHookFile -PathType Leaf)
				{	if ($Debug -eq $true) {	Write-Host "  Loading Tool pre-hook file: $ToolPreHookFile" -ForegroundColor Yellow	}
					. ($ToolPreHookFile)
				}

				$ModuleFile = "$pyIPCMI_ModuleDir\$($LoadEnv[$VendorName]['Tools'][$ToolName]['PSModule'])"
				if (Test-Path $ModuleFile -PathType Leaf)
				{	$ModuleName = (Get-Item $ModuleFile).BaseName
					# unload module if still loaded
					if (Get-Module $ModuleName)
					{ if ($Debug -eq $true) {	Write-Host "  Unloading module: $ModuleName" -ForegroundColor Yellow	}
						Remove-Module $ModuleName
					}

					# load module
					if ($Debug -eq $true) {	Write-Host "  Loading module: $ModuleFile" -ForegroundColor Yellow	}
					Import-Module $ModuleFile -ArgumentList @($Python_Interpreter, $Python_Parameters, $pyIPCMI_FrontEndPy)
					# invoke Open-Environment hook
					return Open-Environment
				}
				elseif ($Debug -eq $true)
				{	Write-Host "[ERROR]: Module '$ModuleFile' not found." -ForegroundColor Red
					return 0
				}
			}
		}
	}
	return 1
}

function Invoke-CloseEnvironment
{	<#
		.SYNOPSIS
		undocumented
		.DESCRIPTION
		undocumented
	#>
	[CmdletBinding()]
	param(
		[Parameter(Mandatory=$true)]	$LoadEnv
	)
	$Debug = $false	# $true

	# execute vendor and tool post-hook files if present
	foreach ($VendorName in $LoadEnv.Keys)
	{	foreach ($ToolName in $LoadEnv[$VendorName]['Tools'].Keys)
		{	if ($LoadEnv[$VendorName]['Tools'][$ToolName]['Load'])
			{	# if exists, source the tool pre-hook file
				$ToolPostHookFile = "$pyIPCMI_HookDir\$($LoadEnv[$VendorName]['Tools'][$ToolName]['PostHookFile'])"
				if (Test-Path $ToolPostHookFile -PathType Leaf)
				{	. ($ToolPostHookFile)		}

				# if exists, source the vendor pre-hook file
				$VendorPostHookFile = "$pyIPCMI_HookDir\$($LoadEnv[$VendorName]['PostHookFile'])"
				if (Test-Path $VendorPostHookFile -PathType Leaf)
				{	. ($VendorPostHookFile)	}

				$ModuleFile = "$pyIPCMI_ModuleDir\$($LoadEnv[$VendorName]['Tools'][$ToolName]['PSModule'])"
				if (Test-Path $ModuleFile -PathType Leaf)
				{	$ModuleName = (Get-Item $ModuleFile).BaseName
					if (Get-Module $ModuleName)
					{ $PyWrapper_ExitCode = Close-Environment
						Remove-Module $ModuleName
					}
				}
			}
		}
	}
}

Export-ModuleMember -Function "Invoke-OpenEnvironment"
Export-ModuleMember -Function "Invoke-CloseEnvironment"

function pyIPCMIQuery
{	<#
		.SYNOPSIS
		pyIPCMI front-end function
		.DESCRIPTION
		undocumented
	#>
	[CmdletBinding()]
	param(
		[Parameter(Mandatory=$true)][string]	$Query
	)
	return Invoke-Expression "$Python_Interpreter $Python_Parameters $pyIPCMI_PythonDir\$pyIPCMI_FrontEndPy query $Query"
}

Export-ModuleMember -Function "pyIPCMIQuery"

function pyIPCMI
{	<#
		.SYNOPSIS
		pyIPCMI front-end function
		.DESCRIPTION
		undocumented
	#>
	# $env:pyIPCMIRootDirectory =			$pyIPCMI_RootDir

	$Expr = "$Python_Interpreter $Python_Parameters $pyIPCMI_FrontEndPy $args"
	Invoke-Expression $Expr
	return $LastExitCode
}

Export-ModuleMember -Function "pyIPCMI"
