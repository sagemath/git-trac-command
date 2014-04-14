"""
Git repository

This is a easy-to use frontend for the necessary git 
operations.
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

from .cached_property import cached_property
from .git_commit import GitCommit
from .git_error import GitError, DetachedHeadException
from .git_interface import GitInterface
from .people import RELEASE_MANAGER
from .logger import logger

SPLIT_RELEASE_LOG_RE = re.compile(
    '^(?P<sha1>[0-9a-f]{40}) Trac #(?P<ticket>[0-9]*): (?P<title>.*)')




class GitRepository(object):

    def __init__(self, verbose=False):
        self._verbose = verbose

    @cached_property
    def git(self):
        return GitInterface(verbose=self._verbose)

    @property
    def master(self):
        head = self.git.show_ref('master', head=True)
        return GitCommit(self, head[0:40])
    
    @property
    def head(self):
        head = self.git.show_ref('HEAD', head=True)
        return GitCommit(self, head[0:40])

    def untracked_files(self):
        r"""
        Return a list of file names for files that are not tracked by git and
        not ignored.

        EXAMPLES::

            sage: repo.untracked_files()
            ['untracked_file']
        """
        log = self.git.ls_files(others=True, exclude_standard=True, z=True)
        result = []
        for line in log.split('\0'):
            if line == '':  # two nulls is the end marker
                break
            result.append(line)
        return result

    def current_branch(self):
        """
        Return the current branch

        EXAMPLES::

            sage: repo.current_branch()
            'public/1002/anything'
        """
        # Does not work with git 1.7.9.5
        # return self.git.symbolic_ref('--short', 'HEAD').strip()
        branch = self.git.symbolic_ref('HEAD').strip()
        return branch.lstrip('refs/').lstrip('heads/')

    def checkout_new_branch(self, remote, local):
        """
        Check out branch.

        This modifies the git working tree.

        EXAMPLES::

            sage: git.silent.stash()
            sage: branch = repo.current_branch()
            sage: repo.checkout_new_branch('u/user/description', 'my/u/user/description')
            sage: '* my/u/user/description' in git.branch()
            True
        """
        remote_ref = 'remotes/trac/' + remote
        if self.git.exit_code.show_ref(remote_ref) != 0:
            logger.debug('downloading branch %s', remote)
            self.git.fetch('trac', remote)
            self.git.branch(local, 'FETCH_HEAD')
        else:
            print('Local branch already exists. Use "git trac pull" to get updates.')
        self.git.checkout(local)
        self.set_upstream(remote)

    def create(self, local, starting_branch='develop'):
        """
        Create new branch.
        """            
        self.git.fetch('trac', starting_branch)
        self.git.branch(local, 'FETCH_HEAD')
        self.git.checkout(local)

    def set_upstream(self, remote):
        # The following does not work if the refspec
        # (http://git-scm.com/book/en/Git-Internals-The-Refspec) does
        # not include the given remote branch. 
        #
        #    self.git.branch('--set-upstream-to', 'remotes/trac/{0}'.format(remote))
        #
        # Since we told people to setup trac with "-t master" the
        # refspec is just master. Instead, set it up manually:
        local = self.current_branch()
        self.git.config('branch.{0}.remote'.format(local), 'trac')
        self.git.config('branch.{0}.merge'.format(local), 'refs/heads/{0}'.format(remote))

    def rename_branch(self, oldname, newname):
        r"""
        Rename ``oldname`` to ``newname``.

        EXAMPLES:

        Create some branches::

            sage: repo.git.silent.branch('branchA')
            sage: repo.git.silent.branch('branchB')

        Rename some branches::

            sage: repo.rename_branch('branchA', 'branchC')
            sage: repo.rename_branch('branchB', 'branchC')
            Traceback (most recent call last):
            ...
            git_trac.git_error.GitError: git returned with 
            non-zero exit code (128) when executing "git branch --move branchB branchC"
                STDERR: fatal: A branch named 'branchC' already exists.
            sage: test.reset_repo()   # cleanup
        """
        self.git.branch(oldname, newname, move=True)

    def pull(self, remote_branch):
        self.git.echo.fetch('trac', remote_branch)
        self.git.echo.merge('FETCH_HEAD')

    def push(self, remote_branch, force=False):
        refspec = 'HEAD:refs/heads/'+remote_branch
        if force:
            self.git.echo.push('--force', 'trac', refspec)
        else:
            self.git.echo.push('trac', refspec)
        self.set_upstream(remote_branch)

    def release_merges(self, head, exclude):
        log = self.git.log('--oneline', '--no-abbrev-commit', '--first-parent', 
                           head, '^'+exclude, author=RELEASE_MANAGER)
        result = []
        for line in log.splitlines():
            match = SPLIT_RELEASE_LOG_RE.match(line.strip())
            if match is None:
                raise ValueError('parsing log failed at "{0}"'.format(line))
            number = match.group('ticket')
            try:
                number = int(number)
            except ValueError:
                raise ValueError('failed to convert ticket number to integer: "{0}"'.format(line))
            commit = GitCommit(self, match.group('sha1'))
            result.append((commit, number))
        return tuple(result)

    def find_release_merge_of_ticket(self, ticket_number):
        """
        Find the git commit that merged the given ticket

        See also :meth:`find_ticket`.
        """
        from .people import RELEASE_MANAGER
        log = self.git.log('--oneline', '--no-abbrev-commit', '--first-parent',
                           'HEAD', author=RELEASE_MANAGER)
        for line in log.splitlines():
            match = SPLIT_RELEASE_LOG_RE.match(line.strip())
            if match is None:
                raise ValueError('parsing log failed at "{0}"'.format(line))
            number = match.group('ticket')
            try:
                number = int(number)
            except ValueError:
                raise ValueError('failed to convert ticket number to integer: "{0}"'.format(line))
            if number == ticket_number:
                return GitCommit(self, match.group('sha1'))
        raise ValueError('release manager has not merged Trac #{0}'.format(ticket_number))
        
    def find_release_merge_of_commit(self, commit):
        """
        Find the nearest release merge in the future of commit.

        See also :meth:`find_release_merge_of_ticket.
        """
        merges = self.git.log('--reverse', '--format=oneline', '--ancestry-path',
                              '--author='+RELEASE_MANAGER, 
                             'HEAD', '^'+str(commit))
        if merges == '':
            raise ValueError('Commit {0} has not been released')
        oldest = merges.splitlines()[0]
        sha1 = oldest[0:40] 
        return GitCommit(self, sha1, title=oldest[41:])

    def review_diff(self, remote):
        """
        Create a list of changes to review
        """
        current = self.current_branch()
        try:
            print('Fetching remote branch...')
            self.git.fetch('trac', remote)
            self.git.checkout('--detach', 'FETCH_HEAD')
            print('Fetching most recent beta version...')
            self.git.fetch('trac', 'develop')
            self.git.merge('FETCH_HEAD')
            return self.git.diff('--minimal', '--color=always', 
                                 'FETCH_HEAD..HEAD')
        finally:
            self.git.checkout(current)
