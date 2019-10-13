# EMACS settings: -*-  tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:               Patrick Lehmann
#
# Python Sub Module:    Saves the pyIPCMI configuration as python source code.
#
# License:
# ==============================================================================
# Copyright 2017-2019 Patrick Lehmann - Bötzingen, Germany
# Copyright 2007-2015 Technische Universität Dresden - Germany
#                     Chair of VLSI-Design, Diagnostics and Architecture
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
#
# load dependencies
from pathlib            import Path

from pyExceptions       import NotConfiguredException, PlatformNotSupportedException

from pyIPCMI.ToolChain  import ConfigurationException


__api__ = [
	'Query',
	'__pyIPCMI_SOLUTION_KEYWORD__',
	'__pyIPCMI_PROJECT_KEYWORD__'
]
__all__ = __api__


__pyIPCMI_SOLUTION_KEYWORD__ =  "Solution"
__pyIPCMI_PROJECT_KEYWORD__ =   "Project"


class Query:
	def __init__(self, host):
		self.__host = host

	@property
	def Host(self):        return self.__host
	@property
	def Platform(self):    return self.__host.Platform
	@property
	def Config(self):  return self.__host.Config

	def QueryConfiguration(self, query):
		if (query == "ModelSim:InstallationDirectory"):
			result = self._GetModelSimInstallationDirectory()
		elif (query == "ModelSim:BinaryDirectory"):
			result = self._GetModelSimBinaryDirectory()
		elif (query == "Xilinx.ISE:SettingsFile"):
			result = self._GetXilinxISESettingsFile()
		elif (query == "Xilinx.Vivado:SettingsFile"):
			result = self._GetXilinxVivadoSettingsFile()
		else:
			parts = query.split(":")
			if (len(parts) == 2):
				sectionName = parts[0]
				optionName =  parts[1]
				try:
					result =  self.Config[sectionName][optionName]
				except KeyError as ex:
					raise ConfigurationException("Requested setting '{0}:{1}' not found.".format(sectionName, optionName)) from ex
			else:
				raise ConfigurationException("Syntax error in query string '{0}'".format(query))

		if isinstance(result, Path):  result = str(result)
		return result

	def _GetModelSimInstallationDirectory(self):
		if (len(self.Config.options('INSTALL.Mentor.QuestaSim')) != 0):
			return Path(self.Config['INSTALL.Mentor.QuestaSim']['InstallationDirectory'])
		elif (len(self.Config.options('INSTALL.Altera.ModelSim')) != 0):
			return Path(self.Config['INSTALL.Altera.ModelSim']['InstallationDirectory'])
		else:
			raise NotConfiguredException("ERROR: ModelSim is not configured on this system.")

	def _GetModelSimBinaryDirectory(self):
		if (len(self.Config.options('INSTALL.Mentor.QuestaSim')) != 0):
			return Path(self.Config['INSTALL.Mentor.QuestaSim']['BinaryDirectory'])
		elif (len(self.Config.options('INSTALL.Altera.ModelSim')) != 0):
			return Path(self.Config['INSTALL.Altera.ModelSim']['BinaryDirectory'])
		else:
			raise NotConfiguredException("ERROR: ModelSim is not configured on this system.")

	def _GetXilinxISESettingsFile(self):
		if (len(self.Config.options('INSTALL.Xilinx.ISE')) != 0):
			iseInstallationDirectoryPath = Path(self.Config['INSTALL.Xilinx.ISE']['InstallationDirectory'])
			if (self.Platform == "Windows"):
				return iseInstallationDirectoryPath / "settings64.bat"
			elif (self.Platform == "Linux"):
				return iseInstallationDirectoryPath / "settings64.sh"
			else:
				raise PlatformNotSupportedException(self.Platform)
		else:
			raise NotConfiguredException("ERROR: Xilinx ISE is not configured on this system.")

	def _GetXilinxVivadoSettingsFile(self):
		if (len(self.Config.options('INSTALL.Xilinx.Vivado')) != 0):
			iseInstallationDirectoryPath = Path(self.Config['INSTALL.Xilinx.Vivado']['InstallationDirectory'])
			if (self.Platform == "Windows"):
				return iseInstallationDirectoryPath / "settings64.bat"
			elif (self.Platform == "Linux"):
				return iseInstallationDirectoryPath / "settings64.sh"
			else:
				raise PlatformNotSupportedException(self.Platform)
		else:
			raise NotConfiguredException("ERROR: Xilinx ISE is not configured on this system.")
