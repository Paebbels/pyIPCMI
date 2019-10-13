# EMACS settings: -*-	tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:          Patrick Lehmann
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
from collections          import OrderedDict
from enum                 import Enum, unique
from pathlib              import Path
from flags                import Flags

from lib.Functions        import Init
from lib.Decorators       import LazyLoadTrigger, ILazyLoadable
from pyIPCMI.ToolChain            import ConfigurationException


__api__ = [
	'EntityTypes',
	'_pyIPCMIEntityTypes_parser',
	'BaseFlags',
	'TestbenchKind', 'NetlistKind',
	'NamespaceRoot',
	'Visibility',
	'PathElement',
	'Namespace',
	'Library',
	'WildCard', 'StarWildCard', 'AskWildCard',
	'IPCore',
	'LazyPathElement',
	'Testbench', 'VHDLTestbench', 'CocoTestbench',
	'Netlist', 'XstNetlist', 'QuartusNetlist', 'LatticeNetlist', 'CoreGeneratorNetlist', 'VivadoNetlist',
	'FQN'
]
__all__ = __api__


@unique
class EntityTypes(Enum):
	Unknown = 0
	Source = 1
	Testbench = 2
	NetList = 3

	def __str__(self):
		if   (self is EntityTypes.Unknown):    return "??"
		elif (self is EntityTypes.Source):    return "src"
		elif (self is EntityTypes.Testbench):  return "tb"
		elif (self is EntityTypes.NetList):    return "nl"

def _pyIPCMIEntityTypes_parser(cls, value):
	if not isinstance(value, str):
		return Enum.__new__(cls, value)
	else:
		# map strings to enum values, default to Unknown
		return {
			'src':      EntityTypes.Source,
			'tb':        EntityTypes.Testbench,
			'nl':        EntityTypes.NetList
		}.get(value,	EntityTypes.Unknown)

# override __new__ method in EntityTypes with _pyIPCMIEntityTypes_parser
setattr(EntityTypes, '__new__', _pyIPCMIEntityTypes_parser)


class BaseFlags(Flags):
	__no_flags_name__ =   "Unknown"
	__all_flags_name__ =  "All"


class TestbenchKind(BaseFlags):
	VHDLTestbench = ()
	CocoTestbench = ()


class NetlistKind(BaseFlags):
	LatticeNetlist = ()
	QuartusNetlist = ()
	XstNetlist = ()
	CoreGeneratorNetlist = ()
	VivadoNetlist = ()


class NamespaceRoot:
	__LibraryRoot_Name = ""
	__LibraryRoot_SectionName = ""

	def __init__(self, host):
		self._host =                      host

		self.__LibraryRoot_Name =         host.LibraryName
		self.__LibraryRoot_SectionName =  host.LibraryName

		self.__libraries =                OrderedDict()
		self.__libraries[self.__LibraryRoot_Name.lower()] = (Library(host, self.__LibraryRoot_Name, self.__LibraryRoot_SectionName, self))

	@property
	def Libraries(self):          return [lib for lib in self.__libraries.values()]
	@property
	def LibraryNames(self):       return [libName for libName in self.__libraries.keys()]
	@property
	def DefaultLibraryName(self): return self.__LibraryRoot_Name

	def GetLibraries(self):       return self.__libraries.values()
	def GetLibraryNames(self):    return self.__libraries.keys()

	def __contains__(self, item):
		return item.lower() in self.__libraries

	def __getitem__(self, key):
		key = key.lower()
		return self.__libraries[key]

	def AddLibrary(self, libraryName, libraryPrefix):
		self.__libraries[libraryName.lower()] = (Library(self._host, libraryName, libraryPrefix, self))

@unique
class Visibility(Enum):
	Unknown =		0
	Private =   1
	Public =    2

	def __eq__(self, other):  return self.value == other.value
	def __ne__(self, other):  return self.value != other.value
	def __lt__(self, other):  return self.value <  other.value
	def __le__(self, other):  return self.value <= other.value
	def __gt__(self, other):  return self.value >  other.value
	def __ge__(self, other):  return self.value >= other.value

	@classmethod
	def Parse(cls, value):
		for key,member in cls.__members__.items():
			if (key == value):
				return member
		raise ValueError("'{0!s}' is not a valid {1}".format(value, cls.__name__))


