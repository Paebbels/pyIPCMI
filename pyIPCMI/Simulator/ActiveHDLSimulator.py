# EMACS settings: -*-	tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:          Patrick Lehmann
#                   Martin Zabel
#
# Python Module:    Aldec Active-HDL simulator.
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
from pathlib                      import Path

from pyIPCMI.Base.Executable              import DryRunException
from pyIPCMI.Base.Project                 import FileTypes, ToolChain, Tool
from pyIPCMI.ToolChain.Aldec.ActiveHDL    import ActiveHDL, ActiveHDLException
from pyIPCMI.Simulator                    import VHDL_TESTBENCH_LIBRARY_NAME, SimulatorException, SkipableSimulatorException, SimulationSteps, Simulator as BaseSimulator


__api__ = [
	'Simulator'
]
__all__ = __api__


class Simulator(BaseSimulator):
	TOOL_CHAIN =      ToolChain.Aldec_ActiveHDL
	TOOL =            Tool.Aldec_aSim

	def __init__(self, host, dryRun, simulationSteps):
		super().__init__(host, dryRun, simulationSteps)

		activeHDLFilesDirectoryName =   host.Config['CONFIG.DirectoryNames']['ActiveHDLFiles']
		self.Directories.Working =      host.Directories.Temp / activeHDLFilesDirectoryName
		self.Directories.PreCompiled =  host.Directories.PreCompiled / activeHDLFilesDirectoryName

		self._PrepareSimulationEnvironment()
		self._PrepareSimulator()

	def _PrepareSimulator(self):
		"""Create the Active-HDL executable factory."""
		self.LogVerbose("Preparing Active-HDL simulator.")
		# for sectionName in ['INSTALL.Aldec.ActiveHDL', 'INSTALL.Lattice.ActiveHDL']:
		# 	if (len(self.Host.Config.options(sectionName)) != 0):
		# 		break
		# else:
		# XXX: check SectionName if ActiveHDL is configured
		# 	raise NotConfiguredException(
		# 		"Neither Aldec's Active-HDL nor Active-HDL Lattice Edition are configured on this system.")

		binaryPath =      Path(self.Host.Config['INSTALL.ActiveHDL']['BinaryDirectory'])
		version =         self.Host.Config['INSTALL.ActiveHDL']['Version']
		self._toolChain = ActiveHDL(self.Host.Platform, self.DryRun, binaryPath, version, logger=self.Logger)

	def _RunAnalysis(self, _):
		# create a ActiveHDLVHDLCompiler instance
		alib = self._toolChain.GetVHDLLibraryTool()

		for lib in self._pyIPCMIProject.VHDLLibraries:
			alib.Parameters[alib.SwitchLibraryName] = lib.Name
			try:
				alib.CreateLibrary()
			except DryRunException:
				pass
			except ActiveHDLException as ex:
				raise SimulatorException("Error creating VHDL library '{0}'.".format(lib.Name)) from ex
			if alib.HasErrors:
				raise SimulatorException("Error creating VHDL library '{0}'.".format(lib.Name))

		# create a ActiveHDLVHDLCompiler instance
		acom = self._toolChain.GetVHDLCompiler()
		acom.Parameters[acom.SwitchVHDLVersion] = repr(self._vhdlVersion)

		# run acom compile for each VHDL file
		for file in self._pyIPCMIProject.Files(fileType=FileTypes.VHDLSourceFile):
			if (not file.Path.exists()):                  raise SimulatorException("Cannot analyse '{0!s}'.".format(file.Path)) from FileNotFoundError(str(file.Path))
			acom.Parameters[acom.SwitchVHDLLibrary] =  file.LibraryName
			acom.Parameters[acom.ArgSourceFile] =      file.Path
			# set a per file log-file with '-l', 'vcom.log',
			try:
				acom.Compile()
			except DryRunException:
				pass
			except ActiveHDLException as ex:
				raise SimulatorException("Error while compiling '{0!s}'.".format(file.Path)) from ex
			if acom.HasErrors:
				raise SkipableSimulatorException("Error while compiling '{0!s}'.".format(file.Path))

	def _RunSimulation(self, testbench):
		if (SimulationSteps.ShowWaveform in self._simulationSteps):
			return self._RunSimulationWithGUI(testbench)

		# tclBatchFilePath =    self.Host.Directories.Root / self.Host.Config[testbench.ConfigSectionName]['aSimBatchScript']

		# create a ActiveHDLSimulator instance
		asim = self._toolChain.GetSimulator()
		asim.Parameters[asim.SwitchBatchCommand] = "asim -lib {0} {1}; run -all; bye".format(VHDL_TESTBENCH_LIBRARY_NAME, testbench.ModuleName)

		# asim.Optimization =      True
		# asim.TimeResolution =    "1fs"
		# asim.ComanndLineMode =  True
		# asim.BatchCommand =      "do {0}".format(str(tclBatchFilePath))
		# asim.TopLevel =          "{0}.{1}".format(VHDLTestbenchLibraryName, testbenchName)
		try:
			testbench.Result = asim.Simulate()
		except DryRunException:
			pass
		except ActiveHDLException as ex:
			raise SimulatorException("Error while simulating '{0}.{1}'.".format(VHDL_TESTBENCH_LIBRARY_NAME, testbench.ModuleName)) from ex
		if asim.HasErrors:
			raise SkipableSimulatorException("Error while simulating '{0}.{1}'.".format(VHDL_TESTBENCH_LIBRARY_NAME, testbench.ModuleName))

	def _RunSimulationWithGUI(self, testbench):
		raise SimulatorException("GUI mode is not supported for Active-HDL.")

		# tclGUIFilePath =      self.Host.Directories.Root / self.Host.Config[testbench.ConfigSectionName]['aSimGUIScript']
		# tclWaveFilePath =      self.Host.Directories.Root / self.Host.Config[testbench.ConfigSectionName]['aSimWaveScript']
		#
		# # create a ActiveHDLSimulator instance
		# aSim = self._toolChain.GetSimulator()
		# aSim.Optimization =    True
		# aSim.TimeResolution =  "1fs"
		# aSim.Title =          testbench.ModuleName
		#
		# if (tclWaveFilePath.exists()):
		# 	self.LogDebug("Found waveform script: '{0!s}'".format(tclWaveFilePath))
		# 	aSim.BatchCommand =  "do {0!s}; do {1!s}".format(tclWaveFilePath, tclGUIFilePath)
		# else:
		# 	self.LogDebug("Didn't find waveform script: '{0!s}'. Loading default commands.".format(tclWaveFilePath))
		# 	aSim.BatchCommand =  "add wave *; do {0!s}".format(tclGUIFilePath)
		#
		# aSim.TopLevel =    "{0}.{1}".format(VHDL_TESTBENCH_LIBRARY_NAME, testbench.ModuleName)
		# aSim.Simulate()

