# EMACS settings: -*-  tab-width: 2; indent-tabs-mode: t -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
# =============================================================================
#               ___ ____   ____ __  __ ___
#   _ __  _   _|_ _|  _ \ / ___|  \/  |_ _|
#  | '_ \| | | || || |_) | |   | |\/| || |
#  | |_) | |_| || ||  __/| |___| |  | || |
#  | .__/ \__, |___|_|    \____|_|  |_|___|
#  |_|    |___/
# =============================================================================
# Authors:            Patrick Lehmann
#
# Package installer:  An IP Core Management Infrastructure written in Python - pyIPCMI.
#
#
# License:
# ============================================================================
# Copyright 2017-2019 Patrick Lehmann - Bötzingen, Germany
# Copyright 2007-2016 Technische Universität Dresden - Germany
#                     Chair of VLSI-Design, Diagnostics and Architecture
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#		http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# SPDX-License-Identifier: Apache-2.0
# ============================================================================
#
import setuptools

with open("README.md", "r") as file:
	long_description = file.read()

requirements = []
with open("requirements.txt") as file:
	for line in file.readlines():
		requirements.append(line)

projectName = "pyIPCMI"

github_url =  "https://github.com/Paebbels/" + projectName
rtd_url =     "https://" + projectName + ".readthedocs.io/en/latest/"

setuptools.setup(
	name=projectName,
	version="1.1.5",

	author="Patrick Lehmann",
	author_email="Paebbels@gmail.com",
	# maintainer="Patrick Lehmann",
	# maintainer_email="Paebbels@gmail.com",

	description="An IP Core Management Infrastructure written in Python - pyIPCMI.",
	long_description=long_description,
	long_description_content_type="text/markdown",

	url=github_url,
	project_urls={
		'Documentation': rtd_url,
		'Source Code':   github_url,
		'Issue Tracker': github_url + "/issues"
	},
	# download_url="",

	packages=setuptools.find_packages(),
	classifiers=[
		"License :: OSI Approved :: Apache Software License",
		"Operating System :: OS Independent",
		"Operating System :: Microsoft :: Windows :: Windows 7",
		"Operating System :: Microsoft :: Windows :: Windows 8",
		"Operating System :: Microsoft :: Windows :: Windows 10",
		"Operating System :: POSIX :: Linux",
		"Operating System :: MacOS",
		"Programming Language :: Python :: 3 :: Only",
		"Programming Language :: Python :: 3.5",
		"Programming Language :: Python :: 3.6",
		"Programming Language :: Python :: 3.7",
		"Programming Language :: Python :: 3.8",
		"Development Status :: 4 - Beta",
#		"Development Status :: 5 - Production/Stable",
		"Intended Audience :: Developers",
		"Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
		"Topic :: Software Development :: Build Tools",
		"Topic :: Software Development :: Testing",
		"Topic :: Software Development :: Testing :: Unit",
		"Topic :: Software Development :: Version Control :: Git",
		"Topic :: System :: Archiving :: Packaging",
		"Topic :: Text Processing :: Filters",
		"Topic :: Utilities"
	],
	keywords="Python3 Generic-Library IP-Core, Management, Packaging, Simulation, Synthesis, Pre-Processing, Post-Processing",

	python_requires='>=3.5',
	install_requires=requirements,
	# provides=
	# obsoletes=
)