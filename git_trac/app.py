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
        self.repo = GitRepository()
        self.git = git = self.repo.git
        self.config = c = Config(git)
        self.trac = TracServer(c.server_hostname,
                               c.server_anonymous_xmlrpc,
                               c.server_authenticated_xmlrpc)

    def search(self, branch=None):
        if branch is not None:
            result = self.trac.search_branch(branch)
        else:
            raise ValueError('search for what?')
        print(result)


    def save_trac_username(self, username):
        self.config.username = username

    def save_trac_password(self, password):
        self.config.password = password
        
    def print_config(self):
        """
        Print configuration information

        EXAMPLES::

            sage: app.print_config()
            Trac xmlrpc URL:
                http://trac.sagemath.org/xmlrpc (anonymous)
                http://trac.sagemath.org/login/xmlrpc (authenticated)
            Username: trac_user
            Password: trac_pass
        """
        c = self.config
        import urllib.parse
        print('Trac xmlrpc URL:')
        url_anon = urllib.parse.urljoin(c.server_hostname, 
                                        c.server_anonymous_xmlrpc)
        print('    {0} (anonymous)'.format(url_anon))
        url_auth = urllib.parse.urljoin(c.server_hostname, 
                                        c.server_authenticated_xmlrpc)
        print('    {0} (authenticated)'.format(url_auth))
        
        print('Username: {0}'.format(c.username))
        print('Password: {0}'.format(c.password))

