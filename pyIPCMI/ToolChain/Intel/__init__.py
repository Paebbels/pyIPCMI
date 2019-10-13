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
from pyIPCMI.ToolChain                import ToolChainException, VendorConfiguration


__api__ = [
	'IntelException',
	'Configuration'
]
__all__ = __api__


class IntelException(ToolChainException):
	pass


class Configuration(VendorConfiguration):
	"""Configuration routines for Intel as a vendor.

	This configuration provides a common installation directory setup for all
	Intel tools installed on a system.
	"""
	_vendor =               "Intel"                     #: The name of the tools vendor.
	_section  =             "INSTALL.Intel"             #: The name of the configuration section. Pattern: ``INSTALL.Vendor.ToolName``.
	_template = {
		"Windows": {
			_section: {
				"InstallationDirectory": "C:/IntelFPGA"
			}
		},
		"Linux": {
			_section: {
				"InstallationDirectory": "/opt/IntelFPGA"
			}
		}
	}                                                   #: The template for the configuration sections represented as nested dictionaries.

	def _GetDefaultInstallationDirectory(self):
		# Intel = environ.get("QUARTUS_ROOTDIR")				# on Windows: D:\IntelFPGA\16.1\quartus
		# if (Intel is not None):
		# 	return str(Path(Intel).parent.parent)

		path = self._TestDefaultInstallPath({
			"Windows":  ("IntelFPGA", "intelFPGA_lite"),
			"Linux":    ("intelFPGA", "IntelFPGA", "intelFPGA_lite")
		})
		if path is None:
			return super()._GetDefaultInstallationDirectory()

		return path.as_posix()
