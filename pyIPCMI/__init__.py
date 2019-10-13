# EMACS settings: -*-  tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:              Patrick Lehmann
#
# Python Sub Module:    Saves the pyIPCMI configuration as python source code.
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
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
#
from argparse       import RawDescriptionHelpFormatter
from configparser   import DuplicateOptionError
from datetime       import datetime
from os             import environ
from pathlib        import Path
from platform       import system as platform_system
from shutil         import copy as shutil_copy
from textwrap       import dedent, wrap

from pyExceptions                     import ExceptionBase, PlatformNotSupportedException, EnvironmentException, NotConfiguredException
from pyAttributes                     import Attribute
from pyAttributes.ArgParseAttributes  import ArgParseMixin
from pyAttributes.ArgParseAttributes  import CommandAttribute, CommandGroupAttribute, ArgumentAttribute, SwitchArgumentAttribute, DefaultAttribute
from pyAttributes.ArgParseAttributes  import CommonArgumentAttribute, CommonSwitchArgumentAttribute
from pyExtendedConfigParser           import ExtendedConfigParser

__author__ =      "Patrick Lehmann, " + \
                  "Martin Zabel"
__copyright__ =   "Copyright 2017-2019 Patrick Lehmann - Bötzingen, Germany\n" + \
                  "Copyright 2007-2016 Technische Universität Dresden - Germany, Chair of VLSI-Design, Diagnostics and Architecture"
__maintainer__ =  "Patrick Lehmann"
__email__ =       "Patrick.Lehmann@plc2.de"
__version__ =     "1.1.2"
__status__ =      "Production"
__license__ =     "Apache License 2.0"
__api__ = [
	'pyIPCMIEntityAttribute',
	'BoardDeviceAttributeGroup',
	'VHDLVersionAttribute',
	'SimulationStepsAttributeGroup',
	'CompileStepsAttributeGroup',
	'IPCoreManagementInfrastructure'
]
__all__ = __api__

def printImportError(ex):
	platform = platform_system()
	print("IMPORT ERROR: One or more Python packages are not available in your environment.")
	print("Missing package: '{0}'\n".format(ex.name))
	if (platform == "Windows"): print("Run: 'py.exe -3 -m pip install -r requirements.txt'\n")
	elif (platform == "Linux"): print("Run: 'python3 -m pip install -r requirements.txt'\n")
	exit(1)

try:
	from lib.Functions                              import Init, Exit
	from lib.Terminal                               import Terminal
	from pyIPCMI.Compiler                           import CompilerException, CompileSteps
	from pyIPCMI.Base.Exceptions                    import CommonException
	from pyIPCMI.Base.Logging                       import ILogable, Logger, Severity
	from pyIPCMI.Base.Project                       import VHDLVersion
	from pyIPCMI.Compiler.LSECompiler               import Compiler as LSECompiler
	from pyIPCMI.Compiler.QuartusCompiler           import Compiler as MapCompiler
	from pyIPCMI.Compiler.ISECompiler               import Compiler as ISECompiler
	from pyIPCMI.Compiler.XCICompiler               import Compiler as XCICompiler
	from pyIPCMI.Compiler.XCOCompiler               import Compiler as XCOCompiler
	from pyIPCMI.Compiler.XSTCompiler               import Compiler as XSTCompiler
	from pyIPCMI.Compiler.VivadoCompiler            import Compiler as VivadoCompiler
	from pyIPCMI.DataBase                           import Query
	from pyIPCMI.DataBase.Config                    import Board
	from pyIPCMI.DataBase.Entity                    import NamespaceRoot, FQN, EntityTypes, WildCard, TestbenchKind, NetlistKind
	from pyIPCMI.DataBase.Solution                  import Repository
	from pyIPCMI.Simulator                          import Simulator as BaseSimulator, SimulatorException, SimulationSteps
	from pyIPCMI.Simulator.ActiveHDLSimulator       import Simulator as ActiveHDLSimulator
	from pyIPCMI.Simulator.RivieraPROSimulator      import Simulator as RivieraPROSimulator
	from pyIPCMI.Simulator.CocotbSimulator          import Simulator as CocotbSimulator
	from pyIPCMI.Simulator.GHDLSimulator            import Simulator as GHDLSimulator
	from pyIPCMI.Simulator.ISESimulator             import Simulator as ISESimulator
	from pyIPCMI.Simulator.ModelSimSimulator        import Simulator as QuestaSimulator
	from pyIPCMI.Simulator.VivadoSimulator          import Simulator as VivadoSimulator
	from pyIPCMI.ToolChain                          import ToolChainException, Configurator, ConfigurationException
	from pyIPCMI.ToolChain.GHDL                     import Configuration as GHDLConfiguration
except ImportError as ex:
	printImportError(ex)


class pyIPCMIEntityAttribute(Attribute):
	def __call__(self, func):
		self._AppendAttribute(func, ArgumentAttribute(metavar="pyIPCMI Entity", dest="FQN", type=str, nargs='+', help="A space separated list of pyIPCMI entities."))
		return func


class BoardDeviceAttributeGroup(Attribute):
	def __call__(self, func):
		self._AppendAttribute(func, ArgumentAttribute("--device", metavar="DeviceName", dest="DeviceName", help="The target platform's device name."))
		self._AppendAttribute(func, ArgumentAttribute("--board", metavar="BoardName", dest="BoardName", help="The target platform's board name."))
		return func


class VHDLVersionAttribute(Attribute):
	def __call__(self, func):
		self._AppendAttribute(func, ArgumentAttribute("--std", metavar="VHDLVersion", dest="VHDLVersion", help="Simulate with VHDL-??"))
		return func


class SimulationStepsAttributeGroup(Attribute):
	def __call__(self, func):
		self._AppendAttribute(func, SwitchArgumentAttribute("-g", "--gui",          dest="GUIMode",       help="Run all steps (prepare, analysis, elaboration, optimization, simulation) and finally display the waveform in a GUI window."))
		self._AppendAttribute(func, SwitchArgumentAttribute("-a", "--analyze",      dest="Analyze",       help="Run only the prepare and analysis step."))
		self._AppendAttribute(func, SwitchArgumentAttribute("-e", "--elaborate",    dest="Elaborate",     help="Run only the prepare and elaboration step."))
		# self._AppendAttribute(func, SwitchArgumentAttribute("-c", "--compile",      dest="Compile",       help="Run only the prepare and compile step."))
		# self._AppendAttribute(func, SwitchArgumentAttribute("-o", "--optimize",     dest="Optimize",      help="Run only the prepare and optimization step."))
		self._AppendAttribute(func, SwitchArgumentAttribute("-R", "--recompile",    dest="Recompile",     help="Run all compile steps (prepare, analysis, elaboration, optimization)."))
		self._AppendAttribute(func, SwitchArgumentAttribute("-s", "--simulate",     dest="Simulate",      help="Run only the prepare and simulation step."))
		self._AppendAttribute(func, SwitchArgumentAttribute("-w", "--showwave",     dest="ShowWave",      help="Run only the prepare step and display the waveform in a GUI window."))
		self._AppendAttribute(func, SwitchArgumentAttribute("-C", "--showcoverage", dest="ShowCoverage",  help="Run only the prepare step and display the coverage data in a GUI window."))
		self._AppendAttribute(func, SwitchArgumentAttribute("-W", "--review",       dest="Review",        help="Run only display the waveform in a GUI window."))
		self._AppendAttribute(func, SwitchArgumentAttribute("-S", "--resimulate",   dest="Resimulate",    help="Run all simulation steps (prepare, simulation) and finally display the waveform in a GUI window."))
		self._AppendAttribute(func, SwitchArgumentAttribute("-r", "--showreport",   dest="ShowReport",    help="Show a simulation report."))
		# self._AppendAttribute(func, SwitchArgumentAttribute(      "--cleanup-after",  dest="CleanUpAfter",  help="Don't delete intermediate files. Skip post-delete rules."))
		return func


class CompileStepsAttributeGroup(Attribute):
	def __call__(self, func):
		self._AppendAttribute(func, SwitchArgumentAttribute("-s", "--synthesize", dest="Synthesize", help="Run only the prepare and synthesize step."))
		# merge
		# place
		# route
		# bitfile
		self._AppendAttribute(func, SwitchArgumentAttribute("-r", "--showreport", dest="ShowReport", help="Show a simulation report."))
		self._AppendAttribute(func, SwitchArgumentAttribute(      "--no-cleanup", dest="NoCleanUp",  help="Don't delete intermediate files. Skip post-delete rules."))
		return func


