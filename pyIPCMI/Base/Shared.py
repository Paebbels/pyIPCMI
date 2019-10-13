# EMACS settings: -*-	tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:          Patrick Lehmann
#
# Python Class:     Base class for ***
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
import shutil
from datetime           import datetime
from os                 import chdir

from pyTokenizer        import ParserException

from lib.Functions              import Init
from pyIPCMI.Base               import IHost
from pyIPCMI.Base.Exceptions    import CommonException, SkipableCommonException
from pyIPCMI.Base.Logging       import ILogable
from pyIPCMI.Base.Project       import ToolChain, Tool, VHDLVersion, Environment
from pyIPCMI.DataBase.Solution  import VirtualProject, FileListFile


__api__ = [
	'to_time',
	'Shared'
]
__all__ = __api__


# local helper function
def to_time(seconds):
	"""
	Convert *n* seconds to a :py:class:`str` with this pattern: "{min}:{sec:02}".

	:type seconds:  int
	:param seconds: Number of seconds to be converted.
	:rtype:         str
	:return:        Returns a string formatted as #:##. E.g. "1:05"
	"""

	minutes = int(seconds / 60)
	seconds -= minutes * 60
	return "{min}:{sec:02}".format(min=minutes, sec=seconds)


class Shared(ILogable):
	"""
	Base class for Simulator and Compiler.

	:type  host:      object
	:param host:      The hosting instance for this instance.
	:type  dryRun:    bool
	:param dryRun:    Enable dry-run mode
	:type  noCleanUp: bool
	:param noCleanUp: Don't clean up after a run.
	"""

	ENVIRONMENT =     Environment.Any
	TOOL_CHAIN =      ToolChain.Any
	TOOL =            Tool.Any
	VHDL_VERSION =    VHDLVersion.VHDL2008

	class __Directories__:
		Working = None
		pyIPCMIRoot = None

	def __init__(self, host : IHost, dryRun):
		ILogable.__init__(self, host.Logger if isinstance(host, ILogable) else None)

		self._host =            host
		self._dryRun =          dryRun
		self._pyIPCMIProject =      None
		self._directories =     self.__Directories__()
		self._toolChain =       None
		self._vhdlVersion =     self.VHDL_VERSION
		self._vhdlGenerics =    None

		self._testSuite =       None
		self._startAt =         datetime.now()
		self._endAt =           None
		self._lastEvent =       self._startAt
		self._prepareTime =     None

	# class properties
	# ============================================================================
	@property
	def Host(self):         return self._host
	@property
	def DryRun(self):       return self._dryRun
	@property
	def VHDLVersion(self):  return self._vhdlVersion
	@property
	def pyIPCMIProject(self):   return self._pyIPCMIProject
	@property
	def Directories(self):  return self._directories

	def _GetTimeDeltaSinceLastEvent(self):
		now = datetime.now()
		result = now - self._lastEvent
		self._lastEvent = now
		return result

	def _PrepareEnvironment(self):
		# create fresh temporary directory
		self.LogVerbose("Creating fresh temporary directory.")
		if (self.Directories.Working.exists()):
			self._PrepareEnvironment_PurgeDirectory()
			# self.LogDebug("Purging temporary directory: {0!s}".format(self.Directories.Working))
			# for item in self.Directories.Working.iterdir():
			# 	try:
			# 		if item.is_dir():
			# 			shutil.rmtree(str(item))
			# 		elif item.is_file():
			# 			item.unlink()
			# 	except OSError as ex:
			# 		raise CommonException("Error while deleting '{0!s}'.".format(item)) from ex
		else:
			self._PrepareEnvironment_CreatingDirectory()
			# self.LogDebug("Creating temporary directory: {0!s}".format(self.Directories.Working))
			# try:
			# 	self.Directories.Working.mkdir(parents=True)
			# except OSError as ex:
			# 	raise CommonException("Error while creating '{0!s}'.".format(self.Directories.Working)) from ex

		self._PrepareEnvironment_ChangeDirectory()
		# change working directory to temporary path
		# self.LogVerbose("Changing working directory to temporary directory.")
		# self.LogDebug("cd \"{0!s}\"".format(self.Directories.Working))
		# try:
		# 	chdir(str(self.Directories.Working))
		# except OSError as ex:
		# 	raise CommonException("Error while changing to '{0!s}'.".format(self.Directories.Working)) from ex

	def _PrepareEnvironment_PurgeDirectory(self):
		self.LogDebug("Purging temporary directory: {0!s}".format(self.Directories.Working))
		for item in self.Directories.Working.iterdir():
			try:
				if item.is_dir():
					shutil.rmtree(str(item))
				elif item.is_file():
					item.unlink()
			except OSError as ex:
				raise CommonException("Error while deleting '{0!s}'.".format(item)) from ex

	def _PrepareEnvironment_CreatingDirectory(self):
		self.LogDebug("Creating temporary directory: {0!s}".format(self.Directories.Working))
		try:
			self.Directories.Working.mkdir(parents=True)
		except OSError as ex:
			raise CommonException("Error while creating '{0!s}'.".format(self.Directories.Working)) from ex

	def _PrepareEnvironment_ChangeDirectory(self):
		"""Change working directory to temporary path 'temp/<tool>'."""
		self.LogVerbose("Changing working directory to temporary directory.")
		self.LogDebug("cd \"{0!s}\"".format(self.Directories.Working))
		try:
			chdir(str(self.Directories.Working))
		except OSError as ex:
			raise CommonException("Error while changing to '{0!s}'.".format(self.Directories.Working)) from ex

	def _Prepare(self):
		self.LogNormal("Preparing {0}.".format(self.TOOL.LongName))

	def _CreatepyIPCMIProject(self, projectName, board):
		# create a pyIPCMIProject and read all needed files
		self.LogVerbose("Creating pyIPCMI project '{0}'".format(projectName))
		pyIPCMIProject = VirtualProject(projectName)

		# configure the project
		pyIPCMIProject.RootDirectory =  self.Host.Directories.Root
		pyIPCMIProject.Environment =    self.ENVIRONMENT
		pyIPCMIProject.ToolChain =      self.TOOL_CHAIN
		pyIPCMIProject.Tool =           self.TOOL
		pyIPCMIProject.VHDLVersion =    self._vhdlVersion
		pyIPCMIProject.Board =          board

		self._pyIPCMIProject = pyIPCMIProject

	def _AddFileListFile(self, fileListFilePath):
		self.LogVerbose("Reading filelist '{0!s}'".format(fileListFilePath))
		# add the *.files file, parse and evaluate it
		# if (not fileListFilePath.exists()):    raise SimulatorException("Files file '{0!s}' not found.".format(fileListFilePath)) from FileNotFoundError(str(fileListFilePath))

		try:
			fileListFile = self._pyIPCMIProject.AddFile(FileListFile(fileListFilePath))
			fileListFile.Parse(self._host)
			fileListFile.CopyFilesToFileSet()
			fileListFile.CopyExternalLibraries()
			self._pyIPCMIProject.ExtractVHDLLibrariesFromVHDLSourceFiles()
		except (ParserException, CommonException) as ex:
			raise SkipableCommonException("Error while parsing '{0!s}'.".format(fileListFilePath)) from ex

		self.LogDebug("=" * 78)
		self.LogDebug("Pretty printing the pyIPCMIProject...")
		self.LogDebug("{DARK_RED}Disabled{NOCOLOR}".format(**Init.Foreground))
		# self.LogDebug(self._pyIPCMIProject.pprint(2))
		self.LogDebug("=" * 78)
		if (len(fileListFile.Warnings) > 0):
			for warn in fileListFile.Warnings:
				self.LogWarning(warn)
			raise SkipableCommonException("Found critical warnings while parsing '{0!s}'".format(fileListFilePath))

	def _GetHDLParameters(self, configSectionName):
		"""Parse option 'HDLParameters' for Verilog Parameters / VHDL Generics."""
		result = {}
		hdlParameters = self.Host.Config[configSectionName]["HDLParameters"]
		if (len(hdlParameters) > 0):
			for keyValuePair in hdlParameters.split(";"):
				try:
					key,value = keyValuePair.split("=")
				except ValueError:
					raise CommonException("Syntax error in option 'HDLParameters' within section {section}.".format(section=configSectionName))
				result[key.strip()] = value.strip()
		return result
