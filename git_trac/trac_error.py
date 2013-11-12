"""
Exception Classes for Trac
"""

##############################################################################
#  The "git trac ..." command extension for git
#  Copyright (C) 2013  Volker Braun <vbraun.name@gmail.com>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################

class TracError(RuntimeError):
    pass

class TracConnectionError(TracError):
    def __init__(self):
        TracError.__init__(self, "Connection to trac server failed.")

class TracInternalError(TracError):
    def __init__(self, fault):
        self._fault = fault
        self.faultCode = fault.faultCode

    def __str__(self):
        return str(self._fault)

