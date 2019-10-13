# EMACS settings: -*-  tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:              Patrick Lehmann
#                       Martin Zabel
#
# Python Main Module:   Entry point to IP Core Management Infrastructure (pyIPCMI).
#
# Description:
# ------------------------------------
#    This is a python main module (executable) which:
#    - runs automated testbenches,
#    - runs automated synthesis,
#    - runs automated regression tests,
#    - ...
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
# load dependencies
from configparser import Error as ConfigParser_Error, DuplicateOptionError
from sys          import argv as sys_argv
from platform     import system as platform_system

from pyExceptions import EnvironmentException, NotConfiguredException, PlatformNotSupportedException, ExceptionBase
from pyTokenizer  import ParserException

def printImportError(ex):
	platform = platform_system()
	print("[IMPORT ERROR]: One or more Python packages are not available in your environment.")
	print("Missing package: '{0}'\n".format(ex.name))
	if (platform == "Windows"):   print("Run: 'py.exe -3 -m pip install -r requirements.txt'\n")
	elif (platform == "Linux"):   print("Run: 'python3 -m pip install -r requirements.txt'\n")
	exit(1)


try:
	from lib.Functions            import Exit, Init
	from pyIPCMI                  import IPCoreManagementInfrastructure
	from pyIPCMI.Base.Exceptions  import CommonException
	from pyIPCMI.Compiler         import CompilerException
	from pyIPCMI.Simulator        import SimulatorException
	from pyIPCMI.ToolChain        import ConfigurationException, ToolChainException
except ImportError as ex:
	printImportError(ex)


# main program
def main(): # mccabe:disable=MC0001
	"""This is the entry point for pyIPCMI written as a function.

	1. It extracts common flags from the script's arguments list, before :py:class:`~argparse.ArgumentParser` is fully loaded.
	2. It initializes colorama for colored outputs
	3. It creates an instance of pyIPCMI and hands over to class based execution. All is wrapped in a big ``try..except`` block to catch every unhandled exception.
	4. Shutdown the script and return its exit code.
	"""

	dryRun =  "--dryrun"  in sys_argv
	debug =   "-d"        in sys_argv
	verbose = "-v"        in sys_argv
	quiet =   "-q"        in sys_argv

	# configure Exit class
	Exit.quiet = quiet

	try:
		Init.init()
		# handover to a class instance
		pyIPCMI = IPCoreManagementInfrastructure(debug, verbose, quiet, dryRun)
		pyIPCMI.Run()
		Exit.exit()

	except (CommonException, ConfigurationException, SimulatorException, CompilerException) as ex:
		print("{RED}ERROR:{NOCOLOR} {message}".format(message=ex.message, **Init.Foreground))
		cause = ex.__cause__
		if isinstance(cause, FileNotFoundError):
			print("{YELLOW}  FileNotFound:{NOCOLOR} '{cause}'".format(cause=str(cause), **Init.Foreground))
		elif isinstance(cause, NotADirectoryError):
			print("{YELLOW}  NotADirectory:{NOCOLOR} '{cause}'".format(cause=str(cause), **Init.Foreground))
		elif isinstance(cause, DuplicateOptionError):
			print("{YELLOW}  DuplicateOptionError:{NOCOLOR} '{cause}'".format(cause=str(cause), **Init.Foreground))
		elif isinstance(cause, ConfigParser_Error):
			print("{YELLOW}  configparser.Error:{NOCOLOR} '{cause}'".format(cause=str(cause), **Init.Foreground))
		elif isinstance(cause, ParserException):
			print("{YELLOW}  ParserException:{NOCOLOR} {cause}".format(cause=str(cause), **Init.Foreground))
			cause = cause.__cause__
			if (cause is not None):
				print("{YELLOW}    {name}:{NOCOLOR} {cause}".format(name=cause.__class__.__name__, cause= str(cause), **Init.Foreground))
		elif isinstance(cause, ToolChainException):
			print("{YELLOW}  {name}:{NOCOLOR} {cause}".format(name=cause.__class__.__name__, cause=str(cause), **Init.Foreground))
			cause = cause.__cause__
			if (cause is not None):
				if isinstance(cause, OSError):
					print("{YELLOW}    {name}:{NOCOLOR} {cause}".format(name=cause.__class__.__name__, cause=str(cause), **Init.Foreground))
			else:
				print("  Possible causes:")
				print("   - The compile order is broken.")
				print("   - A source file was not compiled and an old file got used.")

		if (not (verbose or debug)):
			print()
			print("{CYAN}  Use '-v' for verbose or '-d' for debug to print out extended messages.{NOCOLOR}".format(**Init.Foreground))
		Exit.exit(1)

	except EnvironmentException as ex:          Exit.printEnvironmentException(ex)
	except NotConfiguredException as ex:        Exit.printNotConfiguredException(ex)
	except PlatformNotSupportedException as ex: Exit.printPlatformNotSupportedException(ex)
	except ExceptionBase as ex:                 Exit.printExceptionBase(ex)
	except NotImplementedError as ex:           Exit.printNotImplementedError(ex)
	except ImportError as ex:                   printImportError(ex)
	except Exception as ex:                     Exit.printException(ex)

# entry point
if __name__ == "__main__":
	Exit.versionCheck((3,5,0))
	main()