class PathElement:
	def __init__(self, host, name, configSectionName, parent):
		self._host =              host
		self._name =              name
		self._parent =            parent
		self._configSectionName = configSectionName
		self._visibility =        Visibility.Unknown

		self._Load()

	@property
	def Name(self):               return self._name
	@property
	def Parent(self):             return self._parent
	@property
	def ConfigSectionName(self):  return self._configSectionName
	@property
	def ConfigSection(self):      return self._host.Config[self._configSectionName]
	@property
	def Level(self):              return self._parent.Level + 1
	@property
	def Visibility(self):         return self._visibility
	@property
	def IsVisible(self):          return self._host.Repository.Kind <= self._visibility

	@property
	def Path(self):
		cur = self
		result = []
		while True:
			result.insert(0, cur)
			cur = cur.Parent
			if isinstance(cur, Library):
				break
		else:
			raise ConfigurationException("Hierarchy error. Expected Library.")
		return result

	def _Load(self):
		self._visibility = Visibility.Parse(self.ConfigSection['Visibility'])

	def __str__(self):
		return "{0!s}.{1}".format(self.Parent, self.Name)


class Namespace(PathElement):
	def __init__(self, host, name, configSectionName, parent):
		self.__namespaces =    OrderedDict()
		self.__entities =      OrderedDict()
		super().__init__(host, name, configSectionName, parent)

	def _Load(self):
		super()._Load()
		for optionName in self.ConfigSection:
			kind = self.ConfigSection[optionName]
			if (kind == "Namespace"):
				# print("loading namespace: {0}".format(optionName))
				section = self._configSectionName + "." + optionName
				ns = Namespace(host=self._host, name=optionName, configSectionName=section, parent=self)
				self.__namespaces[optionName.lower()] = ns
			elif (kind == "Entity"):
				# print("loading entity: {0}".format(optionName))
				section = ".".join(["IP"] + self._configSectionName.split(".")[1:] + [optionName])
				ent = IPCore(host=self._host, name=optionName, configSectionName=section, parent=self)
				self.__entities[optionName.lower()] = ent

	@property
	def Namespaces(self):         return [ns for ns in self.GetNamespaces()]
	@property
	def NamespaceNames(self):     return [nsName for nsName in self.GetNamespaceNames()]
	@property
	def Entities(self):           return [entity for entity in self.GetEntities()]
	@property
	def EntityNames(self):        return [entityName for entityName in self.GetEntityNames()]

	def GetNamespaces(self):
		for namespace in self.__namespaces.values():
			if namespace.IsVisible:
				yield namespace

	def GetNamespaceNames(self):
		for namespace in self.__namespaces.values():
			if namespace.IsVisible:
				yield namespace.Name

	def GetEntities(self):
		for entity in self.__entities.values():
			if entity.IsVisible:
				yield entity

	def GetEntityNames(self):
		for entity in self.__entities.values():
			if entity.IsVisible:
				yield entity.Name

	def GetAllEntities(self):
		for namespace in self.GetNamespaces():
			for entity in namespace.GetAllEntities():
				yield entity
		for entity in self.GetEntities():
			yield entity

	def __getitem__(self, key):
		key = key.lower()
		try:
			item = self.__namespaces[key]
		except KeyError:
			item = self.__entities[key]
		if (not item.IsVisible):
			raise KeyError("Item '{0!s}' is not visible.".format(key))

		return item

	def pprint(self, indent=0):
		__indent = "  " * indent
		buffer = "{0}{1}\n".format(__indent, self.Name)
		for ent in self.GetEntities():
			buffer += ent.pprint(indent + 1)
		for ns in self.GetNamespaces():
			buffer += ns.pprint(indent + 1)
		return buffer


class Library(Namespace):
	@property
	def Level(self):
		return 0

	def __str__(self):
		return self.Name


