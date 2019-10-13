# EMACS settings: -*-	tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:          Patrick Lehmann
#                   Martin Zabel
#
# Python Class:     GHDL specific classes
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
from pathlib                    import Path
from re                         import compile as re_compile
from subprocess                 import check_output, CalledProcessError

from pyExceptions               import PlatformNotSupportedException
from pyCallBy                   import CallByRefParam

from lib.Functions              import Init
from pyIPCMI.Base.Logging       import LogEntry, Severity
from pyIPCMI.Base.Executable    import LongValuedFlagArgument, DryRunException
from pyIPCMI.Base.Executable    import ExecutableArgument, PathArgument, StringArgument, ValuedFlagListArgument
from pyIPCMI.Base.Executable    import ShortFlagArgument, LongFlagArgument, CommandLineArgumentList
from pyIPCMI.DataBase.Entity    import SimulationResult
from pyIPCMI.ToolChain          import ToolMixIn, ToolChainException, ConfigurationException, ToolConfiguration, OutputFilteredExecutable
from pyIPCMI.Simulator          import PoCSimulationResultFilter


__api__ = [
	'GHDLException',
	'GHDLReanalyzeException',
	'Configuration',
	'GHDL',
	'GHDLAnalyze',
	'GHDLElaborate',
	'GHDLRun',
	'GHDLAnalyzeFilter',
	'GHDLElaborateFilter',
	'GHDLRunFilter'
]
__all__ = __api__


class GHDLException(ToolChainException):
	pass


class GHDLReanalyzeException(GHDLException):
	pass


