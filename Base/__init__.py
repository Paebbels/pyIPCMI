# EMACS settings: -*-  tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:          Patrick Lehmann
#
# Python Package:   Saves The pyIPCMI-Library configuration as python source code.
#
# License:
# ==============================================================================
# Copyright 2007-2016 Technische Universitaet Dresden - Germany
#                     Chair of VLSI-Design, Diagnostics and Architecture
# Copyright 2017-2018 Patrick Lehmann - Bötzingen, Germany
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
from lib.ExtendedConfigParser import ExtendedConfigParser
from Base.Logging             import ILogable


__api__ = [
	'IHost'
]
__all__ = __api__


class IHost(ILogable):
	"""This is a type hint class (interface description) for a host instance.

	It's needed until pyIPCMI requires Python 3.6.
	"""

	# instance fields
	Platform =    "string"
	pyIPCMIConfig =   ExtendedConfigParser()

	# methods
	def SaveAndReloadpyIPCMIConfiguration(self): pass

	# Syntax not supported by Python 3.5 -> requires 3.6
	# Platform :  str =                  None
	# pyIPCMIConfig : ExtendedConfigParser = None
