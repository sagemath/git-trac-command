"""
Container for Configuration Data
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



import os
import json
import logging


class Config(object):

    def __init__(self):
        self._load()

    def _save(self):
        pass

    def _load(self):
        pass
        
    @property
    def version(self):
        return 1

    @property
    def trac_server_hostname(self):
        return 'http://trac.sagemath.org'

    @property
    def trac_server_anonymous_xmlrpc(self):
        return 'xmlrpc'

    @property
    def trac_server_authenticated_xmlrpc(self):
        return 'login/xmlrpc'