class Configuration(ToolConfiguration):
	_vendor =               "tgingold"                  #: The name of the tools vendor.
	_toolName =             "GHDL"                      #: The name of the tool.
	_section  =             "INSTALL.GHDL"              #: The name of the configuration section. Pattern: ``INSTALL.Vendor.ToolName``.
	_multiVersionSupport =  True                        #: Git supports multiple versions installed on the same system.
	_template = {
		"Windows": {
			_section: {
				"Version":                "0.36-dev",
				"Backend":                "mcode",
				"Runtime":                "gnatgpl32",
				"SectionName":            ("%{PathWithRoot}#${Version}-${Runtime}-${Backend}",  None),
				"InstallationDirectory":  ("${${SectionName}:InstallationDirectory}",           "C:/Tools/GHDL/${Version}-${Runtime}-${Backend}"),
				"BinaryDirectory":        ("${${SectionName}:BinaryDirectory}",                 "${InstallationDirectory}/bin"),
				"ScriptDirectory":        ("${${SectionName}:ScriptDirectory}",                 "${InstallationDirectory}/lib/vendors")
			}
		},
		"Linux": {
			_section: {
				"Version":                "0.36-dev",
				"Backend":                "llvm",
				"SectionName":            ("%{PathWithRoot}#${Version}-${Backend}",   None),
				"InstallationDirectory":  ("${${SectionName}:InstallationDirectory}", "/usr/local"),
				"BinaryDirectory":        ("${${SectionName}:BinaryDirectory}",       "${InstallationDirectory}/bin"),
				"ScriptDirectory":        ("${${SectionName}:ScriptDirectory}",       "${InstallationDirectory}/lib/ghdl/vendors")
			}
		},
		"Darwin": {
			_section: {
				"Version":                "0.36-dev",
				"Backend":                "llvm",
				"SectionName":            ("%{PathWithRoot}#${Version}-${Backend}",   None),
				"InstallationDirectory":  ("${${SectionName}:InstallationDirectory}", "/usr/local"),
				"BinaryDirectory":        ("${${SectionName}:BinaryDirectory}",       "${InstallationDirectory}/bin"),
				"ScriptDirectory":        ("${${SectionName}:ScriptDirectory}",       "${InstallationDirectory}/lib/ghdl/vendors")
			}
		},
		"MinGW": {
			_section: {
				"Version":                "0.36-dev",
				"Backend":                "llvm",
				"SectionName":            ("%{PathWithRoot}#${Version}-${Backend}",   None),
				"InstallationDirectory":  ("${${SectionName}:InstallationDirectory}", "/c/Tools/GHDL/${Version}-${Runtime}-${Backend}"),
				"BinaryDirectory":        ("${${SectionName}:BinaryDirectory}",       "${InstallationDirectory}/bin"),
				"ScriptDirectory":        ("${${SectionName}:ScriptDirectory}",       "${InstallationDirectory}/lib/ghdl/vendors")
			}
		}
	}                                                   #: The template for the configuration sections represented as nested dictionaries.

	def ConfigureForAll(self):
		try:
			if (not self._AskInstalled("Is GHDL installed on your system?")):
				self.ClearSection()
			else:
				# Configure GHDL version
				if self._multiVersionSupport:
					self.PrepareVersionedSections()

				self._ConfigureInstallationDirectory()
				binPath = self._ConfigureBinaryDirectory()

				self.__WriteGHDLSection(binPath)
				self._host.LogNormal("{DARK_GREEN}GHDL is now configured.{NOCOLOR}".format(**Init.Foreground), indent=1)
		except ConfigurationException:
			self.ClearSection()
			raise

	def _GetDefaultInstallationDirectory(self):
		if (self._host.Platform in ["Linux", "Darwin"]):
			try:
				name = check_output(["which", "ghdl"], universal_newlines=True).strip()
				if name != "": return Path(name).parent.as_posix()
			except CalledProcessError:
				pass # `which` returns non-zero exit code if GHDL is not in PATH

		return super()._GetDefaultInstallationDirectory()

	def _ConfigureBinaryDirectory(self):
		"""Updates section with value from _template and returns directory as Path object."""
		self._ConfigureScriptDirectory()
		return super()._ConfigureBinaryDirectory()

	def _ConfigureScriptDirectory(self):
		"""Updates section with value from _template and returns directory as Path object."""
		# unresolved = self._template[self._host.Platform][self._section]['ScriptDirectory']
		# self._host.Config[self._section]['ScriptDirectory'] = unresolved  # create entry
		scriptPath = Path(self._host.Config[self._section]['ScriptDirectory'])  # resolve entry

		if (not scriptPath.exists()):
			raise ConfigurationException("{0!s} script directory '{1!s}' does not exist.".format(self, scriptPath)) \
				from NotADirectoryError(str(scriptPath))

	def __WriteGHDLSection(self, binPath):
		if (self._host.Platform == "Windows"):
			ghdlPath = binPath / "ghdl.exe"
		else:
			ghdlPath = binPath / "ghdl"

		if not ghdlPath.exists():
			raise ConfigurationException("Executable '{0!s}' not found.".format(ghdlPath)) from FileNotFoundError(
				str(ghdlPath))

		# get version and backend
		output = check_output([str(ghdlPath), "-v"], universal_newlines=True)
		version = None
		backend = None
		versionRegExpStr = r"^GHDL (.+?) "
		versionRegExp = re_compile(versionRegExpStr)
		backendRegExpStr = r"(?i).*(mcode|gcc|llvm).* code generator"
		backendRegExp = re_compile(backendRegExpStr)
		for line in output.split('\n'):
			if version is None:
				match = versionRegExp.match(line)
				if match is not None:
					version = match.group(1)

			if backend is None:
				match = backendRegExp.match(line)
				if match is not None:
					backend = match.group(1).lower()

		if ((version is None) or (backend is None)):
			raise ConfigurationException("Version number or back-end name not found in '{0!s} -v' output.".format(ghdlPath))

		self._host.Config[self._section]['Version'] = version
		self._host.Config[self._section]['Backend'] = backend


