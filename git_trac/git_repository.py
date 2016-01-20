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
import textwrap

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

            sage: print(repo.untracked_files()[0])
            untracked_file
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

            sage: print(repo.current_branch())
            public/1002/anything
            sage: repo.git.silent.checkout('master')
            sage: print(repo.current_branch())
            master
            sage: repo.git.silent.checkout('public/1002/anything')    # undo change
        """
        # Does not work with git 1.7.9.5
        # return self.git.symbolic_ref('--short', 'HEAD').strip()
        branch = self.git.symbolic_ref('HEAD').strip()
        def lremove(string, substr):
            return string[len(substr):] if string.startswith(substr) else string
        branch = lremove(branch, 'refs/')
        branch = lremove(branch, 'heads/')
        return branch

    def has_branch(self, branch_name):
        """
        Test whether branch exists in the local repo

            sage: curr = repo.current_branch()
            sage: repo.has_branch(curr)
            True
            sage: repo.has_branch('ceci_n_est_pas_une_branche')
            False
        """
        rc = self.git.exit_code.rev_parse(branch_name, verify=True)
        return rc == 0
    
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
            sage: git.silent.checkout(branch)   # undo change
        """
        if self.git.exit_code.show_ref('refs/heads/' + local) == 0:
            print('Local branch already exists. Use "git trac pull" to get updates.')
            self.git.checkout(local)
            return
        remote_ref = 'remotes/trac/' + remote
        logger.debug('downloading branch %s', remote)
        self.git.fetch('trac', remote)
        self.git.branch(local, 'FETCH_HEAD')
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
            GitError: git returned with non-zero exit code (128) when executing "git branch --move branchB branchC"
                STDERR: fatal: A branch named 'branchC' already exists.
            sage: reset_repo()   # cleanup
        """
        self.git.branch(oldname, newname, move=True)

    def fetch(self, remote_branch):
        self.git.echo.fetch('trac', remote_branch)

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
        """
        Identify the release merges

        INPUT:

        - ``head`` -- commit whose history is considered

        - ``exclude`` -- commit whose history to exclude

        OUTPUT:

        The release merges (made by the release manager, leading to
        closed tickets). Output is a tuple of triples:

        * First, the commit of the release merge (made by the release
          manager)

        * Second, the tip commit of the ticket branch (made by the
          ticket author). This is the second parent of the release
          merge. Can be ``None`` if there is no code on the ticket.

        * Third, the ticket number as integer.
        """
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
            merge_commit = GitCommit(self, match.group('sha1'))
            parents  = merge_commit.get_parents()
            if len(parents) == 2:
                # Normal case
                ticket_commit = merge_commit.get_parents()[1]
            elif len(parents) == 1:
                # No code on ticket; slightly weird but ok
                ticket_commit = None
            else:
                assert False, 'can have at most two parents'
            result.append((merge_commit, ticket_commit, number))
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
        
        INPUT:
        
        - ``commit`` -- string containing the sha1 hash of a commit

        OUTPUT:

        Pair ``(merge, release)`` of
        :class:`git_trac.git_commit.GitCommit` instances. The first is
        the commit where the release manager merged (indicates the
        ticket number), the second is the oldest Sage release
        containing it (indicated when it was merged).

        Both can be ``None`` to indicate that the commit is not merged
        / not merged in a stable release.
        """
        merges = self.git.log('--reverse', '--format=%H%n%an <%ae>%n%s', '--ancestry-path', '-z',
                              #'--author='+RELEASE_MANAGER, 
                             'HEAD', '^'+str(commit))
        # iterate forward over the commits starting at the child of the given commit
        merge_commit = None
        release_commit = None
        for merge in merges.split('\0'):
            lines = merge.split('\n')
            if len(lines) != 3:
                logger.error('cannot parse log output: %s', merge)
                break
            else:
                sha1, author, title = lines
            if merge_commit is None and author == RELEASE_MANAGER:
                merge_commit = GitCommit(self, sha1, title=title)
                continue
            if merge_commit is not None and not title.startswith('Trac #'):
                release_commit = GitCommit(self, sha1, title=title)
                break
        return merge_commit, release_commit

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

    def try_in_detached_head(self, remote):
        """
        Try git branch in detached head with minimal recompiling
        """
        current = self.current_branch()
        print('Fetching most recent beta version...')
        self.git.fetch('trac', 'develop')
        self.git.checkout('--detach', 'FETCH_HEAD')
        print('Fetching remote branch {}...'.format(remote))
        try:
            self.git.fetch('trac', remote)
            self.git.merge('FETCH_HEAD')
        except GitError as e:
            self.git.checkout(current)
            raise e
        msg = """
        Merge of the most recent beta and the remote branch successful. When you are
        finished, switch back to one of the existing branches. For example:

            git checkout {0}
        """.format(current)
        print(textwrap.dedent(msg))

    def head_version(self):
        """
        Return the current version if the branch head is version-tagged.

        OUTPUT:

        String. The version tag. Raises a ``ValueError`` if the
        current branch head is not tagged.
        """
        tag = self.git.tag('-l', '--points-at', 'HEAD').splitlines()
        if len(tag) != 1:
            raise ValueError('branch head is not contained in single tag')
        return tag[0]

    def _tag_iter(self, skip=0):
        """
        Iterate over the tags in reverse chronological order from the current head.
        """
        log = self.git.log('--oneline', '--no-abbrev-commit', '--first-parent', 'HEAD')
        for line in log.splitlines():
            if skip > 0:
                skip -= 1
                continue
            sha1 = line[0:40]
            tag = self.git.tag('-l', '--points-at', sha1).splitlines()
            if len(tag) == 0:
                continue
            if len(tag) > 1:
                raise ValueError('multiple tags for commit ' + sha1)
            yield tag[0]
        raise ValueError('did not find a tagged version')

    def previous_stable_version(self):
        """
        Return the previous stable version.
        """
        for tag in self._tag_iter(skip=1):
            if any(substr in tag for substr in ['beta', 'rc']):
                continue
            return tag
        raise ValueError('did not find a stable version')

    def current_version(self):
        """
        Return the current version.
        """
        for tag in self._tag_iter():
            return tag
        raise ValueError('did not find a stable version')