class WildCard(PathElement):
	def GetEntities(self):
		raise NotImplementedError()

	def GetTestbenches(self, kind=TestbenchKind.All):
		for entity in self.GetEntities():
			for tb in entity.GetTestbenches():
				if (tb.Kind in kind):
					yield tb

	def GetVHDLTestbenches(self):  return self.GetTestbenches(TestbenchKind.VHDLTestbench)
	def GetCocoTestbenches(self):  return self.GetTestbenches(TestbenchKind.CocoTestbench)

	def GetNetlists(self, kind=NetlistKind.All):
		for entity in self.GetEntities():
			for nl in entity.GetNetlists(kind):
				if (nl.Kind in kind):
					yield nl

	def GetLatticeNetlists(self):  return self.GetNetlists(NetlistKind.LatticeNetlist)
	def GetQuartusNetlists(self):  return self.GetNetlists(NetlistKind.QuartusNetlist)
	def GetXSTNetlists(self):      return self.GetNetlists(NetlistKind.XstNetlist)
	def GetCoreGenNetlists(self):  return self.GetNetlists(NetlistKind.CoreGeneratorNetlist)
	def GetVivadoNetlists(self):   return self.GetNetlists(NetlistKind.VivadoNetlist)

	@property
	def Testbenches(self):        return [tb for tb in self.GetTestbenches()]
	@property
	def VHDLTestbenches(self):    return [tb for tb in self.GetVHDLTestbenches()]
	@property
	def CocoTestbenches(self):    return [tb for tb in self.GetCocoTestbenches()]

	@property
	def Netlists(self):           return [tb for tb in self.GetNetlists()]
	@property
	def LatticeNetlists(self):    return [nl for nl in self.GetLatticeNetlists()]
	@property
	def QuartusNetlists(self):    return [nl for nl in self.GetQuartusNetlists()]
	@property
	def XSTNetlists(self):        return [nl for nl in self.GetXSTNetlists()]
	@property
	def CoreGenNetlists(self):    return [nl for nl in self.GetCoreGenNetlists()]
	@property
	def VivadoNetlists(self):     return [nl for nl in self.GetVivadoNetlists()]


class StarWildCard(WildCard):
	def _Load(self):
		pass

	def GetEntities(self):
		for entity in self._parent.GetAllEntities():
			yield entity


class AskWildCard(WildCard):
	def _Load(self):
		pass

	def GetEntities(self):
		for entity in self._parent.GetEntities():
			yield entity


