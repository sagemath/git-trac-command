"""
Interface to the Sage Trac server

Uses XML-RPC to talk to the trac server.

EXAMPLES::

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

from datetime import datetime

try:
    # Python 3.3+
    from xmlrpc.client import ServerProxy
    from .digest_transport import DigestTransport, AuthenticatedDigestTransport
    from urllib import parse as url_parse
except ImportError:
    # Python 2.7
    from xmlrpclib import ServerProxy
    from .digest_transport_py2 import DigestTransport, AuthenticatedDigestTransport
    from urllib2 import urlparse as url_parse

    
from .logger import logger
from .trac_ticket import TracTicket
from .trac_error import TracAuthenticationError
from .cached_property import cached_property

class TracServer(object):

    def __init__(self, config):
        self.config = config
        self._current_ticket_number = None

    @cached_property
    def url_anonymous(self):
        return url_parse.urljoin(self.config.server_hostname, 
                                 self.config.server_anonymous_xmlrpc)

    @cached_property
    def url_authenticated(self):
        return url_parse.urljoin(self.config.server_hostname, 
                                 self.config.server_authenticated_xmlrpc)

    @cached_property 
    def anonymous_proxy(self):
        transport = DigestTransport()
        return ServerProxy(
            self.url_anonymous,
            transport=transport,
            verbose=self.config.debug
        )

    @cached_property 
    def authenticated_proxy(self):
        transport = AuthenticatedDigestTransport(
            realm=self.config.server_realm, 
            url=self.config.server_hostname, 
            username=self.config.username, 
            password=self.config.password)
        return ServerProxy(
            self.url_authenticated,
            transport=transport,
            verbose=self.config.debug
        )

    def get_ssh_keys(self):
        return self.authenticated_proxy.sshkeys.getkeys()

    def get_ssh_fingerprints(self):
        import tempfile
        import subprocess
        fingerprints = []
        try:
            fd, tmp = tempfile.mkstemp()
            os.close(fd)
            for key in self.get_ssh_keys():
                key = key.strip()
                if not key:
                    logger.debug('Skipping empty ssh key line')
                    continue
                with open(tmp, 'w') as f:
                    f.write(key)
                try:
                    out = subprocess.check_output(['ssh-keygen', '-lf', tmp])
                except subprocess.CalledProcessError as error:
                    logger.error(error)
                    logger.error('The SSH key "{0}" is probably invaild.'.format(key))
                    raise error
                yield out.decode('utf-8').strip()
        finally:
            os.remove(tmp)

    def __repr__(self):
        return "Trac server at " + self.config.server_hostname

    def load(self, ticket_number):
        ticket_number = int(ticket_number)
        ticket = TracTicket(ticket_number, self.anonymous_proxy)
        return ticket

    def remote_branch(self, ticket_number):
        ticket = self.load(ticket_number)
        branch = ticket.branch
        if branch == '':
            raise ValueError('"Branch:" field is not set on ticket #'
                             + str(ticket_number))
        return branch

    def set_remote_branch(self, ticket, new_branch):
        """
        Replace the trac "Branch:" field with ``new_branch``
        
        INPUT:

        - ``ticket`` -- a :class:`TracTicket`. The output of
          :meth:`load`, for example.

        - ``new_branch`` -- string.
        """
        attributes = {'_ts': ticket._data['_ts'],
                      'branch': new_branch}
        comment = ''
        self.authenticated_proxy.ticket.update(
            ticket.number, comment, attributes, True)

    def create(self, summary, description):
        """
        Create a new trac ticket
        
        INPUT:
        
        - ``summary`` -- string. The summary (title) of the ticket
        
        - ``description`` -- string. The ticket description.

        OUTPUT:

        Integer. The newly-created trac ticket number.
        """
        return self.authenticated_proxy.ticket.create(summary, description)

    def search_branch(self, branch_name):
        """
        Return the trac ticket using the given (remote) branch
        
        INPUT:

        - ``branch_name`` -- string. The name of a remote branch on
          the trac git repo.
        
        OUTPUT:

        The ticket number as an integer. A ``ValueError`` is raised if
        no such ticket exists currently.

        EXAMPLES::

            sage: trac.search_branch('u/ohanar/build_system')
            14480
            sage: isinstance(_, int)
            True
        """
        branch = self.anonymous_proxy.search.branch(branch_name)
        if len(branch) == 0:
            raise ValueError('no such branch on a trac ticket')
        return branch[0][0]
    
