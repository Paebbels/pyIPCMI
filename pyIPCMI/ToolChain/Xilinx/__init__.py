# EMACS settings: -*-	tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:          Patrick Lehmann
#                   Martin Zabel
#
# Python Class:     TODO
#
# License:
# ==============================================================================
# Copyright 2017-2019 Patrick Lehmann - Bötzingen, Germany
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
#
# load dependencies
from os                       import environ
from pathlib                  import Path

from pyIPCMI.Base.Project             import FileTypes, VHDLVersion
from pyIPCMI.ToolChain                import ToolChainException, VendorConfiguration


__api__ = [
	'XilinxException',
	'Configuration',
	'XilinxProjectExportMixIn'
]
__all__ = __api__


class XilinxException(ToolChainException):
	pass


class Configuration(VendorConfiguration):
	"""Configuration routines for Xilinx as a vendor.

	This configuration provides a common installation directory setup for all
	Xilinx tools installed on a system.
	"""
	_vendor =               "Xilinx"                    #: The name of the tools vendor.
	_section  =             "INSTALL.Xilinx"            #: The name of the configuration section. Pattern: ``INSTALL.Vendor.ToolName``.
	_template = {
		"Windows": {
			_section: {
				"InstallationDirectory": "C:/Xilinx"
			}
		},
		"Linux": {
			_section: {
				"InstallationDirectory": "/opt/Xilinx"
			}
		}
	}                                                   #: The template for the configuration sections represented as nested dictionaries.

	def _GetDefaultInstallationDirectory(self):
		xilinx = environ.get("XILINX")
		if (xilinx is not None):
			return Path(xilinx).parent.parent.parent.as_posix()

		xilinx = environ.get("XILINX_VIVADO")
		if (xilinx is not None):
			return Path(xilinx).parent.parent.as_posix()

		path = self._TestDefaultInstallPath({"Windows": "Xilinx", "Linux": "Xilinx"})
		if path is None: return super()._GetDefaultInstallationDirectory()
		return path.as_posix()


class XilinxProjectExportMixIn:
	def __init__(self):
		pass

	def _GenerateXilinxProjectFileContent(self, tool, vhdlVersion=VHDLVersion.VHDL93):
		projectFileContent = ""
		for file in self.pyIPCMIProject.Files(fileType=FileTypes.VHDLSourceFile | FileTypes.VerilogSourceFile):  # self.pyIPCMIProject only available via late binding
			if (not file.Path.exists()):                raise XilinxException("Cannot add '{0!s}' to {1} project file.".format(file.Path, tool)) from FileNotFoundError(str(file.Path))
			if file.FileType is FileTypes.VHDLSourceFile:
				# create one VHDL line for each VHDL file
				if (vhdlVersion is VHDLVersion.VHDL2008):
					projectFileContent += "vhdl2008 {0} \"{1!s}\"\n".format(file.LibraryName, file.Path)
				else:
					projectFileContent += "vhdl {0} \"{1!s}\"\n".format(file.LibraryName, file.Path)
			else:  # verilog
				projectFileContent += "verilog work \"{0!s}\"\n".format(file.Path)

		return projectFileContent

	def _WriteXilinxProjectFile(self, projectFilePath, tool, vhdlVersion=VHDLVersion.VHDL93):
		projectFileContent = self._GenerateXilinxProjectFileContent(tool, vhdlVersion)
		self.LogDebug("Writing {0} project file to '{1!s}'".format(tool, projectFilePath))  # self.LogDebug only available via late binding
		with projectFilePath.open('w') as prjFileHandle:
			prjFileHandle.write(projectFileContent)
