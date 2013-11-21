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

import re

from .config import Config
from .git_repository import GitRepository
from .trac_server import TracServer

TICKET_NUMBER_IN_BRANCH_REGEX = re.compile('[-_/]([0-9]+)[-_/]')


class Application(object):

    def __init__(self):
        self.repo = GitRepository()
        self.git = git = self.repo.git
        self.config = c = Config(git)
        self.trac = TracServer(c)

    def search(self, branch=None):
        if branch is None:
            branch = self.repo.current_branch()
        result = self.trac.search_branch(branch)
        print(result)

    def pull(self, ticket_number):
        remote = self.trac.remote_branch(ticket_number)
        print('remote branch: '+remote)
        self.repo.pull(remote)

    def suggest_remote_branch(self, template):
        """
        Return a remote branch name

        INPUT:

        - ``template`` -- string. A valid git branch name.

        OUTPUT:

        A remote branch name where you have write permissions. As
        close as possible to ``template``.

        EXAMPLES::

            sage: app.suggest_remote_branch('public/foo/bar')        
            'public/foo/bar'
            sage: app.suggest_remote_branch('u/some_user/foo/bar')        
            'u/trac_user/foo/bar'
            sage: app.suggest_remote_branch('foo/bar')        
            'u/trac_user/foo/bar'
        """
        if template.startswith('public/'):
            return template
        name = self.config.username
        if template.startswith('u/' + name):
            return template
        if template.startswith('u/'):
            parts = template.split('/', 2)
            if len(parts) == 3:
                return '/'.join(['u', name, parts[2]])
        return '/'.join(['u', name, template])

    def push(self, ticket_number):
        try:
            remote = self.trac.remote_branch(ticket_number)
        except ValueError:  # no remote branch yet
            remote = self.repo.current_branch()
        remote = self.suggest_remote_branch(remote)
        print('remote branch: '+remote)
        self.repo.push(remote)

    def guess_ticket_number(self, ticket):
        """
        Guess the ticket number

        INPUT:

        - ``ticket`` -- anything (user input from the command line)

        OUTPUT:

        An integer. If no guess is available, a ``ValueError`` is
        returned.

        EXAMPLES::
        
            sage: app.repo.current_branch()
            'public/1002/anything'
            sage: app.guess_ticket_number(None)
            1002
            sage: app.guess_ticket_number(12345)
            12345
            sage: app.guess_ticket_number('u/user/1001/1_foo')
            1001
            sage: app.guess_ticket_number('u/user/description')
            Traceback (most recent call last):
            ...
            ValueError: could not deduce ticket number from 
            branch name "u/user/description"
        """
        try:
            return int(ticket)
        except (ValueError, TypeError):
            pass
        branch = None
        if ticket is not None:
            ticket = str(ticket)
            if len(ticket) > 0:
                branch = ticket
        if branch is None:
            branch = self.repo.current_branch()
        try:
            return self.trac.search_branch(branch)
        except ValueError:
            pass
        match = TICKET_NUMBER_IN_BRANCH_REGEX.search(branch)
        if match:
            return int(match.groups()[0])
        raise ValueError('could not deduce ticket number from branch'
                         ' name "{0}"'.format(branch))

    def save_trac_username(self, username):
        self.config.username = username

    def save_trac_password(self, password):
        self.config.password = password
        
    def print_config(self, ssh_keys=True):
        """
        Print configuration information

        EXAMPLES::

            sage: app.print_config(False)
            Trac xmlrpc URL:
                https://trac.sagemath.org/xmlrpc (anonymous)
                https://trac.sagemath.org/login/xmlrpc (authenticated)
            Username: trac_user
            Password: trac_pass
        """
        c = self.config
        print('Trac xmlrpc URL:')
        print('    {0} (anonymous)'.format(self.trac.url_anonymous))
        print('    {0} (authenticated)'.format(self.trac.url_authenticated))
        print('    realm {0}'.format(c.server_realm))
        print('Username: {0}'.format(c.username))
        print('Password: {0}'.format(c.password))
        if ssh_keys:
            print('Retrieving SSH keys...')
            for key in self.trac.get_ssh_fingerprints():
                print('    {0}'.format(key))

    def print_ticket(self, ticket_number):
        """
        INPUT:

        - ``ticket_number`` -- integer.

        EXAMPLES:

            sage: app.print_ticket(1000)
            ==============================================================================
            Trac #1000: Sage does not have 10000 users yet.
            <BLANKLINE>            
            ADD DESCRIPTION
            Status: closed                          Component: distribution
            Last modified: 2013-10-05 21:16:12      Created: 2007-10-25 16:48:05 UTC
            Report upstream: N/A
            Authors:
            Reviewers:
            Branch:
            Keywords:
            Dependencies:
            ------------------------------------------------------------------------------
            Comment #1 by was at 2007-10-25 16:50:15 UTC:
            [Owner] changed from mabshoff to was
            ------------------------------------------------------------------------------
            Comment #2 by was at 2007-10-25 16:50:38 UTC:
            [Status] changed from new to assigned
            ------------------------------------------------------------------------------
            Comment #3 by was at 2007-10-25 16:52:37 UTC:
            [Milestone] set to sage-wishlist
            ------------------------------------------------------------------------------
            Comment #4 by was at 2007-12-10 17:29:52 UTC:
            We've made major progress toward this ticket so far with:
            <BLANKLINE>
            http://science.slashdot.org/article.pl?sid=07/12/08/1350258
            <BLANKLINE>
            We had nearly 5000 downloads this weekend.
            ------------------------------------------------------------------------------
            Comment #5 by was at 2008-01-09 06:16:42 UTC:
            I think we have 10000 users now based on downloads, etc.
            [Resolution] set to fixed
            [Status] changed from assigned to closed
            ------------------------------------------------------------------------------
            Comment #6 by mabshoff at 2008-01-10 08:28:40 UTC:
            [Milestone] changed from sage-wishlist to sage-2.10
            ------------------------------------------------------------------------------
            Comment #7 by saraedum at 2013-07-25 14:50:51 UTC:
            [Description] modified
            ------------------------------------------------------------------------------
            Comment #8 by vbraun at 2013-10-04 21:47:15 UTC:
            [Changetime] changed from 20130725T14:50:51 to 20130725T14:50:51
            [Description] modified
            ------------------------------------------------------------------------------
            Comment #9 by was at 2013-10-05 20:41:33 UTC:
            I made this ticket in the first place, so I'm going to make it meaningful by
            defining "number of users" to be "the number of unique *returning* visitors to
            sagemath.org per month".   It's a well-defined quantity, and it's not just
            some sort of pure vanity metric, because to count, a user has to visit the
            site more than once (so temporary spikes due to news don't count).  The data
            from google analytics shows that sage has stayed above 10,000 users -- by that
            metric -- every month for the last year.   However, just barely! There were
            only 11,530 unique returning visitors in July, 2013.
            <BLANKLINE>            
            For the record, the number of unique returning visitors per month for
            sagenb.org is between 3500 and 8000 over this same period.
            <BLANKLINE>            
            For https://cloud.sagemath.com, it's between 0 and 2856.
            <BLANKLINE>            
            (I hope having a description doesn't mess up the dev scripts!)
            [Report Upstream] set to N/A
            ------------------------------------------------------------------------------
            Comment #10 by vbraun at 2013-10-05 20:57:50 UTC:
            This ticket is used in the docs for the dev scripts, apologies for spamming...
            (under normal use the doctests of course do not modify trac tickets)
            ------------------------------------------------------------------------------
            URL: http://trac.sagemath.org/1000
            ==============================================================================
        """
        ticket = self.trac.load(ticket_number)
        from .pretty_ticket import format_ticket
        print(format_ticket(ticket))