class GHDL(OutputFilteredExecutable, ToolMixIn):
	def __init__(self, platform, dryrun, binaryDirectoryPath, version, backend, logger=None):
		ToolMixIn.__init__(self, platform, dryrun, binaryDirectoryPath, version, logger=logger)

		if (platform == "Windows"):             executablePath = binaryDirectoryPath / "ghdl.exe"
		elif (platform.startswith("MINGW32")):  executablePath = binaryDirectoryPath / "ghdl.exe"
		elif (platform.startswith("MINGW64")):  executablePath = binaryDirectoryPath / "ghdl.exe"
		elif (platform == "Linux"):             executablePath = binaryDirectoryPath / "ghdl"
		elif (platform == "Darwin"):            executablePath = binaryDirectoryPath / "ghdl"
		else:                                   raise PlatformNotSupportedException(platform)
		super().__init__(platform, dryrun, executablePath, logger=logger)

		self.Executable = executablePath
		#self.Parameters[self.Executable] = executablePath

		if (platform == "Windows"):
			if (backend not in ["llvm", "mcode"]):        raise GHDLException("GHDL for Windows does not support backend '{0}'.".format(backend))
		elif (platform == "Linux"):
			if (backend not in ["gcc", "llvm", "mcode"]): raise GHDLException("GHDL for Linux does not support backend '{0}'.".format(backend))
		elif (platform == "Darwin"):
			if (backend not in ["gcc", "llvm", "mcode"]): raise GHDLException("GHDL for OS X does not support backend '{0}'.".format(backend))

		self._binaryDirectoryPath =  binaryDirectoryPath
		self._backend =              backend
		self._version =              version

	@property
	def BinaryDirectoryPath(self):  return self._binaryDirectoryPath
	@property
	def Backend(self):              return self._backend
	@property
	def Version(self):              return self._version

	def deco(Arg):
		def getter(_):
			return Arg.Value
		def setter(_, value):
			Arg.Value = value
		return property(getter, setter)

	Executable = deco(ExecutableArgument("Executable", (), {}))

	#class Executable(metaclass=ExecutableArgument):
	#	pass

	class CmdAnalyze(metaclass=ShortFlagArgument):
		_name =    "a"

	class CmdElaborate(metaclass=ShortFlagArgument):
		_name =    "e"

	class CmdRun(metaclass=ShortFlagArgument):
		_name =    "r"

	class FlagVerbose(metaclass=ShortFlagArgument):
		_name =    "v"

	class FlagDebug(metaclass=ShortFlagArgument):
		_name =    "g"

	class FlagExplicit(metaclass=ShortFlagArgument):
		_name =    "fexplicit"

	class FlagRelaxedRules(metaclass=ShortFlagArgument):
		_name =    "frelaxed-rules"

	class FlagWarnBinding(metaclass=LongFlagArgument):
		_name =    "warn-binding"

	class FlagNoVitalChecks(metaclass=LongFlagArgument):
		_name =    "no-vital-checks"

	class FlagMultiByteComments(metaclass=LongFlagArgument):
		_name =    "mb-comments"

	class FlagSynBinding(metaclass=LongFlagArgument):
		_name =    "syn-binding"

	class FlagPSL(metaclass=ShortFlagArgument):
		_name =    "fpsl"

	class FlagProfileArcs(metaclass=ShortFlagArgument):
		_name =    "fprofile-arcs"

	class FlagTestCoverage(metaclass=ShortFlagArgument):
		_name =    "ftest-coverage"

	class SwitchCompilerOption(metaclass=ValuedFlagListArgument):
		_pattern =  "-{0},{1}"
		_name =     "Wc"

	class SwitchAssemblerOption(metaclass=ValuedFlagListArgument):
		_pattern =  "-{0},{1}"
		_name =     "Wa"

	class SwitchLinkerOption(metaclass=ValuedFlagListArgument):
		_pattern =  "-{0},{1}"
		_name =     "Wl"

	class SwitchIEEEFlavor(metaclass=LongValuedFlagArgument):
		_name =     "ieee"

	class SwitchVHDLVersion(metaclass=LongValuedFlagArgument):
		_name =     "std"

	class SwitchVHDLLibrary(metaclass=LongValuedFlagArgument):
		_name =     "work"

	class ArgListLibraryReferences(metaclass=ValuedFlagListArgument):
		_pattern =  "-{0}{1}"
		_name =     "P"

	class ArgSourceFile(metaclass=PathArgument):
		pass

	class ArgTopLevel(metaclass=StringArgument):
		pass

	Parameters = CommandLineArgumentList(
		#Executable,
		CmdAnalyze,
		CmdElaborate,
		CmdRun,
		FlagVerbose,
		FlagDebug,
		FlagExplicit,
		FlagRelaxedRules,
		FlagWarnBinding,
		FlagNoVitalChecks,
		FlagMultiByteComments,
		FlagSynBinding,
		FlagPSL,
		FlagProfileArcs,
		FlagTestCoverage,
		SwitchCompilerOption,
		SwitchAssemblerOption,
		SwitchLinkerOption,
		SwitchIEEEFlavor,
		SwitchVHDLVersion,
		SwitchVHDLLibrary,
		ArgListLibraryReferences,
		ArgSourceFile,
		ArgTopLevel
	)

	class SwitchIEEEAsserts(metaclass=LongValuedFlagArgument):
		_name =     "ieee-asserts"

	class SwitchStopDelta(metaclass=LongValuedFlagArgument):
		_name =     "stop-delta"

	class SwitchVCDWaveform(metaclass=LongValuedFlagArgument):
		_name =     "vcd"

	class SwitchVCDGZWaveform(metaclass=LongValuedFlagArgument):
		_name =     "vcdgz"

	class SwitchFastWaveform(metaclass=LongValuedFlagArgument):
		_name =     "fst"

	class SwitchGHDLWaveform(metaclass=LongValuedFlagArgument):
		_name =     "wave"

	class SwitchWaveformOptionFile(metaclass=LongValuedFlagArgument):
		_name =     "read-wave-opt"		# requires GHDL update

	RunOptions = CommandLineArgumentList(
		SwitchIEEEAsserts,
		SwitchStopDelta,
		SwitchVCDWaveform,
		SwitchVCDGZWaveform,
		SwitchFastWaveform,
		SwitchGHDLWaveform,
		SwitchWaveformOptionFile
	)

	def GetGHDLAnalyze(self):
		ghdl = GHDLAnalyze(self._platform, self._dryrun, self._binaryDirectoryPath, self._version, self._backend, logger=self._logger)
		for param in ghdl.Parameters:
			if (param is not ghdl.Executable):
				ghdl.Parameters[param] =       None
		ghdl.Parameters[ghdl.CmdAnalyze] = True
		return ghdl

	def GetGHDLElaborate(self):
		ghdl = GHDLElaborate(self._platform, self._dryrun, self._binaryDirectoryPath, self._version, self._backend, logger=self._logger)
		for param in ghdl.Parameters:
			if (param is not ghdl.Executable):
				ghdl.Parameters[param] =         None
		ghdl.Parameters[ghdl.CmdElaborate] = True
		return ghdl

	def GetGHDLRun(self):
		ghdl = GHDLRun(self._platform, self._dryrun, self._binaryDirectoryPath, self._version, self._backend, logger=self._logger)
		for param in ghdl.Parameters:
			if (param is not ghdl.Executable):
				ghdl.Parameters[param] =        None
		ghdl.Parameters[ghdl.CmdRun] =      True
		return ghdl


