# EMACS settings: -*-	tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:          Patrick Lehmann
#                   Martin Zabel
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
from enum                 import Enum, unique
from re                   import compile as re_compile

from pyIPCMI.ToolChain            import ConfigurationException


__api__ = [
	'BaseEnum',
	'Vendors',
	'Families', 'GenericFamilies', 'AlteraFamilies', 'LatticeFamilies', 'XilinxFamilies',
	'Devices',  'GenericDevices',  'AlteraDevices',  'LatticeDevices',  'XilinxDevices',
	'SubTypes', 'GenericSubTypes', 'AlteraSubTypes', 'LatticeSubTypes', 'XilinxSubTypes',
	'Packages',
	'Device',
	'Board'
]
__all__ = __api__


class BaseEnum(Enum):
	def __str__(self):
		return self.name

	def __repr__(self):
		return str(self).lower()


@unique
class Vendors(BaseEnum):
	Unknown =     0
	Generic =     1
	Altera =      2
	Lattice =     3
	MicroSemi =   4
	Xilinx =      5

	def __str__(self):
		return self.name

	def __repr__(self):
		return str(self).lower()


class Families(BaseEnum):
	"""Base enum for all Family enums."""

	# @CachedReadOnlyProperty
	@property
	def Token(self):
		return self.value

class GenericFamilies(Families):
	"""Enumeration of all generic families."""
	Unknown = None
	Generic = "g"

class AlteraFamilies(Families):
	"""Enumeration of all Altera families."""
	Max =       "m"
	Cyclone =   "c"
	Arria =     "a"
	Stratix =   "s"

class LatticeFamilies(Families):
	"""Enumeration of all Lattice families."""
	ECP =       "lfe"
	# TODO: MachXO, iCE, ...

class XilinxFamilies(Families):
	"""Enumeration of all Xilinx families."""
	Spartan = "s"
	Artix =   "a"
	Kintex =  "k"
	Virtex =  "v"
	Zynq =    "z"


class Devices(BaseEnum):
	"""Base enum for all Device enums."""

class GenericDevices(Devices):
	"""Enumeration of all generic devices."""
	Unknown =                   0
	Generic =                   1

class AlteraDevices(Devices):
	"""Enumeration of all Altera devices."""
	# Altera.Max devices
	Max2 =                    100
	Max4 =                    101
	Max5 =                    102
	Max10 =                   103
	# Altera.Cyclone devices
	Cyclone3 =                110
	Cyclone4 =                111
	Cyclone5 =                112
	# Altera.Arria devices
	Arria2 =                  120
	Arria5 =                  121
	# Altera.Stratix devices
	Stratix2 =                130
	Stratix4 =                131
	Stratix5 =                132
	Stratix10 =               133

class LatticeDevices(Devices):
	"""Enumeration of all Lattice devices."""
	# Lattice.iCE device
	iCE40 =                   200
	# Lattice.MachXO
	MachXO =                  210
	MachXO2 =                 211
	MachXO3 =                 212
	# Lattice.ECP
	ECP2 =                    220
	ECP3 =                    221
	ECP5 =                    222

class XilinxDevices(Devices):
	"""Enumeration of all Xilinx devices."""
	# Xilinx.Spartan devices
	Spartan3 =                310
	Spartan6 =                311
	# Spartan7 =                312
	# Xilinx.Artix devices
	Artix7 =                  320
	# Xilinx.Kintex devices
	Kintex7 =                 330
	KintexUltraScale =        331
	KintexUltraScalePlus =    332
	# Xilinx.Virtex devices
	Virtex2 =                 340
	Virtex4 =                 341
	Virtex5 =                 342
	Virtex6 =                 343
	Virtex7 =                 344
	VirtexUltraScale =        345
	VirtexUltraScalePlus =    346
	# Xilinx.Zynq devices
	Zynq7000 =                350