class IPCore(PathElement):
	def __init__(self, host, name, configSectionName, parent):
		self._dependencies =    []
		# Testbenches
		self._vhdltb =          []		# OrderedDict()
		self._cocotb =          []		# OrderedDict()
		# Netlists
		self._latticeNetlist =  []		# OrderedDict()
		self._quartusNetlist =  []		# OrderedDict()
		self._xstNetlist =      []		# OrderedDict()
		self._coreGenNetlist =  []		# OrderedDict()
		self._vivadoNetlist =   []		# OrderedDict()

		super().__init__(host, name, configSectionName, parent)

	@property
	def Dependencies(self):	  return self._dependencies

	@property
	def VHDLTestbench(self):
		if (len(self._vhdltb) == 0):
			raise ConfigurationException("No VHDL testbench configured for '{0!s}'.".format(self))
		return self._vhdltb[0]

	@property
	def CocoTestbench(self):
		if (len(self._cocotb) == 0):
			raise ConfigurationException("No Cocotb testbench configured for '{0!s}'.".format(self))
		return self._cocotb[0]

	def GetTestbenches(self, kind=TestbenchKind.All):
		if (TestbenchKind.VHDLTestbench in kind):
			for tb in self._vhdltb:
				if tb.IsVisible:
					yield tb
		if (TestbenchKind.CocoTestbench in kind):
			for tb in self._cocotb:
				if tb.IsVisible:
					yield tb

	@property
	def LatticeNetlist(self):
		if (len(self._latticeNetlist) == 0):
			raise ConfigurationException("No Lattice netlist configured for '{0!s}'.".format(self))
		return self._latticeNetlist[0]

	@property
	def QuartusNetlist(self):
		if (len(self._quartusNetlist) == 0):
			raise ConfigurationException("No Quartus-II netlist configured for '{0!s}'.".format(self))
		return self._quartusNetlist[0]

	@property
	def XSTNetlist(self):
		if (len(self._xstNetlist) == 0):
			raise ConfigurationException("No XST netlist configured for '{0!s}'.".format(self))
		return self._xstNetlist[0]

	@property
	def CGNetlist(self):
		if (len(self._coreGenNetlist) == 0):
			raise ConfigurationException("No CoreGen netlist configured for '{0!s}'.".format(self))
		return self._coreGenNetlist[0]

	@property
	def VivadoNetlist(self):
		if (len(self._vivadoNetlist) == 0):
			raise ConfigurationException("No Vivado netlist configured for '{0!s}'.".format(self))
		return self._vivadoNetlist[0]

	def GetNetlists(self, kind=NetlistKind.All): # mccabe:disable=MC0001
		if (NetlistKind.LatticeNetlist in kind):
			for nl in self._latticeNetlist:
				if nl.IsVisible:
					yield nl
		if (NetlistKind.QuartusNetlist in kind):
			for nl in self._quartusNetlist:
				if nl.IsVisible:
					yield nl
		if (NetlistKind.XstNetlist in kind):
			for nl in self._xstNetlist:
				if nl.IsVisible:
					yield nl
		if (NetlistKind.CoreGeneratorNetlist in kind):
			for nl in self._coreGenNetlist:
				if nl.IsVisible:
					yield nl
		if (NetlistKind.VivadoNetlist in kind):
			for nl in self._vivadoNetlist:
				if nl.IsVisible:
					yield nl

	def _Load(self):
		super()._Load()
		section = self.ConfigSection
		# load dependencies (as names)
		self._dependencies =  section['Dependencies'].split()

		# load testbenches and netlists
		for optionName in section:
			kind = section[optionName].lower()
			if (kind == "vhdltestbench"):
				sectionName = self._configSectionName.replace("IP", "TB") + "." + optionName
				tb = VHDLTestbench(host=self._host, name=optionName, configSectionName=sectionName, parent=self)
				self._vhdltb.append(tb)
				# self._vhdltb[optionName] = tb
			elif (kind == "cocotestbench"):
				sectionName = self._configSectionName.replace("IP", "COCOTB") + "." + optionName
				tb = CocoTestbench(host=self._host, name=optionName, configSectionName=sectionName, parent=self)
				self._cocotb.append(tb)
				# self._cocotb[optionName] = tb
			elif (kind == "lsenetlist"):
				sectionName = self._configSectionName.replace("IP", "LSE") + "." + optionName
				nl = LatticeNetlist(host=self._host, name=optionName, configSectionName=sectionName, parent=self)
				self._latticeNetlist.append(nl)
				# self._xstNetlist[optionName] = nl
			elif (kind == "quartusnetlist"):
				sectionName = self._configSectionName.replace("IP", "QMAP") + "." + optionName
				nl = QuartusNetlist(host=self._host, name=optionName, configSectionName=sectionName, parent=self)
				self._quartusNetlist.append(nl)
				# self._xstNetlist[optionName] = nl
			elif (kind == "xstnetlist"):
				sectionName = self._configSectionName.replace("IP", "XST") + "." + optionName
				nl = XstNetlist(host=self._host, name=optionName, configSectionName=sectionName, parent=self)
				self._xstNetlist.append(nl)
				# self._xstNetlist[optionName] = nl
			elif (kind == "coregennetlist"):
				sectionName = self._configSectionName.replace("IP", "CG") + "." + optionName
				nl = CoreGeneratorNetlist(host=self._host, name=optionName, configSectionName=sectionName, parent=self)
				self._coreGenNetlist.append(nl)
				# self._coreGenNetlist[optionName] = nl
			elif (kind == "vivadonetlist"):
				sectionName = self._configSectionName.replace("IP", "VIVADO") + "." + optionName
				nl = VivadoNetlist(host=self._host, name=optionName, configSectionName=sectionName, parent=self)
				self._vivadoNetlist.append(nl)
				# self._vivadoNetlist[optionName] = nl

	def pprint(self, indent=0):
		buffer = "{0}Entity: {1}\n".format("  " * indent, self.Name)
		if (len(self._vhdltb) > 0):
			buffer += self._vhdltb.pprint(indent + 1)
		if (len(self._cocotb) > 0):
			buffer += self._cocotb.pprint(indent + 1)
		if (len(self._xstNetlist) > 0):
			buffer += self._xstNetlist.pprint(indent + 1)
		if (len(self._coreGenNetlist) > 0):
			buffer += self._coreGenNetlist.pprint(indent + 1)
		if (len(self._vivadoNetlist) > 0):
			buffer += self._vivadoNetlist.pprint(indent + 1)
		return buffer