class IPCoreManagementInfrastructure(ILogable, ArgParseMixin):
	HeadLine =                "pyIPCMI - Service Tool"

	# configure hard coded variables here
	__CONFIGFILE_PRIVATE =    "config.private.ini"
	__CONFIGFILE_DEFAULTS =   "config.defaults.ini"
	__CONFIGFILE_BOARDS =     "config.boards.ini"
	__CONFIGFILE_STRUCTURE =  "config.structure.ini"
	__CONFIGFILE_IPCORES =    "config.entity.ini"

	# load platform information (Windows, Linux, Darwin, ...)
	__PLATFORM =              platform_system()

	# records
	class __Directories__:
		"""Data structure for all main directories.

		WORKAROUND: All members are initialized with empty :py:class:`pathlib.Path`
		instances, until Python 3.6 with type hints gets the default Python version.
		"""
		Working =     Path()
		Root =        Path()
#		PyIPCMIRoot = Path()
		ConfigFiles = Path()
		Solution =    Path()
		Project =     Path()
		Source =      Path()
		Testbench =   Path()
		Netlist =     Path()
		Temp =        Path()
		PreCompiled = Path()

	class __ConfigFiles__:
		"""Data structure for all configuration files.

		WORKAROUND: All members are initialized with empty :py:class:`pathlib.Path`
		instances, until Python 3.6 with type hints gets the default Python version.
		"""
		Private =     Path()
		Defaults =    Path()
		Boards =      Path()
		Structure =   Path()
		IPCores =     Path()
		Solution =    Path()
		Project =     Path()


	def __init__(self, debug, verbose, quiet, dryRun, sphinx=False):
		# Call the initializer of ILogable
		# --------------------------------------------------------------------------
		if quiet:      severity = Severity.Quiet
		elif debug:    severity = Severity.Debug
		elif verbose:  severity = Severity.Verbose
		else:          severity = Severity.Normal

		logger = Logger(severity, printToStdOut=True)
		ILogable.__init__(self, logger=logger)

		# Call the constructor of the ArgParseMixin
		# --------------------------------------------------------------------------
		(terminalWidth, _) = Terminal.GetTerminalSize()
		textWidth = min(terminalWidth, 160)
		description = dedent("""\
			IP Core Management Infrastructure (IPCMI) front end for <LibraryName>.
			""")
		epilog = "\n".join(wrap(dedent("""\
		  PoC - “Pile of Cores” provides implementations for often required hardware functions such as Arithmetic Units, Caches, Clock-Domain-Crossing Circuits, FIFOs, RAM wrappers, and I/O Controllers. The hardware modules are typically provided as VHDL or Verilog source code, so it can be easily re-used in a variety of hardware designs.

		  All hardware modules use a common set of VHDL packages to share new VHDL types, sub-programs and constants. Additionally, a set of simulation helper packages eases the writing of testbenches. Because PoC hosts a huge amount of IP cores, all cores are grouped into sub-namespaces to build a better hierarchy.

		  Various simulation and synthesis tool chains are supported to interoperate with PoC. To generalize all supported free and commercial vendor tool chains, PoC is shipped with a Python based infrastructure to offer a command line based frontend.
		  """), textWidth, replace_whitespace=False))


		class HelpFormatter(RawDescriptionHelpFormatter):
			def __init__(self, *args, **kwargs):
				kwargs['max_help_position'] = 25
				kwargs['width'] =             textWidth
				super().__init__(*args, **kwargs)

		ArgParseMixin.__init__(self, description=description, epilog=epilog, formatter_class=HelpFormatter, add_help=False)
		if sphinx: return

		# Do some basic checks
		(libraryName, libraryRootDirectory, ConfigDirectory) = self.__CheckEnvironment()

		# declare members
		# --------------------------------------------------------------------------
		self.__dryRun =       dryRun
		self.LibraryName =    libraryName
		self.LibraryKey =     "INSTALL." + libraryName
		self.__config =       None
		self.__root =         None
		self.__repo =         None
		self.__directories =  {}

		self.__SimulationDefaultVHDLVersion = BaseSimulator.VHDL_VERSION
		self.__SimulationDefaultBoard =       None

		self._directories =             self.__Directories__()
		self._directories.Working =     Path.cwd()
		self._directories.Root =        Path(libraryRootDirectory)