class SubTypes(BaseEnum):
	"""Base enum for all SubType enums."""

	# @CachedReadOnlyProperty
	@property
	def Groups(self):
		return self.value

class GenericSubTypes(SubTypes):
	"""Enumeration of all generic device subtype."""
	Unknown =   None
	Generic =   1
	NoSubType = ("",	"")

class AlteraSubTypes(SubTypes):
	"""Enumeration of all Altera device subtype."""
	NoSubType = ("",	"")

	LS =        ("ls",	"")
	E =         ("e",		"")
	GS =        ("gs",	"")
	GX =        ("gx",	"")
	GT =        ("gt",	"")
	GZ =        ("gz",	"")
	SX =        ("sx",	"")
	ST =        ("st",	"")

class LatticeSubTypes(SubTypes):
	"""Enumeration of all Lattice device subtype."""
	NoSubType = ("",	"")

	U =         ("u",		"")
	UM =        ("um",	"")

class XilinxSubTypes(SubTypes):
	"""Enumeration of all Xilinx device subtype."""
	NoSubType = ("",	"")

	DA =        ("d",		"a")
	E =         ("",		"e")
	AN =        ("",		"an")
	X =         ("x",		"")
	T =         ("",		"t")
	XT =        ("x",		"t")
	HT =        ("h",		"t")
	LX =        ("lx",	"")
	SXT =       ("sx",	"t")
	LXT =       ("lx",	"t")
	TXT =       ("tx",	"t")
	FXT =       ("fx",	"t")
	CXT =       ("cx",	"t")
	HXT =       ("hx",	"t")


@unique
class Packages(BaseEnum):
	Unknown =  0
	Generic =  1

	TQG =     10

	CLG =     20
	CPG =     21
	CSG =     22

	CABGA =   25

	FBG =     30
	FF =      31
	FFG =     32
	FG =      33
	FGG =     34
	FLG =     35
	FT =      36
	FTG =     37

	RB =      40
	RBG =     41
	RF =      42
	RS =      43

	E =       50
	Q =       51
	F =       52
	U =       53
	M =       54