class LazyPathElement(PathElement, ILazyLoadable):
	def __init__(self, host, name, configSectionName, parent):
		self._kind =        None
		super().__init__(host, name, configSectionName, parent)
		ILazyLoadable.__init__(self)

	@property
	def Kind(self):                return self._kind

	def __str__(self):
		return "{0!s}.{1}".format(self._parent, self._name)


@unique
class SimulationResult(Enum):
	"""Simulation result enumeration."""
	NotRun =      0
	DryRun =      1
	Error =       2
	Failed =      3
	NoAsserts =   4
	Passed =      5
	GUIRun =      6


class Testbench(LazyPathElement):
	def __init__(self, host, name, configSectionName, parent):
		self._kind =        TestbenchKind.Unknown
		self._moduleName =  ""
		self._filesFile =   None
		self._result =      SimulationResult.NotRun
		super().__init__(host, name, configSectionName, parent)

	@property
	@LazyLoadTrigger
	def ModuleName(self):     return self._moduleName
	@property
	@LazyLoadTrigger
	def FilesFile(self):      return self._filesFile

	@property
	def Result(self):         return self._result
	@Result.setter
	def Result(self, value):  self._result = value

	# def __setattr__(self, key, value):
	# 	super().__setattr__(key, value)

	def _LazyLoadable_Load(self):
		super()._LazyLoadable_Load()
		self._moduleName =  self.ConfigSection["TestbenchModule"]
		self._filesFile =    Path(self.ConfigSection["FilesFile"])

	def pprint(self, indent):
		__indent = "  " * indent
		buffer  = "{0}Testbench:\n".format(__indent)
		buffer += "{0}  Files: {1!s}\n".format(__indent, self._filesFile)
		return buffer


class VHDLTestbench(Testbench):
	def __init__(self, host, name, configSectionName, parent):
		super().__init__(host, name, configSectionName, parent)
		self._kind = TestbenchKind.VHDLTestbench

	def _LazyLoadable_Load(self):
		super()._LazyLoadable_Load()

	def __str__(self):
		return super().__str__() + " (VHDL testbench)"

	def pprint(self, indent):
		__indent = "  " * indent
		buffer = "{0}VHDL Testbench:\n".format(__indent)
		buffer += "{0}  Files: {1!s}\n".format(__indent, self._filesFile)
		return buffer


class CocoTestbench(Testbench):
	def __init__(self, host, name, configSectionName, parent):
		self._topLevel =  ""
		super().__init__(host, name, configSectionName, parent)
		self._kind =      TestbenchKind.CocoTestbench

	@property
	@LazyLoadTrigger
	def TopLevel(self):
		return self._topLevel

	def _LazyLoadable_Load(self):
		super()._LazyLoadable_Load()
		self._topLevel =  self.ConfigSection["TopLevel"]

	def __str__(self):
		return super().__str__() + " (Cocotb testbench)"

	def pprint(self, indent):
		__indent = "  " * indent
		buffer = "{0}Cocotb Testbench:\n".format(__indent)
		buffer += "{0}  Files: {1!s}\n".format(__indent, self._filesFile)
		return buffer


class Netlist(LazyPathElement):
	def __init__(self, host, name, configSectionName, parent):
		self._kind =            NetlistKind.Unknown
		self._moduleName =      ""
		self._rulesFile =       None
		super().__init__(host, name, configSectionName, parent)

	@property
	@LazyLoadTrigger
	def ModuleName(self):     return self._moduleName
	@property
	@LazyLoadTrigger
	def RulesFile(self):      return self._rulesFile

	def _LazyLoadable_Load(self):
		super()._LazyLoadable_Load()

		self._moduleName =      self.ConfigSection["TopLevel"]
		self._dependencies =    self.ConfigSection['Dependencies'].split()
		value =                 self.ConfigSection["RulesFile"]
		self._rulesFile =       Path(value) if (value != "") else None


