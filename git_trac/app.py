"""
The Application

There is only one instance. On the debug REPL (if you start with the
``--debug`` option) it is assigned to the variable ``app`` in the
global namespace.
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



from .config import Config
from .git_repository import GitRepository
from .trac_server import TracServer


class Application(object):

    def __init__(self):
        self.config = c = Config()
        self.trac = TracServer(c.trac_server_hostname,
                               c.trac_server_anonymous_xmlrpc,
                               c.trac_server_authenticated_xmlrpc)
        self.repo = GitRepository()
        self.git = self.repo.git

        
    def show_config(self):
        print(self.config)


