# EMACS settings: -*-	tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:          Patrick Lehmann
#                   Martin Zabel
#
# Python Module:    Lattice Diamond synthesizer (compiler).
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
from datetime                   import datetime
from pathlib                    import Path

from pyExceptions                       import PlatformNotSupportedException

from pyIPCMI.Base.Project               import ToolChain, Tool, VHDLVersion
from pyIPCMI.DataBase.Entity            import WildCard
from pyIPCMI.ToolChain.Lattice          import LatticeException
from pyIPCMI.ToolChain.Lattice.Diamond  import Diamond, SynthesisArgumentFile
from pyIPCMI.Compiler                   import CompilerException, SkipableCompilerException, CompileState, Compiler as BaseCompiler


__api__ = [
	'Compiler'
]
__all__ = __api__


class Compiler(BaseCompiler):
	TOOL_CHAIN =      ToolChain.Lattice_Diamond
	TOOL =            Tool.Lattice_LSE

	def __init__(self, host, dryRun, noCleanUp):
		super().__init__(host, dryRun, noCleanUp)

		self._vhdlVersion = VHDLVersion.VHDL2008

		configSection = host.Config['CONFIG.DirectoryNames']
		self.Directories.Working = host.Directories.Temp / configSection['LatticeSynthesisFiles']
		self.Directories.Netlist = host.Directories.Root / configSection['NetlistFiles']

		self._PrepareCompiler()

	def _PrepareCompiler(self):
		super()._PrepareCompiler()

		diamondSection = self.Host.Config['INSTALL.Lattice.Diamond']
		if (self.Host.Platform == "Linux"):     binaryPath = Path(diamondSection['BinaryDirectory2'])		# ispFPGA directory
		elif (self.Host.Platform == "Windows"): binaryPath = Path(diamondSection['BinaryDirectory2'])		# ispFPGA directory
		else:                                   raise PlatformNotSupportedException(self.Host.Platform)

		version =               diamondSection['Version']
		installationDirectory = Path(diamondSection['InstallationDirectory'])
		# binaryDirectory =       Path(diamondSection['BinaryDirectory'])
		self._toolChain =       Diamond(self.Host.Platform, self.DryRun, binaryPath, version, logger=self.Logger)
		self._toolChain.PreparseEnvironment(installationDirectory)

	def RunAll(self, fqnList, *args, **kwargs):
		"""Run a list of netlist compilations. Expand wildcards to all selected netlists."""
		self._testSuite.StartTimer()
		self.Logger.BaseIndent = int(len(fqnList) > 1)
		try:
			for fqn in fqnList:
				entity = fqn.Entity
				if (isinstance(entity, WildCard)):
					self.Logger.BaseIndent = 1
					for netlist in entity.GetLatticeNetlists():
						self.TryRun(netlist, *args, **kwargs)
				else:
					netlist = entity.LatticeNetlist
					self.TryRun(netlist, *args, **kwargs)
		except KeyboardInterrupt:
			self.LogError("Received a keyboard interrupt.")
		finally:
			self._testSuite.StopTimer()

		self.PrintOverallCompileReport()

		return self._testSuite.IsAllSuccess

	def Run(self, netlist, board):
		super().Run(netlist, board)

		netlist.PrjFile = self.Directories.Working / (netlist.ModuleName + ".prj")

		lseArgumentFile = self._WriteLSEProjectFile(netlist, board)
		self._prepareTime = self._GetTimeDeltaSinceLastEvent()

		self.LogNormal("Executing pre-processing tasks...")
		self._state = CompileState.PreCopy
		self._RunPreCopy(netlist)
		self._state = CompileState.PrePatch
		self._RunPreReplace(netlist)
		self._preTasksTime = self._GetTimeDeltaSinceLastEvent()

		self.LogNormal("Running Lattice Diamond LSE...")
		self._state = CompileState.Compile
		self._RunCompile(netlist, lseArgumentFile)			# attach to netlist
		self._compileTime = self._GetTimeDeltaSinceLastEvent()

		self.LogNormal("Executing post-processing tasks...")
		self._state = CompileState.PostCopy
		self._RunPostCopy(netlist)
		self._state = CompileState.PostPatch
		self._RunPostReplace(netlist)
		self._state = CompileState.PostDelete
		self._RunPostDelete(netlist)
		self._postTasksTime = self._GetTimeDeltaSinceLastEvent()

		self._endAt = datetime.now()

	def _WriteLSEProjectFile(self, netlist, board):
		device = board.Device
		argumentFile = SynthesisArgumentFile(netlist.PrjFile)
		argumentFile.Architecture = "\"{0}\"".format(device.Series)
		argumentFile.Device =       "\"{0}\"".format(device.ShortName)
		argumentFile.SpeedGrade =   str(device.SpeedGrade)
		argumentFile.Package =      "{0!s}{1!s}".format(device.Package, device.PinCount)
		argumentFile.TopLevel =     netlist.ModuleName
		argumentFile.LogFile =      self.Directories.Working / (netlist.ModuleName + ".lse.log")
		argumentFile.VHDLVersion =  self._vhdlVersion

		argumentFile.HDLParams.update(self._GetHDLParameters(netlist.ConfigSectionName))

		argumentFile.Write(self.pyIPCMIProject)
		return argumentFile

	def _RunCompile(self, netlist, lseArgumentFile):
		synth = self._toolChain.GetSynthesizer()
		synth.Parameters[synth.SwitchProjectFile] = netlist.ModuleName + ".prj"

		try:
			synth.Compile(lseArgumentFile.LogFile)
		except LatticeException as ex:
			raise CompilerException("Error while compiling '{0!s}'.".format(netlist)) from ex
		if synth.HasErrors:
			raise SkipableCompilerException("Error while compiling '{0!s}'.".format(netlist))
