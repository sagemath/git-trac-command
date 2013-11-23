"""
The Release Management App
"""

import os
import tempfile

from ..app import Application

RELEASE_MANAGER = 'Release Manager <release@sagemath.org>'



class ReleaseApplication(Application):

    def print_ticket(self, ticket_number):
        """
        INPUT:

        - ``ticket_number`` -- a trac ticket numebr.

        EXAMPLES:

        """
        ticket = self.trac.load(ticket_number)
        from .commit_message import format_ticket
        print(format_ticket(ticket))


    def merge(self, ticket_number, branch):
        """
        Create the "release" merge

        INPUT:

        - ``ticket_number`` -- integer or None. The ticket. If
          ``None`` it will be guessed from the ``branch``.

        - ``branch`` -- string or ``None``. The branch to merge. Can
          be either local or remote (in that order of preference). If
          ``None``, the trac ``Branch:`` field is looked up.
        """
        if ticket_number is None and Branch is None:
            raise ValueError('either ticket or branch must be specified')
        if ticket_number is None:
            ticket_number = self.trac.search_branch(branch)
        print('Loading ticket...')
        ticket = self.trac.load(ticket_number)
        if branch is None:
            branch = ticket.branch
        else:
            if branch != ticket.branch:
                raise ValueError('specified branch does not match ticket branch')
        branch = branch.strip()
        if len(branch) == 0:
            raise ValueError('no branch on ticket')
            
        print('URL: http://trac.sagemath.org/{0}'.format(ticket.number))
        print('Trac #{0}: {1}'.format(ticket.number, ticket.title))
        print('Branch {0}'.format(branch))

        from .commit_message import format_ticket
        commit_message = format_ticket(ticket)
        
        print('Fetching remote branch...')
        self.git.echo.fetch('trac', branch)

        print('Merging ticket...')
        self.git.echo.merge('FETCH_HEAD', '--no-ff', '--no-commit')

        status = self.git.status()
        if 'nothing to commit' in status:
            raise ValueError('already merged')
            
        if 'All conflicts fixed but you are still merging.' not in status:
            self.git.merge('--abort')
            raise ValueError('merge was not clean')

        try:
            fd, tmp = tempfile.mkstemp()
            os.close(fd)
            with open(tmp, 'w') as f:
                f.write(commit_message)
            self.git.echo.commit(file=tmp, author=RELEASE_MANAGER)
        finally:
            os.remove(tmp)