class GHDLAnalyze(GHDL):
	def __init__(self, platform, dryrun, binaryDirectoryPath, version, backend, logger=None):
		super().__init__(platform, dryrun, binaryDirectoryPath, version, backend, logger=logger)

	def Analyze(self):
		parameterList = self.Parameters.ToArgumentList()
		parameterList.insert(0, self.Executable)
		self.LogVerbose("command: {0}".format(" ".join(parameterList)))

		try:
			self.StartProcess(parameterList)
		except Exception as ex:
			raise GHDLException("Failed to launch GHDL analyze.") from ex

		self._hasOutput =    False
		self._hasWarnings =  False
		self._hasErrors =    False
		try:
			iterator = iter(GHDLAnalyzeFilter(self.GetReader()))

			line = next(iterator)
			self._hasOutput =    True
			self.LogNormal("ghdl analyze messages for '{0}'".format(self.Parameters[self.ArgSourceFile]), indent=1)
			self.LogNormal(("-" * (78 - self.Logger.BaseIndent*2)), indent=1)

			while True:
				self._hasWarnings |=  (line.Severity is Severity.Warning)
				self._hasErrors |=    (line.Severity is Severity.Error)

				line.IndentBy(self.Logger.BaseIndent + 1)
				self.Log(line)
				line = next(iterator)

		except DryRunException:
			pass
		except StopIteration:
			pass
		finally:
			if self._hasOutput:
				self.LogNormal(("-" * (78 - self.Logger.BaseIndent*2)), indent=1)


class GHDLElaborate(GHDL):
	def __init__(self, platform, dryrun, binaryDirectoryPath, version, backend, logger=None):
		super().__init__(platform, dryrun, binaryDirectoryPath, version, backend, logger=logger)

	def Elaborate(self):
		parameterList = self.Parameters.ToArgumentList()
		parameterList.insert(0, self.Executable)
		self.LogVerbose("command: {0}".format(" ".join(parameterList)))

		try:
			self.StartProcess(parameterList)
		except Exception as ex:
			raise GHDLException("Failed to launch GHDL elaborate.") from ex

		self._hasOutput = False
		self._hasWarnings = False
		self._hasErrors = False
		try:
			iterator = iter(GHDLElaborateFilter(self.GetReader()))

			line = next(iterator)
			line.IndentBy(self.Logger.BaseIndent + 1)
			self._hasOutput = True
			vhdlLibraryName = self.Parameters[self.SwitchVHDLLibrary]
			topLevel = self.Parameters[self.ArgTopLevel]
			self.LogNormal("ghdl elaborate messages for '{0}.{1}'".format(vhdlLibraryName, topLevel), indent=1)
			self.LogNormal(("-" * (78 - self.Logger.BaseIndent*2)), indent=1)
			self.Log(line)

			while True:
				self._hasWarnings |= (line.Severity is Severity.Warning)
				self._hasErrors |= (line.Severity is Severity.Error)

				line = next(iterator)
				line.IndentBy(self.Logger.BaseIndent + 1)
				self.Log(line)

		except DryRunException:
			pass
		except StopIteration:
			pass
		finally:
			if self._hasOutput:
				self.LogNormal(("-" * (78 - self.Logger.BaseIndent*2)), indent=1)