class Device:
	def __init__(self, deviceString):
		# Device members
		self.__vendor =       Vendors.Unknown
		self.__family =       GenericFamilies.Unknown
		self.__device =       GenericDevices.Unknown
		self.__generation =   0
		self.__subtype =      GenericSubTypes.Unknown
		self.__number =       0
		self.__speedGrade =   0
		self.__package =      Packages.Unknown
		self.__pinCount =     0
		self.__deviceString = deviceString

		if (not isinstance(deviceString, str)):
			raise ValueError("Parameter 'deviceString' is not of type str.")
		if ((deviceString is None) or (deviceString == "")):
			raise ValueError("Parameter 'deviceString' is empty.")

		# vendor = GENERIC
		# ==========================================================================
		if   (deviceString[0:2].lower() == "ge"):   self._DecodeGeneric()									# ge - Generic FPGA device
		elif (deviceString[0:2].lower() == "xc"):   self._DecodeXilinx(deviceString)			# xc - Xilinx devices (XC = Xilinx Commercial)
		elif (deviceString[0:2].lower() == "ep"):   self._DecodeAltera(deviceString)			# ep - Altera devices
		elif (deviceString[0:3].lower() == "ice"):  self._DecodeLatticeICE(deviceString)	# ice - Lattice iCE series
		elif (deviceString[0:3].lower() == "lcm"):  self._DecodeLatticeLCM(deviceString)	# lcm - Lattice MachXO series
		elif (deviceString[0:3].lower() == "lfe"):  self._DecodeLatticeLFE(deviceString)	# lfe - Lattice ECP series
		else:                                       raise ConfigurationException("Unknown manufacturer code in device string '{0}'".format(deviceString))

	def _DecodeGeneric(self):
		self.__vendor =   Vendors.Generic
		self.__family =   GenericFamilies.Generic
		self.__device =   GenericDevices.Generic
		self.__subtype =  GenericSubTypes.Generic
		self.__package =  Packages.Generic

	def _DecodeAltera(self, deviceString):
		self.__vendor = Vendors.Altera

		deviceRegExpStr  = r"(?P<gen>\d{1,2})"  # generation
		deviceRegExpStr += r"(?P<fam>[acms])"  # family
		deviceRegExpStr += r"(?P<st>(ls|e|g|x|t|gs|gx|gt|gz|sx|st)?)"  # subtype
		deviceRegExp = re_compile(deviceRegExpStr)
		deviceRegExpMatch = deviceRegExp.match(deviceString[2:].lower())

		if (deviceRegExpMatch is not None):
			self.__generation = int(deviceRegExpMatch.group('gen'))

			family = deviceRegExpMatch.group('fam')
			for fam in AlteraFamilies:
				if fam.Token == family:
					self.__family = fam
					break
			else:
				raise ConfigurationException("Unknown Altera device family.")

			subtype = deviceRegExpMatch.group('st')
			if (subtype != ""):
				d = {"g": "gx", "x": "sx", "t": "gt"} # re-name for Stratix 10 and Arria 10
				if subtype in d: subtype = d[subtype]
				try:                    self.__subtype = AlteraSubTypes[subtype.upper()]
				except KeyError as ex:  raise ConfigurationException("Unknown subtype '{0}'.".format(subtype)) from ex
			else:
				self.__subtype = AlteraSubTypes.NoSubType

		else:
			raise ConfigurationException("RegExp mismatch.")

	def _DecodeLatticeICE(self, deviceString): # pylint:disable=unused-argument
		self.__vendor = Vendors.Lattice

	def _DecodeLatticeLCM(self, deviceString): # pylint:disable=unused-argument
		self.__vendor = Vendors.Lattice

	def _DecodeLatticeLFE(self, deviceString):
		self.__vendor = Vendors.Lattice
		self.__family = LatticeFamilies.ECP
		self.__generation = int(deviceString[3:4])

		if   (self.__generation == 3):  self._DecodeLatticeECP3(deviceString)
		elif (self.__generation == 5):  self._DecodeLatticeECP5(deviceString)
		else:                           raise ConfigurationException("Unknown Lattice ECP generation.")

	def _DecodeLatticeECP3(self, deviceString):
		self.__device =       LatticeDevices.ECP3
		self.__subtype =      LatticeSubTypes.NoSubType
		self.__number =       int(deviceString[5:8])

	def _DecodeLatticeECP5(self, deviceString):
		self.__device =       LatticeDevices.ECP5
		familyToken = deviceString[4:6].lower()
		if (familyToken == "u-"):
			self.__subtype =    LatticeSubTypes.U
			self.__number =     int(deviceString[6:8])
			self.__speedGrade = int(deviceString[10:11])
			self.__package =    Packages.CABGA
			self.__pinCount =   381                            # TODO: implement other packages and pin counts
		elif (familyToken == "um"):
			self.__subtype =    LatticeSubTypes.UM
			self.__number =     int(deviceString[7:9])
			self.__speedGrade = int(deviceString[11:12])
			self.__package =    Packages.CABGA
			self.__pinCount =   381                            # TODO: implement other packages and pin counts
		else:
			raise ConfigurationException("Unknown Lattice ECP5 subtype.")

	def _DecodeXilinx(self, deviceString):
		self.__vendor =     Vendors.Xilinx
		self.__generation = int(deviceString[2:3])

		familyToken = deviceString[3:4].lower()
		for fam in XilinxFamilies:
			if fam.Token == familyToken:
				self.__family = fam
				break
		else:
			raise ConfigurationException("Unknown Xilinx device family.")

		deviceRegExpStr  = r"(?P<st1>[a-z]{0,2})"   # device subtype - part 1
		deviceRegExpStr += r"(?P<no>\d{1,4})"       # device number
		deviceRegExpStr += r"(?P<st2>[aent]{0,2})"  # device subtype - part 2
		deviceRegExpStr += r"(?P<sg>[-1-5]{2})"     # speed grade
		deviceRegExpStr += r"(?P<pack>[a-z]{1,3})"  # package
		deviceRegExpStr += r"(?P<pins>\d{1,4})"     # pin count
		deviceRegExp = re_compile(deviceRegExpStr)
		deviceRegExpMatch = deviceRegExp.match(deviceString[4:].lower())

		if (deviceRegExpMatch is not None):
			subtype = deviceRegExpMatch.group('st1') + deviceRegExpMatch.group('st2')
			package = deviceRegExpMatch.group('pack')

			if (subtype != ""):
				try:                    self.__subtype = XilinxSubTypes[subtype.upper()]
				except KeyError as ex:  raise ConfigurationException("Unknown subtype '{0}'.".format(subtype)) from ex
			else:	                    self.__subtype = XilinxSubTypes.NoSubType
			self.__number =           int(deviceRegExpMatch.group('no'))
			self.__speedGrade =       int(deviceRegExpMatch.group('sg'))
			try:                      self.__package = Packages[package.upper()]
			except KeyError as ex:    raise ConfigurationException("Unknown package '{0}'.".format(package)) from ex
			self.__pinCount =         int(deviceRegExpMatch.group('pins'))
		else:
			raise ConfigurationException("RegExp mismatch.")

	@property
	def Vendor(self):     return self.__vendor
	@property
	def Family(self):     return self.__family
	@property
	def Device(self):     return self.__device
	@property
	def Generation(self): return self.__generation
	@property
	def Number(self):     return self.__number
	@property
	def SpeedGrade(self): return self.__speedGrade
	@property
	def PinCount(self):   return self.__pinCount
	@property
	def Package(self):    return self.__package
	@property
	def Name(self):       return self.FullName.upper()

	# @CachedReadOnlyProperty
	@property
	def ShortName(self):
		if (self.__vendor is Vendors.Generic):
			return "GENERIC"
		elif (self.__vendor is Vendors.Xilinx):
			subtype = self.__subtype.Groups
			if (self.__family is XilinxFamilies.Zynq):
				number_format = "{num:03d}"
			else:
				number_format = "{num}"
			return ("XC{gen}{fam}{st0}{num}{st1}".format(
				gen=self.__generation,
				fam=self.__family.Token,
				st0=subtype[0],
				num=number_format.format(num=self.__number),
				st1=subtype[1]
			)).upper()
		elif (self.__vendor is Vendors.Altera):
			if self.__generation == 5: return self.__deviceString[2:]
			return self.__deviceString
		elif (self.__vendor is Vendors.Lattice):
			return "{0!s}{1!s}{2!s}-{3!s}F".format(self.__family.value, self.__generation, self.__subtype, self.__number)
		else:
			raise NotImplementedError("Device.ShortName() not implemented for vendor {0!s}".format(self.__vendor))

	# @CachedReadOnlyProperty
	@property
	def FullName(self):
		if (self.__vendor is Vendors.Generic):
			return "GENERIC"
		elif (self.__vendor is Vendors.Xilinx):
			subtype = self.__subtype.Groups
			if (self.__family is XilinxFamilies.Zynq):
				number_format = "{num:03d}"
			else:
				number_format = "{num}"
			return ("XC{gen}{fam}{st0}{num}{st1}{sg}{pack}{pin}".format(
				gen=self.__generation,
				fam=self.__family.Token,
				st0=subtype[0],
				num=number_format.format(num=self.__number),
				st1=subtype[1],
				sg=self.__speedGrade,
				pack=str(self.__package),
				pin=self.__pinCount
			)).upper()
		elif (self.__vendor is Vendors.Altera):
			return self.__deviceString
		elif (self.__vendor is Vendors.Lattice):
			return self.__deviceString
		else:
			raise NotImplementedError("Device.FullName() not implemented for vendor {0!s}".format(self.__vendor))

	# @CachedReadOnlyProperty
	@property
	def FullName2(self):
		if (self.__vendor is Vendors.Generic):
			return "GENERIC"
		elif (self.__vendor is Vendors.Xilinx):
			subtype = self.__subtype.Groups
			if (self.__family is XilinxFamilies.Zynq):
				number_format = "{num:03d}"
			else:
				number_format = "{num}"
			return ("XC{gen}{fam}{st0}{num}{st1}{pack}{pin}{sg}".format(
				gen=self.__generation,
				fam=self.__family.Token,
				st0=subtype[0],
				num=number_format.format(num=self.__number),
				st1=subtype[1],
				pack=str(self.__package),
				pin=self.__pinCount,
				sg=self.__speedGrade
			)).upper()
		elif (self.__vendor is Vendors.Altera):
			return self.__deviceString
		elif (self.__vendor is Vendors.Lattice):
			return self.__deviceString
		else:
			raise NotImplementedError("Device.FullName() not implemented for vendor {0!s}".format(self.__vendor))

	# @CachedReadOnlyProperty
	@property
	def FamilyName(self):
		if (self.__family is XilinxFamilies.Zynq):
			return str(self.__family)
		else:
			return str(self.__family) + str(self.__generation)

	# @CachedReadOnlyProperty
	@property
	def Series(self):
		if self.__vendor is Vendors.Generic:
			return "GENERIC"
		elif self.__vendor is Vendors.Altera:
			d = {1: "", 2: " II", 3: " III", 4: " IV", 5: " V", 10: " 10"}
			return "{0!s}{1}".format(self.__family, d[self.__generation])
		elif self.__vendor is Vendors.Xilinx:
			if (self.__generation == 7):
				return "Series-7"
			else:
				return "{0!s}-{1}".format(self.__family, self.__generation)
		elif self.__vendor is Vendors.Lattice:
			return "{0!s}{1!s}".format(self.__device, self.__subtype)

	def GetVariables(self):
		result = {
			"DeviceShortName":    self.ShortName,
			"DeviceFullName":     self.FullName,
			"DeviceVendor":       str(self.Vendor),
			"DeviceFamily":       str(self.Family),
			"DeviceGeneration":   self.Generation,
			"DeviceSeries":       self.Series,
			"DeviceNumber":       self.Number,
			"DeviceSpeedGrade":   self.SpeedGrade,
			"DevicePackage":      self.Package,
			"DevicePinCount":     self.PinCount
		}
		return result

	def __str__(self):
		return self.FullName