#		self._directories.PyIPCMIRoot = Path(pyIPCMIRootDirectory)
		self._directories.ConfigFiles = Path(ConfigDirectory)

		self._configFiles =             self.__ConfigFiles__()
		self._configFiles.Private =     self.Directories.ConfigFiles / self.__CONFIGFILE_PRIVATE
		self._configFiles.Defaults =    self.Directories.ConfigFiles / self.__CONFIGFILE_DEFAULTS
		self._configFiles.Boards =      self.Directories.ConfigFiles / self.__CONFIGFILE_BOARDS
		self._configFiles.Structure =   self.Directories.ConfigFiles / self.__CONFIGFILE_STRUCTURE
		self._configFiles.IPCores =     self.Directories.ConfigFiles / self.__CONFIGFILE_IPCORES

		self.__config =                 ExtendedConfigParser()
		self.Config.optionxform =       str

	# class properties
	# ============================================================================
	@property
	def Platform(self):           return self.__PLATFORM
	@property
	def DryRun(self):             return self.__dryRun

	@property
	def Directories(self):        return self._directories
	@property
	def ConfigFiles(self):        return self._configFiles

	@property
	def Config(self):             return self.__config
	@property
	def Root(self):               return self.__root
	@property
	def Repository(self):         return self.__repo

	def __CheckEnvironment(self):
		if not ((self.Platform in ["Windows", "Linux", "Darwin"]) or
		        self.Platform.startswith("MINGW64_NT") or
		        self.Platform.startswith("MINGW32_NT")):
			raise PlatformNotSupportedException(self.Platform)

		libraryName =             environ.get('Library')
		libraryRootDirectory =    environ.get('LibraryRootDirectory')
		pyIPCMIConfigDirectory =  environ.get('pyIPCMIConfigDirectory')

		if (libraryName is None):             raise EnvironmentException("Shell environment does not provide 'Library' variable.")
		if (libraryRootDirectory is None):    raise EnvironmentException("Shell environment does not provide 'LibraryRootDirectory' variable.")
		if (pyIPCMIConfigDirectory is None):  raise EnvironmentException("Shell environment does not provide 'pyIPCMIConfigDirectory' variable.")

		return (libraryName, libraryRootDirectory, pyIPCMIConfigDirectory)

	# read pyIPCMI configuration
	# ============================================================================
	def __ReadConfiguration(self):
		self.LogVerbose("Reading configuration files...")

		configFiles = [
			(self.ConfigFiles.Private,		"private"),
			(self.ConfigFiles.Defaults,		"defaults"),
			(self.ConfigFiles.Boards,			"boards"),
			(self.ConfigFiles.Structure,	"structure"),
			(self.ConfigFiles.IPCores,		"IP core")
		]

		# create parser instance
		self.LogDebug("Reading pyIPCMI configuration from:")

		try:
			# process first file (private)
			file, name = configFiles[0]
			self.LogDebug("  {0!s}".format(file))
			if not file.exists():  raise NotConfiguredException("pyIPCMI's {0} configuration file '{1!s}' does not exist.".format(name, file))  from FileNotFoundError(str(file))
			self.Config.read(str(file))

			for file, name in configFiles[1:]:
				self.LogDebug("  {0!s}".format(file))
				if not file.exists():  raise ConfigurationException("pyIPCMI's {0} configuration file '{1!s}' does not exist.".format(name, file))  from FileNotFoundError(str(file))
				self.Config.read(str(file))
		except DuplicateOptionError as ex:
			raise ConfigurationException("Error in configuration file '{0!s}'.".format(file)) from ex

		# check pyIPCMI installation directory
		installationDirectory = Path(self.Config[self.LibraryKey]['InstallationDirectory'])
		# WORKAROUND: Bug in pathlib. It doesn't compare absolute paths of Windows and MinGW: 'C:\' vs. '/c/'.
		if ((self.Directories.Root != installationDirectory) and not (self.Platform.startswith("MINGW"))):
			raise NotConfiguredException("There is a mismatch between pyIPCMIRoot ('{0}') and pyIPCMI's installation directory ('{1}').".format(
				self.Directories.Root, installationDirectory
			))

		# parsing values into class fields
		configSection =                 self.Config['CONFIG.DirectoryNames']
		self.Directories.Source =       self.Directories.Root / configSection['HDLSourceFiles']
		self.Directories.Testbench =    self.Directories.Root / configSection['TestbenchFiles']
		self.Directories.NetList =      self.Directories.Root / configSection['NetlistFiles']
		self.Directories.Temp =         self.Directories.Root / configSection['TemporaryFiles']
		self.Directories.PreCompiled =  self.Directories.Root / configSection['PrecompiledFiles']

		# Initialize the default board (GENERIC)
		self.__SimulationDefaultBoard = Board(self)

		# Initialize pyIPCMI's namespace structure
		self.__root = NamespaceRoot(self)
		self.__repo = Repository(self)

	def __BackupConfiguration(self):
		now = datetime.now()
		backupFile = self._configFiles.Private.with_suffix(".{datetime}.ini".format(datetime=now.strftime("%Y.%m.%d-%H.%M.%S")))
		self.LogVerbose("Copying old configuration file to '{0!s}'.".format(backupFile, **Init.Foreground))
		self.LogDebug("cp {0!s} {1!s}".format(self._configFiles.Private, backupFile))
		try:
			shutil_copy(str(self._configFiles.Private), str(backupFile))
		except OSError as ex:
			raise ConfigurationException("Error while copying '{0!s}'.".format(self._configFiles.Private)) from ex

	def __WriteConfiguration(self):
		for sectionName in [sectionName for sectionName in self.Config if not (sectionName.startswith("INSTALL") or sectionName.startswith("SOLUTION"))]:
			self.Config.remove_section(sectionName)

		self.Config.remove_section("SOLUTION.DEFAULTS")

		# Writing configuration to disc
		self.LogNormal("{GREEN}Writing configuration file to '{0!s}'.{NOCOLOR}".format(self._configFiles.Private, **Init.Foreground))
		with self._configFiles.Private.open('w') as configFileHandle:
			self.Config.write(configFileHandle)

	def SaveAndReloadConfiguration(self):
		self.__WriteConfiguration()
		self.Config.clear()
		self.__ReadConfiguration()

	def __PrepareForConfiguration(self):
		self.__ReadConfiguration()

	def __PrepareForSimulation(self):
		self.LogNormal("Initializing pyIPCMI Service Tool for simulations")
		self.__ReadConfiguration()

	def __PrepareForSynthesis(self):
		self.LogNormal("Initializing pyIPCMI Service Tool for synthesis")
		self.__ReadConfiguration()

	# ============================================================================
	# Common commands
	# ============================================================================
	# common arguments valid for all commands
	# ----------------------------------------------------------------------------
	@CommonSwitchArgumentAttribute("-D",              dest="DEBUG",   help="Enable script wrapper debug mode. See also :option:`pyIPCMI.ps1 -D`.")
	@CommonSwitchArgumentAttribute(      "--dryrun",  dest="DryRun",  help="Don't execute external programs.")
	@CommonSwitchArgumentAttribute("-d", "--debug",   dest="debug",   help="Enable debug mode.")
	@CommonSwitchArgumentAttribute("-v", "--verbose", dest="verbose", help="Print out detailed messages.")
	@CommonSwitchArgumentAttribute("-q", "--quiet",   dest="quiet",   help="Reduce messages to a minimum.")
	@CommonArgumentAttribute("--sln", metavar="SolutionID", dest="SolutionID",  help="Solution name.")
	@CommonArgumentAttribute("--prj", metavar="ProjectID",  dest="ProjectID",   help="Project name.")
	def Run(self):
		ArgParseMixin.Run(self)

	def PrintHeadline(self):
		self.LogNormal("{HEADLINE}{line}{NOCOLOR}".format(line="="*80, **Init.Foreground))
		self.LogNormal("{HEADLINE}{headline: ^80s}{NOCOLOR}".format(headline=self.HeadLine, **Init.Foreground))
		self.LogNormal("{HEADLINE}{line}{NOCOLOR}".format(line="="*80, **Init.Foreground))

	# ----------------------------------------------------------------------------
	# fallback handler if no command was recognized
	# ----------------------------------------------------------------------------
	@DefaultAttribute()
	def HandleDefault(self, _):
		self.PrintHeadline()

		# print("Common arguments:")
		# for funcname,func in CommonArgumentAttribute.GetMethods(self):
		# 	for comAttribute in CommonArgumentAttribute.GetAttributes(func):
		# 		print("  {0}  {1}".format(comAttribute.Args, comAttribute.KWArgs['help']))
		#
		# 		self.__mainParser.add_argument(*(comAttribute.Args), **(comAttribute.KWArgs))
		#
		# for funcname,func in CommonSwitchArgumentAttribute.GetMethods(self):
		# 	for comAttribute in CommonSwitchArgumentAttribute.GetAttributes(func):
		# 		print("  {0}  {1}".format(comAttribute.Args, comAttribute.KWArgs['help']))

		self.MainParser.print_help()
		Exit.exit()

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "help" command
	# ----------------------------------------------------------------------------
	@CommandAttribute("help", help="Display help page(s) for the given command name.")
	@ArgumentAttribute(metavar="Command", dest="Command", type=str, nargs="?", help="Print help page(s) for a command.")
	def HandleHelp(self, args):
		self.PrintHeadline()
		if (args.Command is None):
			self.MainParser.print_help()
			Exit.exit()
		elif (args.Command == "help"):
			print("This is a recursion ...")
		else:
			self.SubParsers[args.Command].print_help()
		Exit.exit()

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "info" command
	# ----------------------------------------------------------------------------
	@CommandAttribute("info", help="Display tool and version information.")
	def HandleInfo(self, args):
		self.PrintHeadline()
		copyrights = __copyright__.split("\n", 1)
		self.LogNormal("Copyright:  {0}".format(copyrights[0]))
		self.LogNormal("            {0}".format(copyrights[1]))
		self.LogNormal("License:    {0}".format(__license__))
		authors = __author__.split(", ")
		self.LogNormal("Authors:    {0}".format(authors[0]))
		for author in authors[1:]:
			self.LogNormal("            {0}".format(author))
		self.LogNormal("Version:    {0}".format(__version__))
		Exit.exit()


	# ============================================================================
	# Configuration commands
	# ============================================================================
	# create the sub-parser for the "configure" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Configuration commands") # mccabe:disable=MC0001
	@CommandAttribute("configure", help="Configure vendor tools for pyIPCMI.")
	@ArgumentAttribute(metavar="ToolChain",         dest="ToolChain", type=str, nargs="?", help="Specify a tool chain to be configured.")
	@SwitchArgumentAttribute("--relocated",         dest="Relocated",                      help="Consistency check after pyIPCMI was relocated.")
	def HandleConfiguration(self, args):
		"""Handle 'configure' command."""
		self.PrintHeadline()

		if (self.Platform not in ["Darwin", "Linux", "Windows"]):    raise PlatformNotSupportedException(self.Platform)

		toolChain = args.ToolChain

		# load existing configuration or create a new one
		try:
			self.__ReadConfiguration()
			self.__BackupConfiguration()
			configurator = Configurator(self)
			configurator.UpdateConfiguration()
		except NotConfiguredException as ex:
			if (toolChain is None):
				self.LogWarning("No private configuration found. Generating an empty pyIPCMI configuration...")
				configurator = Configurator(self)
				configurator.InitializeConfiguration()
			else:
				raise ex

		if (args.Relocated is True):
			configurator.Relocated()
		else:
			if (toolChain is None):
				configurator.ConfigureAll()
			else:
				configurator.ConfigureTool(toolChain)

		if (self.Logger.LogLevel is Severity.Debug):
			self.LogDebug("Dumping Config...")
			self.LogDebug("-" * 40)
			for sectionName in self.Config.sections():
				if (not sectionName.startswith("INSTALL")):
					continue
				self.LogDebug("[{0}]".format(sectionName))
				configSection = self.Config[sectionName]
				for optionName in configSection:
					try:
						optionValue = configSection[optionName]
					except Exception:
						optionValue = "-- ERROR --"
					self.LogDebug("{0} = {1}".format(optionName, optionValue), indent=3)
			self.LogDebug("-" * 40)

	# create the sub-parser for the "select" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Configuration commands") # mccabe:disable=MC0001
	@CommandAttribute("select", help="Select the default tool for a tool chain.")
	# @ArgumentAttribute(metavar="ToolChain",         dest="ToolChain", type=str, nargs="?", help="Specify a tool chain to be configured.")
	def HandleSelection(self, args):
		"""Handle 'select' command."""
		self.PrintHeadline()

		if (self.Platform not in ["Darwin", "Linux", "Windows"]):    raise PlatformNotSupportedException(self.Platform)

		# load existing configuration or create a new one
		try:
			self.__ReadConfiguration()
			self.__BackupConfiguration()
			configurator = Configurator(self)
			configurator.UpdateConfiguration()
		except NotConfiguredException as ex:
			raise ex

		configurator.ConfigureDefaultTools()

		if (self.Logger.LogLevel is Severity.Debug):
			self.LogDebug("Dumping Config...")
			self.LogDebug("-" * 40)
			for sectionName in self.Config.sections():
				if (not sectionName.startswith("INSTALL")):
					continue
				self.LogDebug("[{0}]".format(sectionName))
				configSection = self.Config[sectionName]
				for optionName in configSection:
					try:
						optionValue = configSection[optionName]
					except Exception:
						optionValue = "-- ERROR --"
					self.LogDebug("{0} = {1}".format(optionName, optionValue), indent=3)
			self.LogDebug("-" * 40)

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "add-solution" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Configuration commands")
	@CommandAttribute("add-solution", help="Add a solution to pyIPCMI.", description=dedent("""\
		Add a solution to pyIPCMI.
		"""))
	def HandleAddSolution(self, _): #args
		self.PrintHeadline()
		self.__PrepareForConfiguration()

		self.LogNormal("Register a new solutions in pyIPCMI")
		self.LogNormal("Solution name: ", indent=1)
		solutionName = input()
		if (solutionName == ""):        raise ConfigurationException("Empty input. Aborting!")

		self.LogNormal("Solution id:   ", indent=1)
		solutionID = input()
		if (solutionID == ""):          raise ConfigurationException("Empty input. Aborting!")
		if (solutionID in self.__repo): raise ConfigurationException("Solution ID is already used.")

		self.LogNormal("Solution path: ", indent=1)
		solutionRootPath = input()
		if (solutionRootPath == ""):    raise ConfigurationException("Empty input. Aborting!")
		solutionRootPath = Path(solutionRootPath)

		if (not solutionRootPath.exists()):
			self.LogNormal("Path does not exists. Should it be created? [{CYAN}Y{NOCOLOR}/n]: ".format(**Init.Foreground), appendLinebreak=False)
			createPath = input()
			createPath = createPath if createPath != "" else "Y"
			if (createPath in ['n', 'N']):
				raise ConfigurationException("Cannot continue to register the new project, because '{0!s}' does not exist.".format(solutionRootPath))
			elif (createPath not in ['y', 'Y']):
				raise ConfigurationException("Unsupported choice '{0}'".format(createPath))

			try:
				solutionRootPath.mkdir(parents=True)
			except OSError as ex:
				raise ConfigurationException("Error while creating '{0!s}'.".format(solutionRootPath)) from ex

			self.__repo.AddSolution(solutionID, solutionName, solutionRootPath)
		self.__WriteConfiguration()
		self.LogNormal("Solution {GREEN}successfully{NOCOLOR} created.".format(**Init.Foreground))


	# ----------------------------------------------------------------------------
	# create the sub-parser for the "list-solution" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Configuration commands")
	@CommandAttribute("list-solution", help="List all solutions registered in pyIPCMI.", description=dedent("""\
		List all solutions registered in pyIPCMI.
		"""))
	def HandleListSolution(self, _): #args
		self.PrintHeadline()
		self.__PrepareForConfiguration()

		self.LogNormal("Registered solutions in pyIPCMI:")
		if self.__repo.Solutions:
			for solution in self.__repo.Solutions:
				self.LogNormal("  {id: <10}{name}".format(id=solution.ID, name=solution.Name))
				if (self.Logger.LogLevel <= Severity.Verbose):
					self.LogVerbose("  Path:   {path!s}".format(path=solution.Path))
					self.LogVerbose("  Projects:")
					for project in solution.Projects:
						self.LogVerbose("    {id: <6}{name}".format(id=project.ID, name=project.Name))
		else:
			self.LogNormal("  {RED}No registered solutions found.{NOCOLOR}".format(**Init.Foreground))

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "remove-solution" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Configuration commands")
	@CommandAttribute("remove-solution", help="Remove a solution from pyIPCMI.", description=dedent("""\
		Remove a solution from pyIPCMI.
		"""))
	@ArgumentAttribute(metavar="SolutionID", dest="SolutionID", type=str, help="Solution name.")
	def HandleRemoveSolution(self, args):
		self.PrintHeadline()
		self.__PrepareForConfiguration()

		solution = self.__repo[args.SolutionID]

		self.LogNormal("Removing solution '{0}'.".format(solution.Name))
		remove = input("Do you really want to remove this solution? [N/y]: ")
		remove = remove if remove != "" else "N"
		if (remove in ['n', 'N']):
			raise ConfigurationException("Operation canceled.")
		elif (remove not in ['y', 'Y']):
			raise ConfigurationException("Unsupported choice '{0}'".format(remove))

		self.__repo.RemoveSolution(solution)

		self.__WriteConfiguration()
		self.LogNormal("Solution {GREEN}successfully{NOCOLOR} removed.".format(**Init.Foreground))


	# ----------------------------------------------------------------------------
	# create the sub-parser for the "add-project" command
	# ----------------------------------------------------------------------------
	# @CommandGroupAttribute("Configuration commands")
	# @CommandAttribute("add-project", help="Add a project to pyIPCMI.")
	# def HandleAddProject(self, args):
	# 	self.PrintHeadline()
	# 	self.__PrepareForConfiguration()

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "list-project" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Configuration commands")
	@CommandAttribute("list-project", help="List all projects registered in pyIPCMI.", description=dedent("""\
		List all projects registered in pyIPCMI.
		"""))
	def HandleListProject(self, args):
		self.PrintHeadline()
		self.__PrepareForConfiguration()

		if (args.SolutionID is None):    raise ConfigurationException("Missing command line argument '--sln'.")
		try:
			solution =  self.__repo[args.SolutionID]
		except KeyError as ex:
			raise ConfigurationException("Solution ID '{0}' is not registered in pyIPCMI.".format(args.SolutionID)) from ex

		self.LogNormal("Registered projects for solution '{0}':".format(solution.ID))
		if solution.Projects:
			for project in solution.Projects:
				self.LogNormal("  {id: <10}{name}".format(id=project.ID, name=project.Name))
		else:
			self.LogNormal("  {RED}No registered projects found.{NOCOLOR}".format(**Init.Foreground))

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "remove-project" command
	# ----------------------------------------------------------------------------
	# @CommandGroupAttribute("Configuration commands")
	# @CommandAttribute("remove-project", help="Add a project to pyIPCMI.")
	# @ArgumentAttribute(metavar="Project", dest="Project", type=str, help="Project name.")
	# def HandleRemoveProject(self, args):
	# 	self.PrintHeadline()
	# 	self.__PrepareForConfiguration()

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "add-ipcore" command
	# ----------------------------------------------------------------------------
	# @CommandGroupAttribute("Configuration commands")
	# @CommandAttribute("add-ipcore", help="Add a ipcore to pyIPCMI.")
	# def HandleAddIPCore(self, args):
	# 	self.PrintHeadline()
	# 	self.__PrepareForConfiguration()

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "list-ipcore" command
	# ----------------------------------------------------------------------------
	# @CommandGroupAttribute("Configuration commands")
	# @CommandAttribute("list-ipcore", help="List all ipcores registered in pyIPCMI.")
	# def HandleListIPCore(self, args):
	# 	self.PrintHeadline()
	# 	self.__PrepareForConfiguration()
	#
	# 	ipcore = Solution(self)
	#
	# 	self.LogNormal("Registered ipcores in pyIPCMI:")
	# 	for ipcoreName in ipcore.GetIPCoreNames():
	# 		print("  {0}".format(ipcoreName))

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "remove-ipcore" command
	# ----------------------------------------------------------------------------
	# @CommandGroupAttribute("Configuration commands")
	# @CommandAttribute("remove-ipcore", help="Add a ipcore to pyIPCMI.")
	# @ArgumentAttribute(metavar="IPCore", dest="IPCore", type=str, help="IPCore name.")
	# def HandleRemoveIPCore(self, args):
	# 	self.PrintHeadline()
	# 	self.__PrepareForConfiguration()

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "add-testbench" command
	# ----------------------------------------------------------------------------
	# @CommandGroupAttribute("Configuration commands")
	# @CommandAttribute("add-testbench", help="Add a testbench to pyIPCMI.")
	# def HandleAddTestbench(self, args):
	# 	self.PrintHeadline()
	# 	self.__PrepareForConfiguration()

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "remove-testbench" command
	# ----------------------------------------------------------------------------
	# @CommandGroupAttribute("Configuration commands")
	# @CommandAttribute("remove-testbench", help="Add a testbench to pyIPCMI.")
	# @ArgumentAttribute(metavar="Testbench", dest="Testbench", type=str, help="Testbench name.")
	# def HandleRemoveTestbench(self, args):
	# 	self.PrintHeadline()
	# 	self.__PrepareForConfiguration()

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "query" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Configuration commands")
	@CommandAttribute("query", help="Query pyIPCMI's database.", description=dedent("""\
		Query pyIPCMI's database.
		"""))
	@ArgumentAttribute(metavar="Query", dest="Query", type=str, help="todo help")
	def HandleQueryConfiguration(self, args):
		self.__PrepareForConfiguration()
		query = Query(self)
		try:
			result = query.QueryConfiguration(args.Query)
			print(result, end="")
			Exit.exit()
		except ConfigurationException as ex:
			print(str(ex), end="")
			Exit.exit(1)

	# ============================================================================
	# Simulation	commands
	# ============================================================================
	# TODO: Maybe required to self-compile libraries again or in the future
	# def __PrepareVendorLibraryPaths(self):
	# 	# prepare vendor library path for Altera
	# 	if (len(self.Config.options("INSTALL.Altera.Quartus")) != 0):
	# 		self.Directories["AlteraPrimitiveSource"] = Path(self.Config['INSTALL.Altera.Quartus']['InstallationDirectory']) / "eda/sim_lib"
	# 	# prepare vendor library path for Xilinx
	# 	if (len(self.Config.options("INSTALL.Xilinx.ISE")) != 0):
	# 		self.Directories["XilinxPrimitiveSource"] = Path(self.Config['INSTALL.Xilinx.ISE']['InstallationDirectory']) / "ISE/vhdl/src"
	# 	elif (len(self.Config.options("INSTALL.Xilinx.Vivado")) != 0):
	# 		self.Directories["XilinxPrimitiveSource"] = Path(self.Config['INSTALL.Xilinx.Vivado']['InstallationDirectory']) / "data/vhdl/src"

	def _ExtractBoard(self, BoardName, DeviceName, force=False):
		if (BoardName is not None):     return Board(self, BoardName)
		elif (DeviceName is not None):  return Board(self, "Custom", DeviceName)
		elif (force is True):           raise CommonException("Either a board name or a device name is required.")
		else:                           return self.__SimulationDefaultBoard

	def _ExtractFQNs(self, fqns, defaultLibrary=None, defaultType=EntityTypes.Testbench):
		if (len(fqns) == 0):            raise CommonException("No FQN given.")
		return [FQN(self, fqn, libraryName=defaultLibrary, defaultType=defaultType) for fqn in fqns]

	def _ExtractVHDLVersion(self, vhdlVersion, defaultVersion=None):
		if (defaultVersion is None):    defaultVersion = self.__SimulationDefaultVHDLVersion
		if (vhdlVersion is None):       return defaultVersion
		else:                           return VHDLVersion.Parse(vhdlVersion)

	def __CheckSection(self, sectionName, toolName):
		if (len(self.Config.options(sectionName)) == 0):    raise NotConfiguredException("{0} is not configured on this system.".format(toolName))
		sectionName = self.Config[sectionName]["SectionName"]
		if (len(self.Config.options(sectionName)) == 0):    raise NotConfiguredException("{0} is not configured on this system.".format(toolName))
		if self.Config.has_option(sectionName, "SectionName"):
			sectionName = self.Config[sectionName]["SectionName"]
			if (len(self.Config.options(sectionName)) == 0):  raise NotConfiguredException("{0} is not configured on this system.".format(toolName))

	# TODO: move to Configuration class in ToolChain.Aldec.ActiveHDL
	def _CheckActiveHDL(self):
		# check if Active-HDL is configure
		self.__CheckSection("INSTALL.ActiveHDL", "Active-HDL")

	# TODO: move to Configuration class in ToolChain.Aldec.RivieraPRO
	def _CheckRivieraPRO(self):
		# check if RivieraPRO is configure
		self.__CheckSection("INSTALL.Aldec.RivieraPRO", "Aldec Riviera-PRO")

	# TODO: move to Configuration class in ToolChain.Altera.Quartus
	def _CheckQuartus(self):
		# check if RivieraPRO is configure
		self.__CheckSection("INSTALL.Quartus", "Quartus")

	# TODO: move to Configuration class in ToolChain.Lattice.Diamond
	def _CheckDiamond(self):
		# check if RivieraPRO is configure
		self.__CheckSection("INSTALL.Lattice.Diamond", "Lattice Diamond")

	# TODO: move to Configuration class in ToolChain.ModelSim
	def _CheckModelSim(self):
		# check if ModelSim is configure
		self.__CheckSection("INSTALL.ModelSim", "ModelSim")

	# TODO: move to Configuration class in ToolChain.Xilinx.ISE
	def _CheckISE(self):
		# check if RivieraPRO is configure
		self.__CheckSection("INSTALL.Xilinx.ISE", "Xilinx ISE")

	# TODO: move to Configuration class in ToolChain.Xilinx.Vivado
	def _CheckVivado(self):
		# check if RivieraPRO is configure
		self.__CheckSection("INSTALL.Xilinx.Vivado", "Xilinx Vivado")

	# TODO: move to Configuration class in ToolChain.GHDL
	def _CheckGHDL(self):
		# check if GHDL is configure
		self.__CheckSection("INSTALL.GHDL", "GHDL")

	@staticmethod
	def _ExtractSimulationSteps(guiMode, analyze, elaborate, optimize, recompile, simulate, showWaveform, showCoverage, resimulate, showReport, cleanUp):
		simulationSteps = SimulationSteps.no_flags
		if (not (analyze or elaborate or optimize or recompile or simulate or resimulate or showWaveform or showCoverage)):
			simulationSteps |= SimulationSteps.Prepare | SimulationSteps.CleanUpBefore
			simulationSteps |= SimulationSteps.Analyze | SimulationSteps.Elaborate #| SimulationSteps.Optimize
			simulationSteps |= SimulationSteps.Simulate
			simulationSteps |= SimulationSteps.ShowWaveform & guiMode
			simulationSteps |= SimulationSteps.ShowCoverage & guiMode
			simulationSteps |= SimulationSteps.ShowReport
			simulationSteps |= SimulationSteps.CleanUpAfter & cleanUp
		elif (not (analyze or elaborate or optimize or simulate or resimulate or showWaveform or showCoverage or guiMode) and recompile):
			simulationSteps |= SimulationSteps.Analyze | SimulationSteps.Elaborate #| SimulationSteps.Optimize
			simulationSteps |= SimulationSteps.Recompile
			simulationSteps |= SimulationSteps.ShowReport &   showReport
			simulationSteps |= SimulationSteps.CleanUpAfter & cleanUp
		elif (not (analyze or elaborate or optimize or recompile or simulate or showWaveform or showCoverage) and resimulate):
			simulationSteps |= SimulationSteps.Simulate
			simulationSteps |= SimulationSteps.ShowWaveform & guiMode
			simulationSteps |= SimulationSteps.ShowCoverage & guiMode
			simulationSteps |= SimulationSteps.ShowReport &   showReport
			simulationSteps |= SimulationSteps.CleanUpAfter & cleanUp
		elif (recompile or resimulate):
			raise SimulatorException("Combination of command line options is not allowed.")
		else:
			# simulationSteps |=  SimulationSteps.CleanUpBefore &  True   #cleanup
			simulationSteps |=  SimulationSteps.Prepare &        True   #prepare
			simulationSteps |=  SimulationSteps.Analyze &        analyze
			simulationSteps |=  SimulationSteps.Elaborate &      elaborate
			# simulationSteps |=  SimulationSteps.Optimize &       optimize
			simulationSteps |=  SimulationSteps.Simulate &       simulate
			simulationSteps |=  SimulationSteps.ShowWaveform &  (showWaveform or guiMode)
			simulationSteps |=  SimulationSteps.ShowCoverage &  (showCoverage or guiMode)
			simulationSteps |=  SimulationSteps.ShowReport &     showReport
		return simulationSteps

	@staticmethod
	def _ExtractCompileSteps(guiMode, synthesize, showReport, cleanUp):
		compileSteps = CompileSteps.no_flags
		if (not (synthesize)):
			compileSteps |= CompileSteps.Prepare | SimulationSteps.CleanUpBefore
			compileSteps |= CompileSteps.Synthesize
			compileSteps |= CompileSteps.ShowReport   & showReport
			compileSteps |= CompileSteps.CleanUpAfter & cleanUp
		else:
			# simulationSteps |=  SimulationSteps.CleanUpBefore &  True   #cleanup
			compileSteps |=  CompileSteps.Prepare &     True   #prepare
			compileSteps |=  CompileSteps.Synthesize &  synthesize
			compileSteps |=  CompileSteps.ShowReport &  showReport
			compileSteps |=  CompileSteps.ShowGUI &     guiMode
		return compileSteps

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "list-testbench" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Simulation commands") # mccabe:disable=MC0001
	@CommandAttribute("list-testbench", help="List all testbenches.", description=dedent("""\
		List all testbenches.
		"""))
	@pyIPCMIEntityAttribute()
	@ArgumentAttribute("--kind", metavar="Kind", dest="TestbenchKind", help="Testbench kind: VHDL | COCOTB")
	def HandleListTestbenches(self, args):
		self.PrintHeadline()
		self.__PrepareForSimulation()

		defaultLibrary = self.LibraryName

		if (args.SolutionID is not None):
			solutionName = args.SolutionID
			print("Solution name: {0}".format(solutionName))
			if self.Config.has_option("SOLUTION.Solutions", solutionName):
				sectionName = "SOLUTION.{0}".format(solutionName)
				print("Found registered solution:")
				print("  Name: {0}".format(self.Config[sectionName]['Name']))
				print("  Path: {0}".format(self.Config[sectionName]['Path']))

				solutionRootPath = self.Directories.Root / self.Config[sectionName]['Path']
				solutionConfigFile = solutionRootPath / ".pyIPCMI" / "solution.config.ini"
				solutionDefaultsFile = solutionRootPath / ".pyIPCMI" / "solution.defaults.ini"
				print("  sln files: {0!s}  {1!s}".format(solutionConfigFile, solutionDefaultsFile))

				self.LogVerbose("Reading solution file...")
				self.LogDebug("  {0!s}".format(solutionConfigFile))
				self.LogDebug("  {0!s}".format(solutionDefaultsFile))
				if not solutionConfigFile.exists():
					raise NotConfiguredException("Solution's {0} configuration file '{1!s}' does not exist.".format(solutionName, solutionConfigFile)) \
						from FileNotFoundError(str(solutionConfigFile))
				if not solutionDefaultsFile.exists():
					raise NotConfiguredException("Solution's {0} defaults file '{1!s}' does not exist.".format(solutionName, solutionDefaultsFile)) \
						from FileNotFoundError(str(solutionDefaultsFile))
				self.Config.read(str(solutionConfigFile))
				self.Config.read(str(solutionDefaultsFile))

				section =         self.Config['PROJECT.Projects']
				defaultLibrary =  section['DefaultLibrary']
				print("Solution:")
				print("  Name:            {0}".format(section['Name']))
				print("  Default library: {0}".format(defaultLibrary))
				print("  Projects:")
				for item in section:
					if (section[item] in ["pyIPCMIProject", "ISEProject", "VivadoProject", "QuartusProject"]):
						sectionName2 = "PROJECT.{0}".format(item)
						print("    {0}".format(self.Config[sectionName2]['Name']))

				print("  Namespace roots:")
				for item in section:
					if (section[item] == "Library"):
						libraryPrefix = item
						print("    {0: <16}  {1}".format(self.Config[libraryPrefix]['Name'], libraryPrefix))

						self.Root.AddLibrary(libraryPrefix, libraryPrefix)


		if (args.TestbenchKind is None):
			tbFilter =  TestbenchKind.All
		else:
			tbFilter =  TestbenchKind.Unknown
			for kind in args.TestbenchKind.lower().split(","):
				if   (kind == "vhdl"):    tbFilter |= TestbenchKind.VHDLTestbench
				elif (kind == "cocotb"):  tbFilter |= TestbenchKind.CocoTestbench
				else:                      raise CommonException("Argument --kind has an unknown value '{0}'.".format(kind))

		fqnList = self._ExtractFQNs(args.FQN, defaultLibrary)
		for fqn in fqnList:
			self.LogNormal("")
			entity = fqn.Entity
			if (isinstance(entity, WildCard)):
				for testbench in entity.GetTestbenches(tbFilter):
					print(str(testbench))
			else:
				testbench = entity.GetTestbenches(tbFilter)
				print(str(testbench))

		Exit.exit()


	# ----------------------------------------------------------------------------
	# create the sub-parser for the "asim" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Simulation commands")
	@CommandAttribute("asim", help="Simulate a pyIPCMI Entity with Aldec Active-HDL.", description=dedent("""\
		Simulate a pyIPCMI Entity with Aldec Active-HDL.
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@VHDLVersionAttribute()
	@SimulationStepsAttributeGroup()
	def HandleActiveHDLSimulation(self, args):
		self.PrintHeadline()
		self.__PrepareForSimulation()
		self._CheckActiveHDL()

		fqnList =         self._ExtractFQNs(args.FQN)
		board =           self._ExtractBoard(args.BoardName, args.DeviceName)
		vhdlVersion =     self._ExtractVHDLVersion(args.VHDLVersion)
		simulationSteps = self._ExtractSimulationSteps(args.GUIMode, args.Analyze, args.Elaborate, False, args.Recompile, args.Simulate, args.ShowWave, args.ShowCoverage, args.Resimulate, args.ShowReport, False)

		# create a GHDLSimulator instance and prepare it
		simulator = ActiveHDLSimulator(self, self.DryRun, simulationSteps)
		allPassed = simulator.RunAll(fqnList, board=board, vhdlVersion=vhdlVersion)

		Exit.exit(1 if ((SimulationSteps.Simulate in simulationSteps) and not allPassed) else 0)


# ----------------------------------------------------------------------------
	# create the sub-parser for the "ghdl" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Simulation commands")
	@CommandAttribute("ghdl", help="Simulate a pyIPCMI Entity with GHDL.", description=dedent("""\
		Simulate a pyIPCMI Entity with GHDL.
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@VHDLVersionAttribute()
	@SimulationStepsAttributeGroup()
	@SwitchArgumentAttribute("--with-coverage", dest="WithCoverage", help="Compile with coverage information.")
	@ArgumentAttribute("--reproducer", metavar="Name", dest="CreateReproducer", help="Create a bug reproducer")
	def HandleGHDLSimulation(self, args):
		self.PrintHeadline()
		self.__PrepareForSimulation()
		self._CheckGHDL()

		config = GHDLConfiguration(self)
		if (not config.IsSupportedPlatform()):    raise PlatformNotSupportedException(self.Platform)
		if (not config.IsConfigured()):           raise NotConfiguredException("GHDL is not configured on this system.")

		fqnList =         self._ExtractFQNs(args.FQN)
		board =           self._ExtractBoard(args.BoardName, args.DeviceName)
		vhdlVersion =     self._ExtractVHDLVersion(args.VHDLVersion)
		simulationSteps = self._ExtractSimulationSteps(args.GUIMode, args.Analyze, args.Elaborate, False, args.Recompile, args.Simulate, args.ShowWave, args.ShowCoverage, args.Resimulate, args.ShowReport, False)

		simulator = GHDLSimulator(self, self.DryRun, simulationSteps)
		allPassed = simulator.RunAll(fqnList, board=board, vhdlVersion=vhdlVersion, withCoverage=args.WithCoverage)

		Exit.exit(1 if ((SimulationSteps.Simulate in simulationSteps) and not allPassed) else 0)


	# ----------------------------------------------------------------------------
	# create the sub-parser for the "isim" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Simulation commands")
	@CommandAttribute("isim", help="Simulate a pyIPCMI Entity with Xilinx ISE Simulator (iSim).", description=dedent("""\
		Simulate a pyIPCMI Entity with Xilinx ISE Simulator (iSim).
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@SimulationStepsAttributeGroup()
	def HandleISESimulation(self, args):
		self.PrintHeadline()
		self.__PrepareForSimulation()
		self._CheckISE()

		fqnList =         self._ExtractFQNs(args.FQN)
		board =           self._ExtractBoard(args.BoardName, args.DeviceName)
		simulationSteps = self._ExtractSimulationSteps(args.GUIMode, args.Analyze, args.Elaborate, False, args.Recompile, args.Simulate, args.ShowWave, args.ShowCoverage, args.Resimulate, args.ShowReport, False)

		simulator = ISESimulator(self, self.DryRun, simulationSteps)
		allPassed = simulator.RunAll(fqnList, board=board, vhdlVersion=VHDLVersion.VHDL93)

		Exit.exit(1 if ((SimulationSteps.Simulate in simulationSteps) and not allPassed) else 0)

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "msim" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Simulation commands")
	@CommandAttribute("msim", help="Simulate a pyIPCMI Entity with Mentor ModelSim (msim).",
					  description=dedent("""\
		Simulate a pyIPCMI Entity with Mentor ModelSim (msim).
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@VHDLVersionAttribute()
	@SimulationStepsAttributeGroup()
	@SwitchArgumentAttribute("--with-coverage", dest="WithCoverage", help="Compile with coverage information.")
	def HandleModelSimSimulation(self, args):
		self.PrintHeadline()
		self.__PrepareForSimulation()
		self._CheckModelSim()

		fqnList = self._ExtractFQNs(args.FQN)
		board = self._ExtractBoard(args.BoardName, args.DeviceName)
		vhdlVersion = self._ExtractVHDLVersion(args.VHDLVersion)
		simulationSteps = self._ExtractSimulationSteps(args.GUIMode, args.Analyze, args.Elaborate, False,
													   args.Recompile, args.Simulate, args.ShowWave,
													   args.ShowCoverage, args.Resimulate, args.ShowReport, False)

		simulator = QuestaSimulator(self, self.DryRun, simulationSteps)
		allPassed = simulator.RunAll(fqnList, board=board, vhdlVersion=vhdlVersion, withCoverage=args.WithCoverage)

		Exit.exit(1 if ((SimulationSteps.Simulate in simulationSteps) and not allPassed) else 0)

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "vsim" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Simulation commands")
	@CommandAttribute("vsim", help="Simulate a pyIPCMI Entity with any Mentor QuestaSim or ModelSim (vsim).",
					  description=dedent("""\
		Simulate a pyIPCMI Entity with any Mentor QuestaSim or ModelSim (vsim).
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@VHDLVersionAttribute()
	@SimulationStepsAttributeGroup()
	@SwitchArgumentAttribute("--with-coverage", dest="WithCoverage", help="Compile with coverage information.")
	def HandleAnyMentorSimulation(self, args):
		self.PrintHeadline()
		self.__PrepareForSimulation()
		self._CheckModelSim()

		fqnList = self._ExtractFQNs(args.FQN)
		board = self._ExtractBoard(args.BoardName, args.DeviceName)
		vhdlVersion = self._ExtractVHDLVersion(args.VHDLVersion)
		simulationSteps = self._ExtractSimulationSteps(args.GUIMode, args.Analyze, args.Elaborate, False,
													   args.Recompile, args.Simulate, args.ShowWave,
													   args.ShowCoverage, args.Resimulate, args.ShowReport,
													   False)

		simulator = QuestaSimulator(self, self.DryRun, simulationSteps)
		allPassed = simulator.RunAll(fqnList, board=board, vhdlVersion=vhdlVersion,
									 withCoverage=args.WithCoverage)

		Exit.exit(1 if ((SimulationSteps.Simulate in simulationSteps) and not allPassed) else 0)


	# ----------------------------------------------------------------------------
	# create the sub-parser for the "rsim" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Simulation commands")
	@CommandAttribute("rpro", help="Simulate a pyIPCMI Entity with Aldec Riviera-PRO (rpro)")
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@VHDLVersionAttribute()
	@SimulationStepsAttributeGroup()
	def HandleRivieraPROSimulation(self, args):
		self.PrintHeadline()
		self.__PrepareForSimulation()
		self._CheckRivieraPRO()

		fqnList =         self._ExtractFQNs(args.FQN)
		board =           self._ExtractBoard(args.BoardName, args.DeviceName)
		simulationSteps = self._ExtractSimulationSteps(args.GUIMode, args.Analyze, args.Elaborate, False, args.Recompile, args.Simulate, args.ShowWave, args.ShowCoverage, args.Resimulate, args.ShowReport, False)
		vhdlVersion =     self._ExtractVHDLVersion(args.VHDLVersion)

		simulator = RivieraPROSimulator(self, self.DryRun, simulationSteps)
		allPassed = simulator.RunAll(fqnList, board=board, vhdlVersion=vhdlVersion)

		Exit.exit(1 if ((SimulationSteps.Simulate in simulationSteps) and not allPassed) else 0)


	# ----------------------------------------------------------------------------
	# create the sub-parser for the "qsim" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Simulation commands")
	@CommandAttribute("qsim", help="Simulate a pyIPCMI Entity with Mentor QuestaSim (qsim).", description=dedent("""\
		Simulate a pyIPCMI Entity with Mentor QuestaSim (qsim).
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@VHDLVersionAttribute()
	@SimulationStepsAttributeGroup()
	@SwitchArgumentAttribute("--with-coverage", dest="WithCoverage", help="Compile with coverage information.")
	def HandleQuestaSimSimulation(self, args):
		self.PrintHeadline()
		self.__PrepareForSimulation()
		self._CheckModelSim()

		fqnList =         self._ExtractFQNs(args.FQN)
		board =           self._ExtractBoard(args.BoardName, args.DeviceName)
		vhdlVersion =     self._ExtractVHDLVersion(args.VHDLVersion)
		simulationSteps = self._ExtractSimulationSteps(args.GUIMode, args.Analyze, args.Elaborate, False, args.Recompile, args.Simulate, args.ShowWave, args.ShowCoverage, args.Resimulate, args.ShowReport, False)

		simulator = QuestaSimulator(self, self.DryRun, simulationSteps)
		allPassed = simulator.RunAll(fqnList, board=board, vhdlVersion=vhdlVersion, withCoverage=args.WithCoverage)

		Exit.exit(1 if ((SimulationSteps.Simulate in simulationSteps) and not allPassed) else 0)


	# ----------------------------------------------------------------------------
	# create the sub-parser for the "xsim" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Simulation commands")
	@CommandAttribute("xsim", help="Simulate a pyIPCMI Entity with Xilinx Vivado Simulator (xSim).", description=dedent("""\
		Simulate a pyIPCMI Entity with Xilinx Vivado Simulator (xSim).
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@VHDLVersionAttribute()
	@SimulationStepsAttributeGroup()
	def HandleVivadoSimulation(self, args):
		self.PrintHeadline()
		self.__PrepareForSimulation()
		self._CheckVivado()

		fqnList =         self._ExtractFQNs(args.FQN)
		board =           self._ExtractBoard(args.BoardName, args.DeviceName)
		# FIXME: VHDL-2008 is broken in Vivado 2016.1 -> use VHDL-93 by default
		vhdlVersion =     self._ExtractVHDLVersion(args.VHDLVersion, defaultVersion=VHDLVersion.VHDL93)
		simulationSteps = self._ExtractSimulationSteps(args.GUIMode, args.Analyze, args.Elaborate, False, args.Recompile, args.Simulate, args.ShowWave, args.ShowCoverage, args.Resimulate, args.ShowReport, False)

		simulator = VivadoSimulator(self, self.DryRun, simulationSteps)
		allPassed = simulator.RunAll(fqnList, board=board, vhdlVersion=vhdlVersion)

		Exit.exit(1 if ((SimulationSteps.Simulate in simulationSteps) and not allPassed) else 0)


	# ----------------------------------------------------------------------------
	# create the sub-parser for the "cocotb" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Simulation commands")
	@CommandAttribute("cocotb", help="Simulate a pyIPCMI Entity with Cocotb and QuestaSim.", description=dedent("""\
		Simulate a pyIPCMI Entity with Cocotb and QuestaSim.
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@SimulationStepsAttributeGroup()
	def HandleCocotbSimulation(self, args):
		self.PrintHeadline()
		self.__PrepareForSimulation()
		self._CheckModelSim()

		# check if QuestaSim is configured
		if (len(self.Config.options("INSTALL.Mentor.QuestaSim")) == 0):
			if (len(self.Config.options("INSTALL.Altera.ModelSim")) == 0):
				raise NotConfiguredException("Neither Mentor QuestaSim, Mentor ModelSim nor ModelSim Altera Edition are configured on this system.")

		fqnList =         self._ExtractFQNs(args.FQN)
		board =           self._ExtractBoard(args.BoardName, args.DeviceName)
		simulationSteps = self._ExtractSimulationSteps(args.GUIMode, args.Analyze, args.Elaborate, False, args.Recompile, args.Simulate, args.ShowWave, args.ShowCoverage, args.Resimulate, args.ShowReport, False)

		# create a CocotbSimulator instance and prepare it
		simulator = CocotbSimulator(self, self.DryRun, simulationSteps)
		allPassed = simulator.RunAll(fqnList, board=board, vhdlVersion=VHDLVersion.VHDL2008)

		Exit.exit(1 if ((SimulationSteps.Simulate in simulationSteps) and not allPassed) else 0)


	# ============================================================================
	# Synthesis	commands
	# ============================================================================
	# create the sub-parser for the "list-netlist" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Simulation commands")
	@CommandAttribute("list-netlist", help="List all netlists.", description=dedent("""\
		List all netlists.
		"""))
	@pyIPCMIEntityAttribute()
	@ArgumentAttribute("--kind", metavar="Kind", dest="NetlistKind", help="Netlist kind: Lattice | Quartus | XST | CoreGen")
	def HandleListNetlist(self, args):
		self.PrintHeadline()
		self.__PrepareForSynthesis()

		if (args.NetlistKind is None):
			nlFilter = NetlistKind.All
		else:
			nlFilter = NetlistKind.Unknown
			for kind in args.TestbenchKind.lower().split(","):
				if   (kind == "lattice"):  nlFilter |= NetlistKind.LatticeNetlist
				elif (kind == "quartus"):  nlFilter |= NetlistKind.QuartusNetlist
				elif (kind == "xst"):      nlFilter |= NetlistKind.XstNetlist
				elif (kind == "coregen"):  nlFilter |= NetlistKind.CoreGeneratorNetlist
				elif (kind == "vivado"):   nlFilter |= NetlistKind.VivadoNetlist
				else:                      raise CommonException("Argument --kind has an unknown value '{0}'.".format(kind))

		fqnList = self._ExtractFQNs(args.FQN)
		for fqn in fqnList:
			entity = fqn.Entity
			if (isinstance(entity, WildCard)):
				for testbench in entity.GetNetlists(nlFilter):
					print(str(testbench))
			else:
				testbench = entity.GetNetlists(nlFilter)
				print(str(testbench))

		Exit.exit()

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "ise" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Synthesis commands")
	@CommandAttribute("ise", help="Generate any IP core for the Xilinx ISE tool chain.", description=dedent("""\
		Generate any IP core for the Xilinx ISE tool chain.
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@CompileStepsAttributeGroup()
	def HandleISECompilation(self, args):
		self.PrintHeadline()
		self.__PrepareForSynthesis()
		self._CheckISE()

		fqnList =  self._ExtractFQNs(args.FQN, defaultType=EntityTypes.NetList)
		board =    self._ExtractBoard(args.BoardName, args.DeviceName, force=True)

		compiler = ISECompiler(self, self.DryRun, args.NoCleanUp)
		compiler.RunAll(fqnList, board)

		Exit.exit()

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "coregen" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Synthesis commands")
	@CommandAttribute("coregen", help="Generate an IP core with Xilinx ISE Core Generator.", description=dedent("""\
		Generate an IP core with Xilinx ISE Core Generator.
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@CompileStepsAttributeGroup()
	def HandleCoreGeneratorCompilation(self, args):
		self.PrintHeadline()
		self.__PrepareForSynthesis()
		self._CheckISE()

		fqnList =  self._ExtractFQNs(args.FQN, defaultType=EntityTypes.NetList)
		board =    self._ExtractBoard(args.BoardName, args.DeviceName, force=True)

		compiler = XCOCompiler(self, self.DryRun, args.NoCleanUp)
		compiler.RunAll(fqnList, board)

		Exit.exit()

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "xst" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Synthesis commands")
	@CommandAttribute("xst", help="Compile a pyIPCMI IP core with Xilinx ISE XST to a netlist.", description=dedent("""\
		Compile a pyIPCMI IP core with Xilinx ISE XST to a netlist.
		:ref:`IP:pyIPCMI.Mem`
		foooo baaarr.
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@CompileStepsAttributeGroup()
	def HandleXstCompilation(self, args):
		self.PrintHeadline()
		self.__PrepareForSynthesis()
		self._CheckISE()

		fqnList =  self._ExtractFQNs(args.FQN, defaultType=EntityTypes.NetList)
		board =    self._ExtractBoard(args.BoardName, args.DeviceName, force=True)

		compiler = XSTCompiler(self, self.DryRun, args.NoCleanUp)
		compiler.RunAll(fqnList, board)

		Exit.exit()

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "xci" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Synthesis commands")
	@CommandAttribute("xci", help="Generate an IP core from Xilinx Vivado IP Catalog.", description=dedent("""\
		Generate an IP core from Xilinx Vivado IP Catalog.
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@CompileStepsAttributeGroup()
	def HandleIpCatalogCompilation(self, args):
		self.PrintHeadline()
		self.__PrepareForSynthesis()
		self._CheckVivado()

		fqnList = self._ExtractFQNs(args.FQN, defaultType=EntityTypes.NetList)
		board = self._ExtractBoard(args.BoardName, args.DeviceName, force=True)

		compiler = XCICompiler(self, self.DryRun, args.NoCleanUp)
		compiler.RunAll(fqnList, board)

		Exit.exit()

	# ----------------------------------------------------------------------------
	# create the sub-parser for the "vivado" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Synthesis commands")
	@CommandAttribute("vivado", help="Compile a pyIPCMI IP core with Xilinx Vivado Synth to a design checkpoint.", description=dedent("""\
		Compile a pyIPCMI IP core with Xilinx Vivado Synth to a design checkpoint.
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@CompileStepsAttributeGroup()
	def HandleVivadoCompilation(self, args):
		self.PrintHeadline()
		self.__PrepareForSynthesis()
		self._CheckVivado()

		fqnList =  self._ExtractFQNs(args.FQN, defaultType=EntityTypes.NetList)
		board =    self._ExtractBoard(args.BoardName, args.DeviceName, force=True)

		compiler = VivadoCompiler(self, self.DryRun, args.NoCleanUp)
		compiler.RunAll(fqnList, board)

		Exit.exit()


	# ----------------------------------------------------------------------------
	# create the sub-parser for the "quartus" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Synthesis commands")
	@CommandAttribute("quartus", help="Compile a pyIPCMI IP core with Altera Quartus II Map to a netlist.", description=dedent("""\
		Compile a pyIPCMI IP core with Altera Quartus II Map to a netlist.
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@CompileStepsAttributeGroup()
	def HandleQuartusCompilation(self, args):
		self.PrintHeadline()
		self.__PrepareForSynthesis()
		self._CheckQuartus()

		fqnList =  self._ExtractFQNs(args.FQN, defaultType=EntityTypes.NetList)
		board =    self._ExtractBoard(args.BoardName, args.DeviceName, force=True)

		compiler = MapCompiler(self, self.DryRun, args.NoCleanUp)
		compiler.RunAll(fqnList, board)

		Exit.exit()


	# ----------------------------------------------------------------------------
	# create the sub-parser for the "lattice" command
	# ----------------------------------------------------------------------------
	@CommandGroupAttribute("Synthesis commands")
	@CommandAttribute("lse", help="Compile a pyIPCMI IP core with Lattice Diamond LSE to a netlist.", description=dedent("""\
		Compile a pyIPCMI IP core with Lattice Diamond LSE to a netlist.
		"""))
	@pyIPCMIEntityAttribute()
	@BoardDeviceAttributeGroup()
	@CompileStepsAttributeGroup()
	def HandleLSECompilation(self, args):
		self.PrintHeadline()
		self.__PrepareForSynthesis()
		self._CheckDiamond()

		fqnList =  self._ExtractFQNs(args.FQN, defaultType=EntityTypes.NetList)
		board =    self._ExtractBoard(args.BoardName, args.DeviceName, force=True)

		compiler = LSECompiler(self, self.DryRun, args.NoCleanUp)
		compiler.RunAll(fqnList, board)

		Exit.exit()