class GHDLRun(GHDL):
	def __init__(self, platform, dryrun, binaryDirectoryPath, version, backend, logger=None):
		super().__init__(platform, dryrun, binaryDirectoryPath, version, backend, logger=logger)

	def Run(self):
		parameterList = self.Parameters.ToArgumentList()
		parameterList += self.RunOptions.ToArgumentList()
		parameterList.insert(0, self.Executable)
		self.LogVerbose("command: {0}".format(" ".join(parameterList)))

		try:
			self.StartProcess(parameterList)
		except Exception as ex:
			raise GHDLException("Failed to launch GHDL run.") from ex

		self._hasOutput =    False
		self._hasWarnings =  False
		self._hasErrors =    False
		simulationResult =  CallByRefParam(SimulationResult.Error)
		try:
			iterator = iter(PoCSimulationResultFilter(GHDLRunFilter(self.GetReader()), simulationResult))

			line = next(iterator)
			line.IndentBy(self.Logger.BaseIndent + 1)
			self._hasOutput = True
			vhdlLibraryName =  self.Parameters[self.SwitchVHDLLibrary]
			topLevel =        self.Parameters[self.ArgTopLevel]
			self.LogNormal("ghdl run messages for '{0}.{1}'".format(vhdlLibraryName, topLevel), indent=1)
			self.LogNormal("-" * 78, indent=1)
			self.Log(line)

			while True:
				self._hasWarnings |= (line.Severity is Severity.Warning)
				self._hasErrors |= (line.Severity is Severity.Error)

				line = next(iterator)
				line.IndentBy(self.Logger.BaseIndent + 1)
				self.Log(line)

		except DryRunException:
			simulationResult <<= SimulationResult.DryRun
		except StopIteration:
			pass
		finally:
			if self._hasOutput:
				self.LogNormal("-" * 78, indent=1)

		return simulationResult.value


def GHDLAnalyzeFilter(gen):
	filterPattern = r".+?:\d+:\d+:(?P<warning>warning:)? (?P<message>.*)"			# <Path>:<line>:<column>:[warning:] <message>
	filterRegExp  = re_compile(filterPattern)

	for line in gen:
		filterMatch = filterRegExp.match(line)
		if ("ghdl: compilation error" in line):
			yield LogEntry(line, Severity.Error)
			continue
		elif (filterMatch is not None):
			if (filterMatch.group('warning') is not None):
				yield LogEntry(line, Severity.Warning)
				continue

			message = filterMatch.group('message')
			if message.endswith("has changed and must be reanalysed"):
				raise GHDLReanalyzeException(message)
			yield LogEntry(line, Severity.Error)
			continue

		yield LogEntry(line, Severity.Normal)

GHDLElaborateFilter = GHDLAnalyzeFilter

def GHDLRunFilter(gen):
	#  Pattern                                                             Classification
	# ------------------------------------------------------------------------------------------------------
	#  <path>:<line>:<column>: <message>                                -> Severity.Error (by (*))
	#  <path>:<line>:<column>:<severity>: <message>                     -> According to <severity>
	#  <path>:<line>:<column>:@<time>:(report <severity>): <message>    -> According to <severity>
	#  others                                                           -> Severity.Normal
	#  (*) -> unknown <severity>                                        -> Severity.Error

	filterPattern = r".+?:\d+:\d+:((?P<report>@\w+:\((?:report|assertion) )?(?P<severity>\w+)(?(report)\)):)? (?P<message>.*)"
	filterRegExp = re_compile(filterPattern)

	lineno = 0
	for line in gen:
		if (lineno < 2):
			lineno += 1
			if ("Linking in memory" in line):
				yield LogEntry(line, Severity.Verbose)
				continue
			if ("Starting simulation" in line):
				yield LogEntry(line, Severity.Verbose)
				continue

		filterMatch = filterRegExp.match(line)
		if filterMatch is not None:
			yield LogEntry(line, Severity.ParseVHDLSeverityLevel(filterMatch.group('severity'), Severity.Error))
			continue

		yield LogEntry(line, Severity.Normal)
