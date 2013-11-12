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


import logging

from .cached_property import cached_property
from .git_commit import GitCommit
from .git_error import GitError, DetachedHeadException
from .git_interface import GitInterface



class GitRepository(object):

    def __init__(self, verbose=False):
        self._verbose = verbose

    @cached_property
    def git(self):
        return GitInterface(verbose=self._verbose)

    @property
    def master(self):
        return GitCommit(self, 'master')
    
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
        return self.git.symbolic_ref('--short', 'HEAD').strip()

    def checkout_branch(self, branch_name, ticket_number=None):
        """
        Check out branch.

        This modifies the git working tree.

        EXAMPLES::

            sage: git.silent.stash()
            sage: branch = repo.current_branch()
            sage: repo.checkout_branch('u/user/description')
            sage: '* u/user/description' in git.branch()
            True
            sage: repo.checkout_branch(branch)            
        """
        if self.git.exit_code.show_ref(branch_name) != 0:
            logging.debug('downloading branch %s', branch_name)
            self.git.fetch('trac', branch_name)
            self.git.branch(branch_name, 'FETCH_HEAD')
        self.git.checkout(branch_name)

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

