"""
The Release Management App
"""

import os
import tempfile

from ..app import Application

from ..people import RELEASE_MANAGER




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


    def _commit(self, commit_message, **kwds):
        try:
            fd, tmp = tempfile.mkstemp()
            os.close(fd)
            with open(tmp, 'w') as f:
                f.write(commit_message)
            self.git.echo.commit(file=tmp, author=RELEASE_MANAGER, **kwds)
        finally:
            os.remove(tmp)

    def merge(self, ticket_number, close=False, allow_empty=False):
        """
        Create the "release" merge

        INPUT:

        - ``ticket_number`` -- integer or None. The ticket. If
          ``None`` it will be guessed from the ``branch``.

        - ``close`` -- boolean. Whether to close the trac ticket.

        - ``allow_empty`` -- boolean. Whether to allow empty commits.
        """
        print('Loading ticket...')
        ticket = self.trac.load(ticket_number)
        branch = ticket.branch.strip()
        if len(branch) == 0:
            raise ValueError('no branch on ticket')
            
        print('URL: http://trac.sagemath.org/{0}'.format(ticket.number))
        print('Trac #{0}: {1}'.format(ticket.number, ticket.title))
        print('Branch {0}'.format(branch))
        print('Author(s): {0}'.format(ticket.author))
        print('Reviewer(s): {0}'.format(ticket.reviewer))
        
        import string
        if not all(author[0].strip() in string.ascii_uppercase 
                   for author in ticket.author.split(',')):
            raise ValueError('author {0} does not look right'.format(ticket.author))
        if not all(reviewer[0].strip() in string.ascii_uppercase 
                   for reviewer in ticket.reviewer.split(',')):
            raise ValueError('reviewer {0} does not look right'.format(ticket.reviewer))

        from .commit_message import format_ticket
        commit_message = format_ticket(ticket)
        
        print('Fetching remote branch...')
        self.git.echo.fetch('trac', branch)

        print('Merging ticket...')
        self.git.echo.merge('FETCH_HEAD', '--no-ff', '--no-commit')

        status = self.git.status()
        if 'nothing to commit' in status:
            if not allow_empty:
                raise ValueError('already merged')
            print('This is an empty commit')
            self._commit(commit_message, allow_empty=True)
        else:
            if 'All conflicts fixed but you are still merging.' not in status:
                self.git.merge('--abort')
                raise ValueError('merge was not clean')
            self._commit(commit_message)

        if close:
            self.close_ticket(ticket)

    def merge_multiple(self, ticket_numbers, close=False, allow_empty=False):
        for ticket_number in ticket_numbers:
            self.merge(ticket_number, close=close, allow_empty=allow_empty)

    def close_ticket(self, ticket):
        comment = ''
        attributes = {
            '_ts': ticket.timestamp,
            'status': 'closed',
            'resolution': 'fixed',
        }
        notify = True
        if len(ticket.commit) > 0:
            attributes['branch'] = ticket.commit
        return self.trac.authenticated_proxy.ticket.update(
            ticket.number, comment, attributes, notify)

    def close_tickets(self, head, exclude):
        ticket_list = self.repo.release_merges(head, exclude)
        for commit, ticket_number in ticket_list:
            ticket = self.trac.load(ticket_number)
            if ticket.status == 'closed':
                print('Trac #{0} already closed'.format(ticket_number))
            else:
                print('Trac #{0}: {1} -> closed'.format(ticket_number, ticket.status))
                self.close_ticket(ticket)
                
    def publish(self):
        tag = self.git.tag('-l', '--contains', 'HEAD').splitlines()
        if len(tag) != 1:
            raise ValueError('branch head is not contained in single tag')
        tag = tag[0]
        log_head = self.git.log('--oneline', '--no-abbrev-commit', '-1', 'HEAD')
        log_tag  = self.git.log('--oneline', '--no-abbrev-commit', '-1', tag)
        if log_head != log_tag:
            raise ValueError('branch head is not tagged')
        self.git.push('--tags', 'trac', 'develop')
