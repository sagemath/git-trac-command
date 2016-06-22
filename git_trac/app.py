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

import sys
import re

from .config import Config
from .git_repository import GitRepository
from .trac_server import TracServer

TICKET_NUMBER_IN_BRANCH_REGEX = re.compile('[-_/]([0-9]{2,})([-_/]|$)')
TICKET_WITH_NUMBER_REGEX = re.compile('^t(icket)?/(?P<number>\d+)/(?P<name>.*)$')


def title_to_branch_name(title):
    """
    Convert a human-readable summary/title into a valid branch name
    """
    return re.sub('[^a-zA-Z0-9]', '_', title.lower().strip())


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

    def fetch(self, ticket_or_branch=None):
        try:
            ticket_number = self.guess_ticket_number(ticket_or_branch)
        except ValueError:
            # Some more DWIM
            if ticket_or_branch is not None:
                # allow "git trac fetch u/user/description" even if not on a ticket
                # allow "git trac fetch develop" which should never be on a ticket
                self.repo.fetch(str(ticket_or_branch))
            else:
                # Finally, just try "git pull"
                self.git.fetch()
            return
        remote = self.trac.remote_branch(ticket_number)
        print('remote branch: '+remote)
        self.repo.fetch(remote)

    def pull(self, ticket_or_branch=None):
        try:
            ticket_number = self.guess_ticket_number(ticket_or_branch)
        except ValueError:
            # Some more DWIM
            if ticket_or_branch is not None:
                # allow "git trac pull u/user/description" even if not on a ticket
                # allow "git trac pull develop" which should never be on a ticket
                self.repo.pull(str(ticket_or_branch))
            else:
                # Finally, just try "git pull"
                self.git.pull()
            return
        remote = self.trac.remote_branch(ticket_number)
        print('remote branch: '+remote)
        self.repo.pull(remote)

    def suggest_local_branch(self, ticket_number, remote_branch):
        """
        Return a local branch name 

        EXAMPLES::

            sage: print(app.suggest_local_branch(123, 'public/foo/bar'))
            t/123/public/foo/bar
            sage: print(app.suggest_local_branch(123, 'u/some_user/foo/bar'))      
            t/123/foo/bar
            sage: print(app.suggest_local_branch(123, 'foo/bar'))
            t/123/foo/bar
            sage: print(app.suggest_local_branch(123, 'master'))
            t/123/master
        """
        if remote_branch.startswith('u/'):
            parts = remote_branch.split('/', 2)
            if len(parts) == 3:
                remote_branch = parts[2]
        return 't/{0}/{1}'.format(ticket_number, remote_branch)

    def checkout(self, ticket_or_branch, branch_name=None):
        if ticket_or_branch.is_number():
            self._checkout_ticket(int(ticket_or_branch), branch_name)
        else:
            branch = str(ticket_or_branch)
            self.repo.checkout_new_branch(branch, branch)
            
    def _checkout_ticket(self, ticket_number, branch_name=None):
        print('Loading ticket #{0}...'.format(ticket_number))
        ticket = self.trac.load(ticket_number)
        if len(ticket.branch) == 0:
            # No branch attached to the trac ticket, creating new one
            branch_name = title_to_branch_name(ticket.title)
            remote = self.suggest_remote_branch(branch_name)
            local = self.suggest_local_branch(ticket_number, remote)
            if self.repo.has_branch(local):
                print('Local branch: {0}'.format(local))
                self.repo.checkout_new_branch(remote, local)
            else:
                print('Newly created local branch: {0}'.format(local))
                self.repo.create(local)
            return
        if branch_name is None:
            branch = self.suggest_local_branch(ticket_number, ticket.branch)
        else:
            branch = branch_name.strip()
            if len(branch) == 0:
                raise ValueError('no local branch specified')
        print('Checking out Trac #{0} remote branch {1} -> local branch {2}...'
              .format(ticket_number, ticket.branch, branch))
        self.repo.checkout_new_branch(ticket.branch, branch)

    def tryout(self, ticket_or_branch):
        if ticket_or_branch.is_number():
            branch = self.trac.remote_branch(ticket_or_branch)
        else:
            branch = str(ticket_or_branch)
        self.repo.try_in_detached_head(branch)

    def suggest_remote_branch(self, template):
        """
        Return a remote branch name

        INPUT:

        - ``template`` -- string. A valid git branch name.

        OUTPUT:

        A remote branch name where you have write permissions. As
        close as possible to ``template``.

        EXAMPLES::
 
            sage: print(app.suggest_remote_branch('public/foo/bar'))
            public/foo/bar
            sage: print(app.suggest_remote_branch('u/some_user/foo/bar'))      
            u/trac_user/foo/bar
            sage: print(app.suggest_remote_branch('foo/bar'))
            u/trac_user/foo/bar
            sage: print(app.suggest_remote_branch('master'))
            u/trac_user/master
            sage: print(app.suggest_remote_branch('article-fsm-in-sage'))
            u/trac_user/article-fsm-in-sage

        Remove ``'ticket/<number>/'`` or ``'t/<number>/'`` if necessary::

            sage: print(app.suggest_remote_branch('ticket/123'))
            u/trac_user/ticket/123
            sage: print(app.suggest_remote_branch('ticket/123/public/foo/bar'))
            public/foo/bar
            sage: print(app.suggest_remote_branch('ticket/123/u/some_user/foo/bar'))
            u/trac_user/foo/bar
            sage: print(app.suggest_remote_branch('ticket/123/foo/bar'))
            u/trac_user/foo/bar
            sage: print(app.suggest_remote_branch('t/123/foo/bar'))
            u/trac_user/foo/bar
        """
        m = TICKET_WITH_NUMBER_REGEX.match(template)
        if m is not None:
            template = m.group('name')
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

    def push(self, ticket_number, remote=None, force=False):
        if remote is not None:
            print('Specified remote branch: '+remote)
        else:
            try:
                remote = self.trac.remote_branch(ticket_number)
            except ValueError:  # no remote branch yet
                remote = self.repo.current_branch()
            remote = self.suggest_remote_branch(remote)
            print('Guessed remote branch: '+remote)
        self.repo.push(remote, force)
        ticket = self.trac.load(ticket_number)
        must_set_branch = (ticket.branch != remote)
        if must_set_branch:
            print('Changing the trac "Branch:" field...')
            self.trac.set_remote_branch(ticket, remote)

    def create(self, summary, branch_name=None):
        if summary.lower() == 'help':
            # Common confusion, see https://trac.sagemath.org/ticket/17813
            print('Use "git trac create -h" for the online help.')
            sys.exit(0)
        if branch_name is None:
            branch_name = title_to_branch_name(summary)
        remote = self.suggest_remote_branch(branch_name)
        print('Remote branch: {0}'.format(remote))
        ticket_number = self.trac.create(summary, '')
        print('Newly-created ticket number: {0}'.format(ticket_number))
        print('Ticket URL: https://trac.sagemath.org/{0}'.format(ticket_number))
        local = self.suggest_local_branch(ticket_number, remote)
        print('Local branch: {0}'.format(local))
        self.repo.create(local)

    def guess_ticket_number(self, ticket):
        """
        Guess the ticket number

        INPUT:

        - ``ticket`` -- anything (user input from the command line)

        OUTPUT:

        An integer. If no guess is available, a ``ValueError`` is
        returned.

        EXAMPLES::
        
            sage: print(app.repo.current_branch())
            public/1002/anything
            sage: app.guess_ticket_number(None)
            1002
            sage: app.guess_ticket_number(12345)
            12345
            sage: app.guess_ticket_number('u/user/1001/1_foo')
            1001
            sage: app.guess_ticket_number('ticket/14102')
            14102
            sage: app.guess_ticket_number('ticket/22-vla-les-flics')
            22

        There is no open one digit ticket on trac. So 14102 is the correct answer::

            sage: app.guess_ticket_number('ticket/blahv-2-foo-14102-blob')
            14102
            sage: app.guess_ticket_number('u/user/description')
            Traceback (most recent call last):
            ...
            ValueError: could not deduce ticket number from
            branch name "u/user/description"
            sage: app.guess_ticket_number('u/user/1-foo')
            Traceback (most recent call last):
            ...
            ValueError: could not deduce ticket number from
            branch name "u/user/1-foo"

        The ticket number needs to be delimited by ``-`` or ``/``::

            sage: app.guess_ticket_number('u/user/foo23')
            Traceback (most recent call last):
            ...
            ValueError: could not deduce ticket number from
            branch name "u/user/foo23"
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
        print('Saved trac username.')

    def save_trac_password(self, password):
        self.config.password = password
        print('Saved trac password.')

    def print_config(self, ssh_keys=True):
        """
        Print configuration information

        EXAMPLES::

            sage: app.print_config(False)
            Trac xmlrpc URL:
                https://trac.sagemath.org/xmlrpc (anonymous)
                https://trac.sagemath.org/login/xmlrpc (authenticated)
                realm sage.math.washington.edu
            Username: trac_user
            Password: trac_pass
        """
        from git_trac.config import AuthenticationError
        c = self.config
        print('Trac xmlrpc URL:')
        print('    {0} (anonymous)'.format(self.trac.url_anonymous))
        print('    {0} (authenticated)'.format(self.trac.url_authenticated))
        print('    realm {0}'.format(c.server_realm))
        try:
            c.username
            anonymous_only = False
        except AuthenticationError:
            anonymous_only = True

        if anonymous_only:
            print('Anonymous (read) access only. To configure an account, use:')
            print('    git trac config --user=<name> --pass=<password>')
        else:
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
            URL: https://trac.sagemath.org/1000
            ==============================================================================
        """
        ticket = self.trac.load(ticket_number)
        from .pretty_ticket import format_ticket
        print(format_ticket(ticket))

    def log(self, ticket_number, oneline=False):
        commit = self.repo.find_release_merge_of_ticket(ticket_number)
        print('History of {0}'.format(commit.title))
        # by convention, the first ancestor (sha1^) is the previous release merge
        args = ['--color=always', commit.sha1, '^'+commit.sha1+'^']
        if oneline:
            args = ['--oneline'] + args
        print(args)
        self.git.echo.log(*args)

    def find(self, commit):
        merge, release = self.repo.find_release_merge_of_commit(commit)
        if release is not None:
            version = re.sub('^Updated Sage version to ', '', release.title)
            print('Commit has been merged in {0}.'.format(version))
            assert merge is not None
        elif merge is not None:
            # only the release manager should ever see this
            print('Commit has been merged, but not into a released version.')
        else:
            print('Commit has not been merged by the release manager into your current branch.')
            return
        self.git.echo.show(merge.sha1, '--color=always')

    def review_diff(self, ticket_number):
        remote = self.trac.remote_branch(ticket_number)
        diff = self.repo.review_diff(remote)
        print(diff)

    def add_remote(self):
        """
        Add the "trac" remotes (RW+RO) if necessary
        """
        REPO_RW = 'git@trac.sagemath.org:sage.git'
        REPO_RO = 'git://trac.sagemath.org/sage.git'
        remotes = self.git.remote().split()
        if 'trac' in remotes:
            cmd = 'set-url'
        else:
            cmd = 'add'
        self.git.remote(cmd, 'trac', REPO_RO)
        self.git.remote('set-url', '--push', 'trac', REPO_RW)

    def print_dependencies(self, ticket_number):
        """
        Print the trac dependencies

        INPUT:

        - ``ticket_number`` -- integer.

        EXAMPLES:

            sage: app.print_dependencies(16461)
            Dependencies: #16464, #16391
            * release manager has not merged Trac #16464
            * release manager has not merged Trac #16391
        """
        ticket = self.trac.load(ticket_number)
        if not ticket.dependencies.strip():
            print('No dependencies')
            return
        print('Dependencies: {0}'.format(ticket.dependencies))
        for dep in ticket.dependencies.split(','):
            try:
                dep_number = int(dep.lstrip(' #').rstrip())
            except ValueError:
                print('* invalid dependency "{0}"'.format(dep))
                continue
            try:
                commit = self.repo.find_release_merge_of_ticket(dep_number)
            except ValueError as err:
                print('* ' + str(err))
                continue
            print('* dependency {0} merged in {1}'.format(dep, commit))