class XstNetlist(Netlist):
	def __init__(self, host, name, configSectionName, parent):
		self._filesFile =       None
		self._prjFile =         None
		self._xcfFile =         None
		self._filterFile =      None
		self._xstTemplateFile = None
		self._xstFile =         None
		super().__init__(host, name, configSectionName, parent)
		self._kind =            NetlistKind.XstNetlist

	@property
	@LazyLoadTrigger
	def FilesFile(self):        return self._filesFile
	@property
	@LazyLoadTrigger
	def XcfFile(self):          return self._xcfFile
	@property
	@LazyLoadTrigger
	def FilterFile(self):       return self._filterFile
	@property
	@LazyLoadTrigger
	def XstTemplateFile(self):  return self._xstTemplateFile

	@property
	def PrjFile(self):
		return self._prjFile
	@PrjFile.setter
	def PrjFile(self, value):
		if isinstance(value, str):
			value = Path(value)
		self._prjFile = value

	@property
	def XstFile(self):
		return self._xstFile
	@XstFile.setter
	def XstFile(self, value):
		if isinstance(value, str):
			value = Path(value)
		self._xstFile = value

	def _LazyLoadable_Load(self):
		super()._LazyLoadable_Load()
		self._filesFile =       Path(self.ConfigSection["FilesFile"])
		self._xcfFile =         Path(self.ConfigSection['XSTConstraintsFile'])
		self._filterFile =      Path(self.ConfigSection['XSTFilterFile'])
		self._xstTemplateFile = Path(self.ConfigSection['XSTOptionsFile'])

	def __str__(self):
		return super().__str__() + " (XST netlist)"

	def pprint(self, indent):
		__indent = "  " * indent
		buffer = "{0}Netlist: {1}\n".format(__indent, self._moduleName)
		buffer += "{0}  Files: {1!s}\n".format(__indent, self._filesFile)
		buffer += "{0}  Rules: {1!s}\n".format(__indent, self._rulesFile)
		return buffer

class QuartusNetlist(Netlist):
	def __init__(self, host, name, configSectionName, parent):
		self._filesFile =       None
		self._qsfFile =         None
		super().__init__(host, name, configSectionName, parent)
		self._kind =            NetlistKind.QuartusNetlist

	@property
	@LazyLoadTrigger
	def FilesFile(self):      return self._filesFile

	@property
	def QsfFile(self):        return self._qsfFile
	@QsfFile.setter
	def QsfFile(self, value):
		if isinstance(value, str):
			value = Path(value)
		self._qsfFile = value

	def _LazyLoadable_Load(self):
		super()._LazyLoadable_Load()
		self._filesFile = Path(self.ConfigSection["FilesFile"])

	def __str__(self):
		return super().__str__() + " (Quartus netlist)"

	def pprint(self, indent):
		__indent = "  " * indent
		buffer = "{0}Netlist: {1}\n".format(__indent, self._moduleName)
		buffer += "{0}  Files: {1!s}\n".format(__indent, self._filesFile)
		buffer += "{0}  Rules: {1!s}\n".format(__indent, self._rulesFile)
		return buffer


class LatticeNetlist(Netlist):
	def __init__(self, host, name, configSectionName, parent):
		self._filesFile =       None
		self._prjFile =         None
		super().__init__(host, name, configSectionName, parent)
		self._kind =            NetlistKind.LatticeNetlist

	@property
	@LazyLoadTrigger
	def FilesFile(self):        return self._filesFile

	@property
	def PrjFile(self):          return self._prjFile
	@PrjFile.setter
	def PrjFile(self, value):
		if isinstance(value, str):
			value = Path(value)
		self._prjFile = value

	def _LazyLoadable_Load(self):
		super()._LazyLoadable_Load()
		self._filesFile =        Path(self.ConfigSection["FilesFile"])

	def __str__(self):
		return super().__str__() + " (Lattice netlist)"

	def pprint(self, indent):
		__indent = "  " * indent
		buffer = "{0}Netlist: {1}\n".format(__indent, self._moduleName)
		buffer += "{0}  Files: {1!s}\n".format(__indent, self._filesFile)
		buffer += "{0}  Rules: {1!s}\n".format(__indent, self._rulesFile)
		return buffer


