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
import sys

from .git_error import GitError


class Config(object):

    def __init__(self, git):
        self._git = git
        self._debug = False

    def _save(self, config_option, value):
        try:
            self._git.config('--local', '--unset-all', config_option)
        except GitError:
            pass
        if len(value.strip()) != 0:
            self._git.config('--local', '--add', config_option, value)

    def _load(self, config_option):
        return self._git.config('--get', config_option).strip()

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = bool(value)
    
    @property
    def version(self):
        return 1

    @property
    def server_hostname(self):
        return 'https://trac.sagemath.org'

    @property
    def server_realm(self):
        return 'sage.math.washington.edu'

    @property
    def server_anonymous_xmlrpc(self):
        return 'xmlrpc'

    @property
    def server_authenticated_xmlrpc(self):
        return 'login/xmlrpc'

    @property
    def username(self):
        try:
            return os.environ['TRAC_USERNAME']
        except KeyError:
            pass
        try:
            return self._load('trac.username')
        except GitError:
            raise AuthenticationError('Use "git trac config --user=<name>"'
                                      ' to set your trac username')

    @username.setter
    def username(self, value):
        self._save('trac.username', value)

    @property
    def password(self):
        try:
            return os.environ['TRAC_PASSWORD']
        except KeyError:
            pass
        try:
            return self._load('trac.password')
        except GitError:
            raise AuthenticationError('Use "git trac config --pass=<secret>"'
                                      ' to set your trac password')

    @password.setter
    def password(self, value):
        self._save('trac.password', value)

class AuthenticationError(Exception):
    pass