class Board:
	def __init__(self, host, boardName=None, device=None):
		# Board members
		if (boardName is None):
			boardName = "GENERIC"
		elif (boardName == ""):
			raise ValueError("Parameter 'board' is empty.")
		elif (not isinstance(boardName, str)):
			raise ValueError("Parameter 'board' is not of type str.")

		boardName = boardName.lower()

		if (boardName == "custom"):
			if (device is None):
				raise ValueError("Parameter 'device' is None.")
			elif isinstance(device, Device):
				self.__device = device
			else:
				self.__device = Device(device)
		else:
			boardSectionName = None
			for board in host.Config['BOARDS']:
				if (board.lower() == boardName):
					boardSectionName = host.Config['BOARDS'][board] # real board name
					boardName = boardSectionName.split('.')[1]
					break
			else:
				raise ConfigurationException("Unknown board '{0}'".format(boardName))

			deviceName = host.Config[boardSectionName]['FPGA']
			self.__device = Device(deviceName)

		self.__boardName = boardName

	@property
	def Name(self):      return self.__boardName
	@property
	def Device(self):    return self.__device

	def GetVariables(self):
		result = {
			"BoardName" : self.__boardName
		}
		return result

	def __str__(self):
		return self.__boardName

	def __repr__(self):
		return str(self).lower()
