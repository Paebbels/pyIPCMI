# EMACS settings: -*-	tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:          Patrick Lehmann
#                   Martin Zabel
#
# Python Module:    Xilinx Vivado simulator.
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

from pyIPCMI.Base.Executable            import DryRunException
from pyIPCMI.Base.Logging               import Severity
from pyIPCMI.Base.Project               import ToolChain, Tool
from pyIPCMI.ToolChain.Xilinx           import XilinxProjectExportMixIn
from pyIPCMI.ToolChain.Xilinx.Vivado    import Vivado, VivadoException
from pyIPCMI.Simulator                  import VHDL_TESTBENCH_LIBRARY_NAME, SimulatorException, SkipableSimulatorException, SimulationSteps, Simulator as BaseSimulator


__api__ = [
	'Simulator'
]
__all__ = __api__


class Simulator(BaseSimulator, XilinxProjectExportMixIn):
	TOOL_CHAIN =      ToolChain.Xilinx_Vivado
	TOOL =            Tool.Xilinx_xSim

	def __init__(self, host, dryRun, simulationSteps):
		super().__init__(host, dryRun, simulationSteps)
		XilinxProjectExportMixIn.__init__(self)

		vivadoFilesDirectoryName =      host.Config['CONFIG.DirectoryNames']['VivadoSimulatorFiles']
		self.Directories.Working =      host.Directories.Temp / vivadoFilesDirectoryName
		self.Directories.PreCompiled =  host.Directories.PreCompiled / vivadoFilesDirectoryName

		self._PrepareSimulationEnvironment()
		self._PrepareSimulator()

	def _PrepareSimulator(self):
		# create the Vivado executable factory
		self.LogVerbose("Preparing Vivado simulator.")
		vivadoSection =         self.Host.Config['INSTALL.Xilinx.Vivado']
		version =               vivadoSection['Version']
		installationDirectory = Path(vivadoSection['InstallationDirectory'])
		binaryPath =            Path(vivadoSection['BinaryDirectory'])
		self._toolChain =       Vivado(self.Host.Platform, self.DryRun, binaryPath, version, logger=self.Logger)
		self._toolChain.PreparseEnvironment(installationDirectory)

	def _RunElaboration(self, testbench):
		xelabLogFilePath =  self.Directories.Working / (testbench.ModuleName + ".xelab.log")
		prjFilePath =       self.Directories.Working / (testbench.ModuleName + ".prj")
		self._WriteXilinxProjectFile(prjFilePath, "xSim", self._vhdlVersion)

		# create a VivadoLinker instance
		xelab = self._toolChain.GetElaborator()
		xelab.Parameters[xelab.SwitchTimeResolution] =  "1fs"	# set minimum time precision to 1 fs
		xelab.Parameters[xelab.SwitchMultiThreading] =  "off" if self.Logger.LogLevel is Severity.Debug else "auto"		# disable multithreading support in debug mode
		xelab.Parameters[xelab.FlagRangeCheck] =        True

		xelab.Parameters[xelab.SwitchOptimization] =    "0" if self.Logger.LogLevel is Severity.Debug else "2"		# set to "0" to disable optimization
		xelab.Parameters[xelab.SwitchDebug] =           "typical"
		xelab.Parameters[xelab.SwitchSnapshot] =        testbench.ModuleName

		xelab.Parameters[xelab.SwitchVerbose] =         "1" if self.Logger.LogLevel is Severity.Debug else "0"		# set to "1" for detailed messages
		xelab.Parameters[xelab.SwitchProjectFile] =     str(prjFilePath)
		xelab.Parameters[xelab.SwitchLogFile] =         str(xelabLogFilePath)
		xelab.Parameters[xelab.ArgTopLevel] =           "{0}.{1}".format(VHDL_TESTBENCH_LIBRARY_NAME, testbench.ModuleName)

		try:
			xelab.Link()
		except DryRunException:
			pass
		except VivadoException as ex:
			raise SimulatorException("Error while analysing '{0!s}'.".format(prjFilePath)) from ex
		if xelab.HasErrors:
			raise SkipableSimulatorException("Error while analysing '{0!s}'.".format(prjFilePath))

	def _RunSimulation(self, testbench):
		xSimLogFilePath =    self.Directories.Working / (testbench.ModuleName + ".xSim.log")
		tclBatchFilePath =  self.Host.Directories.Root / self.Host.Config[testbench.ConfigSectionName]['xSimBatchScript']
		tclGUIFilePath =    self.Host.Directories.Root / self.Host.Config[testbench.ConfigSectionName]['xSimGUIScript']
		wcfgFilePath =      self.Host.Directories.Root / self.Host.Config[testbench.ConfigSectionName]['xSimWaveformConfigFile']

		# create a VivadoSimulator instance
		xSim = self._toolChain.GetSimulator()
		xSim.Parameters[xSim.SwitchLogFile] =         str(xSimLogFilePath)

		if (SimulationSteps.ShowWaveform not in self._simulationSteps):
			xSim.Parameters[xSim.SwitchTclBatchFile] =  tclBatchFilePath.as_posix()
		else:
			xSim.Parameters[xSim.SwitchTclBatchFile] =  tclGUIFilePath.as_posix()
			xSim.Parameters[xSim.FlagGuiMode] =         True

			# if xSim save file exists, load it's settings
			if wcfgFilePath.exists():
				self.LogDebug("Found waveform config file: '{0!s}'".format(wcfgFilePath))
				xSim.Parameters[xSim.SwitchWaveformFile] = str(wcfgFilePath)
			else:
				self.LogDebug("Didn't find waveform config file: '{0!s}'".format(wcfgFilePath))

		xSim.Parameters[xSim.SwitchSnapshot] = testbench.ModuleName

		try:
			testbench.Result = xSim.Simulate()
		except DryRunException:
			pass
		except VivadoException as ex:
			raise SimulatorException("Error while simulating '{0}.{1}'.".format(VHDL_TESTBENCH_LIBRARY_NAME, testbench.ModuleName)) from ex
		if xSim.HasErrors:
			raise SkipableSimulatorException("Error while simulating '{0}.{1}'.".format(VHDL_TESTBENCH_LIBRARY_NAME, testbench.ModuleName))