class CoreGeneratorNetlist(Netlist):
	def __init__(self, host, name, configSectionName, parent):
		self._xcoFile =         None
		super().__init__(host, name, configSectionName, parent)
		self._kind =            NetlistKind.CoreGeneratorNetlist

	def __str__(self):
		return super().__str__() + " (Core Generator netlist)"

	@property
	def FilesFile(self):      return None

	@property
	def XcoFile(self):        return self._xcoFile

	def _LazyLoadable_Load(self):
		super()._LazyLoadable_Load()
		self._xcoFile = Path(self.ConfigSection['CoreGeneratorFile'])

	def pprint(self, indent):
		__indent = "  " * indent
		buffer = "{0}Netlist: {1}\n".format(__indent, self._moduleName)
		buffer += "{0}  Rules: {1!s}\n".format(__indent, self._rulesFile)
		return buffer


class VivadoNetlist(Netlist):
	def __init__(self, host, name, configSectionName, parent):
		self._filesFile =       None
		self._tclFile =         None
		super().__init__(host, name, configSectionName, parent)
		self._kind =            NetlistKind.VivadoNetlist

	@property
	@LazyLoadTrigger
	def FilesFile(self):      return self._filesFile

	@property
	def TclFile(self):        return self._tclFile
	@TclFile.setter
	def TclFile(self, value):
		if isinstance(value, str):
			value = Path(value)
		self._tclFile = value

	def _LazyLoadable_Load(self):
		super()._LazyLoadable_Load()
		self._filesFile =       Path(self.ConfigSection["FilesFile"])

	def __str__(self):
		return super().__str__() + " (Vivado netlist)"

	def pprint(self, indent):
		__indent = "  " * indent
		buffer = "{0}Netlist: {1}\n".format(__indent, self._moduleName)
		buffer += "{0}  Files: {1!s}\n".format(__indent, self._filesFile)
		buffer += "{0}  Rules: {1!s}\n".format(__indent, self._rulesFile)
		return buffer


class FQN:
	def __init__(self, host, fqn, libraryName=None, defaultType=EntityTypes.Source):
		self.__host =   host
		self.__type =   None
		self.__parts =  []

		if (fqn is None):      raise ValueError("Parameter 'fqn' is None.")
		if (fqn == ""):        raise ValueError("Parameter 'fqn' is empty.")

		if (libraryName is None):
			libraryName = self.__host.Root.DefaultLibraryName

		# extract EntityType
		splitList1 = fqn.split(":")
		if (len(splitList1) == 1):
			self.__type = defaultType
			entity =      fqn
		elif (len(splitList1) == 2):
			self.__type = EntityTypes(splitList1[0])
			entity =      splitList1[1]
		else:
			raise ValueError("Argument 'fqn' has to many ':' signs.")

		# extract parts
		parts = entity.split(".")
		if (parts[0].lower() not in self.__host.Root):
			parts.insert(0, libraryName)

		# check and resolve parts
		cur = self.__host.Root
		self.__parts.append(cur)
		last = len(parts) - 1
		for pos,part in enumerate(parts):
			if ((pos == last) and ("*" in part)):
				pe = StarWildCard(host, part, "----", cur)
				self.__parts.append(pe)
			elif ((pos == last) and ("?" in part)):
				pe = AskWildCard(host, part, "----", cur)
				self.__parts.append(pe)
			else:
				try:
					pe = cur[part]
				except KeyError:
					raise ConfigurationException("Entity '{GREEN}{good}{RED}.{bad}{NOCOLOR}' not found.".format(good=(".".join(parts[:pos])), bad=(".".join(parts[pos:])), **Init.Foreground))
				self.__parts.append(pe)
				cur = pe

	def Root(self):
		return self.__host.Root

	@property
	def Entity(self):
		return self.__parts[-1]

	def __str__(self):
		return str(self.Entity)
