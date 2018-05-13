# EMACS settings: -*-	tab-width: 2; indent-tabs-mode: t; python-indent-offset: 2 -*-
# vim: tabstop=2:shiftwidth=2:noexpandtab
# kate: tab-width 2; replace-tabs off; indent-width 2;
#
# ==============================================================================
# Authors:            Patrick Lehmann
#
# Auxillary Classes:  Auxillary classes to implement call by reference.
#
# License:
# ==============================================================================
# Copyright 2017-2018 Patrick Lehmann - Bötzingen, Germany
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


__api__ = [
	'CallByRefParam',
	'CallByRefBoolParam',
	'CallByRefIntParam'
]
__all__ = __api__

class CallByRefParam:
	"""Implements a "call by reference" parameter.

	.. seealso::

	   :py:class:`CallByRefBoolParam`
	     A special "call by reference" implementation for boolean reference types.
	   :py:class:`CallByRefIntParam`
	     A special "call by reference" implementation for integer reference types.
	"""
	def __init__(self, value=None):
		self.value = value

	def __ilshift__(self, other):
		self.value = other
		return self

	def __eq__(self, other):  return self.value == other
	def __ne__(self, other):  return self.value != other
	def __repr__(self):       return repr(self.value)
	def __str__(self):        return str(self.value)


class CallByRefBoolParam(CallByRefParam):
	"""A special "call by reference" implementation for boolean reference types."""
	# unary operators
	def __neg__(self):         return not self.value

	# binary operators - logical
	def __and__(self, other):  return self.value and other
	def __or__(self, other):   return self.value or  other

	# binary inplace operators
	def __iand__(self, other):
		self.value = self.value and other
		return self
	def __ior__(self, other):
		self.value = self.value or other
		return self

	# type conversion operators
	def __bool__(self): return self.value
	def __int__(self):  return int(self.value)


class CallByRefIntParam(CallByRefParam):
	"""A special "call by reference" implementation for integer reference types."""

	# unary operators
	def __neg__(self):            return not self.value

	# binary operators - arithmetic
	def __add__(self, other):     return self.value +  other
	def __sub__(self, other):     return self.value -  other
	def __truediv__(self, other): return self.value /  other
	def __mul__(self, other):     return self.value *  other
	def __mod__(self, other):     return self.value %  other
	def __pow__(self, other):     return self.value ** other

	# binary operators - comparison
	def __eq__(self, other):  return self.value == other
	def __ne__(self, other):  return self.value != other
	def __lt__(self, other):  return self.value <  other
	def __le__(self, other):  return self.value <= other
	def __gt__(self, other):  return self.value >  other
	def __ge__(self, other):  return self.value >= other

	# type conversion operators
	def __bool__(self):       return bool(self.value)
	def __int__(self):        return self.value
