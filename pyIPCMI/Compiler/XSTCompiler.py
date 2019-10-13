# EMACS settings: -*-	tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:          Patrick Lehmann
#                   Martin Zabel
#
# Python Module:    Xilinx ISE synthesizer (compiler).
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
from datetime                 import datetime
from pathlib                  import Path

from pyIPCMI.Base.Project             import ToolChain, Tool
from pyIPCMI.DataBase.Entity          import WildCard
from pyIPCMI.ToolChain.Xilinx         import XilinxProjectExportMixIn
from pyIPCMI.ToolChain.Xilinx.ISE     import ISE, ISEException
from pyIPCMI.Compiler                 import CompilerException, SkipableCompilerException, CompileState, Compiler as BaseCompiler


__api__ = [
	'Compiler'
]
__all__ = __api__


class Compiler(BaseCompiler, XilinxProjectExportMixIn):
	TOOL_CHAIN =      ToolChain.Xilinx_ISE
	TOOL =            Tool.Xilinx_XST

	class __Directories__(BaseCompiler.__Directories__):
		XSTFiles =    None

	def __init__(self, host, dryRun, noCleanUp):
		super().__init__(host, dryRun, noCleanUp)
		XilinxProjectExportMixIn.__init__(self)

		configSection = host.Config['CONFIG.DirectoryNames']
		self.Directories.Working =  host.Directories.Temp / configSection['ISESynthesisFiles']
		self.Directories.XSTFiles = host.Directories.Root / configSection['ISESynthesisFiles']
		self.Directories.Netlist =  host.Directories.Root / configSection['NetlistFiles']

		self._PrepareCompiler()

	def _PrepareCompiler(self):
		super()._PrepareCompiler()
		iseSection =            self.Host.Config['INSTALL.Xilinx.ISE']
		version =               iseSection['Version']
		installationDirectory = Path(iseSection['InstallationDirectory'])
		binaryPath =            Path(iseSection['BinaryDirectory'])
		self._toolChain =       ISE(self.Host.Platform, self.DryRun, binaryPath, version, logger=self.Logger)
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
					for netlist in entity.GetXSTNetlists():
						self.TryRun(netlist, *args, **kwargs)
				else:
					netlist = entity.XSTNetlist
					self.TryRun(netlist, *args, **kwargs)
		except KeyboardInterrupt:
			self.LogError("Received a keyboard interrupt.")
		finally:
			self._testSuite.StopTimer()

		self.PrintOverallCompileReport()

		return self._testSuite.IsAllSuccess

	def Run(self, netlist, board):
		super().Run(netlist, board)

		netlist.XstFile = self.Directories.Working / (netlist.ModuleName + ".xst")
		netlist.PrjFile = self.Directories.Working / (netlist.ModuleName + ".prj")

		self._WriteXilinxProjectFile(netlist.PrjFile, "XST")
		self._WriteXstOptionsFile(netlist, board.Device)
		self._prepareTime = self._GetTimeDeltaSinceLastEvent()

		self.LogNormal("Executing pre-processing tasks...")
		self._state = CompileState.PreCopy
		self._RunPreCopy(netlist)
		self._state = CompileState.PrePatch
		self._RunPreReplace(netlist)
		self._preTasksTime = self._GetTimeDeltaSinceLastEvent()

		self.LogNormal("Running Xilinx Synthesis Tool...")
		self._state = CompileState.Compile
		self._RunCompile(netlist)
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

	def _WriteSpecialSectionIntoConfig(self, device):
		# add the key Device to section SPECIAL at runtime to change interpolation results
		self.Host.Config['SPECIAL'] = {}
		self.Host.Config['SPECIAL']['Device'] =        device.FullName
		self.Host.Config['SPECIAL']['DeviceSeries'] =  device.Series
		self.Host.Config['SPECIAL']['OutputDir']	=      self.Directories.Working.as_posix()

	def _RunCompile(self, netlist):
		reportFilePath = self.Directories.Working / (netlist.ModuleName + ".log")

		xst = self._toolChain.GetXst()
		xst.Parameters[xst.SwitchIntStyle] =    "xflow"
		xst.Parameters[xst.SwitchXstFile] =      netlist.ModuleName + ".xst"
		xst.Parameters[xst.SwitchReportFile] =  str(reportFilePath)
		try:
			xst.Compile()
		except ISEException as ex:
			raise CompilerException("Error while compiling '{0!s}'.".format(netlist)) from ex
		if xst.HasErrors:
			raise SkipableCompilerException("Error while compiling '{0!s}'.".format(netlist))


	def _WriteXstOptionsFile(self, netlist, device):
		self.LogVerbose("Generating XST options file.")

		# read XST options file template
		self.LogDebug("Reading Xilinx Compiler Tool option file from '{0!s}'".format(netlist.XstTemplateFile))
		if (not netlist.XstTemplateFile.exists()):
			raise CompilerException("XST template files '{0!s}' not found.".format(netlist.XstTemplateFile))\
				from FileNotFoundError(str(netlist.XstTemplateFile))

		with netlist.XstTemplateFile.open('r') as fileHandle:
			xstFileContent = fileHandle.read()

		xstTemplateDictionary = {
			'prjFile':                                                            str(netlist.PrjFile),
			'UseNewParser': self.Host.Config[netlist.ConfigSectionName]                  ['XSTOption.UseNewParser'],
			'InputFormat': self.Host.Config[netlist.ConfigSectionName]                   ['XSTOption.InputFormat'],
			'OutputFormat': self.Host.Config[netlist.ConfigSectionName]                  ['XSTOption.OutputFormat'],
			'OutputName':                                                         netlist.ModuleName,
			'Part':                                                               str(device),
			'TopModuleName':                                                      netlist.ModuleName,
			'OptimizationMode': self.Host.Config[netlist.ConfigSectionName]              ['XSTOption.OptimizationMode'],
			'OptimizationLevel': self.Host.Config[netlist.ConfigSectionName]             ['XSTOption.OptimizationLevel'],
			'PowerReduction': self.Host.Config[netlist.ConfigSectionName]                ['XSTOption.PowerReduction'],
			'IgnoreSynthesisConstraintsFile': self.Host.Config[netlist.ConfigSectionName]['XSTOption.IgnoreSynthesisConstraintsFile'],
			'SynthesisConstraintsFile':                                           str(netlist.XcfFile),
			'KeepHierarchy': self.Host.Config[netlist.ConfigSectionName]                 ['XSTOption.KeepHierarchy'],
			'NetListHierarchy': self.Host.Config[netlist.ConfigSectionName]              ['XSTOption.NetListHierarchy'],
			'GenerateRTLView': self.Host.Config[netlist.ConfigSectionName]               ['XSTOption.GenerateRTLView'],
			'GlobalOptimization': self.Host.Config[netlist.ConfigSectionName]            ['XSTOption.Globaloptimization'],
			'ReadCores': self.Host.Config[netlist.ConfigSectionName]                     ['XSTOption.ReadCores'],
			'SearchDirectories':                                                  '"{0!s}"'.format(self.Directories.Destination),
			'WriteTimingConstraints': self.Host.Config[netlist.ConfigSectionName]        ['XSTOption.WriteTimingConstraints'],
			'CrossClockAnalysis': self.Host.Config[netlist.ConfigSectionName]            ['XSTOption.CrossClockAnalysis'],
			'HierarchySeparator': self.Host.Config[netlist.ConfigSectionName]            ['XSTOption.HierarchySeparator'],
			'BusDelimiter': self.Host.Config[netlist.ConfigSectionName]                  ['XSTOption.BusDelimiter'],
			'Case': self.Host.Config[netlist.ConfigSectionName]                          ['XSTOption.Case'],
			'SliceUtilizationRatio': self.Host.Config[netlist.ConfigSectionName]         ['XSTOption.SliceUtilizationRatio'],
			'BRAMUtilizationRatio': self.Host.Config[netlist.ConfigSectionName]          ['XSTOption.BRAMUtilizationRatio'],
			'DSPUtilizationRatio': self.Host.Config[netlist.ConfigSectionName]           ['XSTOption.DSPUtilizationRatio'],
			'LUTCombining': self.Host.Config[netlist.ConfigSectionName]                  ['XSTOption.LUTCombining'],
			'ReduceControlSets': self.Host.Config[netlist.ConfigSectionName]             ['XSTOption.ReduceControlSets'],
			'Verilog2001': self.Host.Config[netlist.ConfigSectionName]                   ['XSTOption.Verilog2001'],
			'FSMExtract': self.Host.Config[netlist.ConfigSectionName]                    ['XSTOption.FSMExtract'],
			'FSMEncoding': self.Host.Config[netlist.ConfigSectionName]                   ['XSTOption.FSMEncoding'],
			'FSMSafeImplementation': self.Host.Config[netlist.ConfigSectionName]         ['XSTOption.FSMSafeImplementation'],
			'FSMStyle': self.Host.Config[netlist.ConfigSectionName]                      ['XSTOption.FSMStyle'],
			'RAMExtract': self.Host.Config[netlist.ConfigSectionName]                    ['XSTOption.RAMExtract'],
			'RAMStyle': self.Host.Config[netlist.ConfigSectionName]                      ['XSTOption.RAMStyle'],
			'ROMExtract': self.Host.Config[netlist.ConfigSectionName]                    ['XSTOption.ROMExtract'],
			'ROMStyle': self.Host.Config[netlist.ConfigSectionName]                      ['XSTOption.ROMStyle'],
			'MUXExtract': self.Host.Config[netlist.ConfigSectionName]                    ['XSTOption.MUXExtract'],
			'MUXStyle': self.Host.Config[netlist.ConfigSectionName]                      ['XSTOption.MUXStyle'],
			'DecoderExtract': self.Host.Config[netlist.ConfigSectionName]                ['XSTOption.DecoderExtract'],
			'PriorityExtract': self.Host.Config[netlist.ConfigSectionName]               ['XSTOption.PriorityExtract'],
			'ShRegExtract': self.Host.Config[netlist.ConfigSectionName]                  ['XSTOption.ShRegExtract'],
			'ShiftExtract': self.Host.Config[netlist.ConfigSectionName]                  ['XSTOption.ShiftExtract'],
			'XorCollapse': self.Host.Config[netlist.ConfigSectionName]                   ['XSTOption.XorCollapse'],
			'AutoBRAMPacking': self.Host.Config[netlist.ConfigSectionName]               ['XSTOption.AutoBRAMPacking'],
			'ResourceSharing': self.Host.Config[netlist.ConfigSectionName]               ['XSTOption.ResourceSharing'],
			'ASyncToSync': self.Host.Config[netlist.ConfigSectionName]                   ['XSTOption.ASyncToSync'],
			'UseDSP48': self.Host.Config[netlist.ConfigSectionName]                      ['XSTOption.UseDSP48'],
			'IOBuf': self.Host.Config[netlist.ConfigSectionName]                         ['XSTOption.IOBuf'],
			'MaxFanOut': self.Host.Config[netlist.ConfigSectionName]                     ['XSTOption.MaxFanOut'],
			'BufG': self.Host.Config[netlist.ConfigSectionName]                          ['XSTOption.BufG'],
			'RegisterDuplication': self.Host.Config[netlist.ConfigSectionName]           ['XSTOption.RegisterDuplication'],
			'RegisterBalancing': self.Host.Config[netlist.ConfigSectionName]             ['XSTOption.RegisterBalancing'],
			'SlicePacking': self.Host.Config[netlist.ConfigSectionName]                  ['XSTOption.SlicePacking'],
			'OptimizePrimitives': self.Host.Config[netlist.ConfigSectionName]            ['XSTOption.OptimizePrimitives'],
			'UseClockEnable': self.Host.Config[netlist.ConfigSectionName]                ['XSTOption.UseClockEnable'],
			'UseSyncSet': self.Host.Config[netlist.ConfigSectionName]                    ['XSTOption.UseSyncSet'],
			'UseSyncReset': self.Host.Config[netlist.ConfigSectionName]                  ['XSTOption.UseSyncReset'],
			'PackIORegistersIntoIOBs': self.Host.Config[netlist.ConfigSectionName]       ['XSTOption.PackIORegistersIntoIOBs'],
			'EquivalentRegisterRemoval': self.Host.Config[netlist.ConfigSectionName]     ['XSTOption.EquivalentRegisterRemoval'],
			'SliceUtilizationRatioMaxMargin': self.Host.Config[netlist.ConfigSectionName]['XSTOption.SliceUtilizationRatioMaxMargin']
		}

		xstFileContent = xstFileContent.format(**xstTemplateDictionary)

		hdlParameters=self._GetHDLParameters(netlist.ConfigSectionName)
		if(len(hdlParameters)>0):
			xstFileContent += "-generics {"
			for keyValuePair in hdlParameters.items():
				xstFileContent += " {0}={1}".format(*keyValuePair)
			xstFileContent += " }\n"

		self.LogDebug("Writing Xilinx Compiler Tool option file to '{0!s}'".format(netlist.XstFile))
		with netlist.XstFile.open('w') as fileHandle:
			fileHandle.write(xstFileContent)
