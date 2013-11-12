"""
Exception classes for Git
"""

##############################################################################
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


class GitError(RuntimeError):
    r"""
    Error raised when git exits with a non-zero exit code.

    EXAMPLES::

        sage: from git_trac.git_error import GitError
        sage: raise GitError({'exit_code':128, 'stdout':'', 'stderr':'', 'cmd':'command'})
        Traceback (most recent call last):
        ...
        git_trac.git_error.GitError: git returned with 
        non-zero exit code (128) when executing "command"
    """
    def __init__(self, result, explain=None, advice=None):
        r"""
        Initialization.

        TESTS::

            sage: from git_trac.git_error import GitError
            sage: type(GitError({'exit_code':128, 'stdout':'', 'stderr':'', 'cmd':'command'}))
            <class 'git_trac.git_error.GitError'>
        """
        self.exit_code = result['exit_code']
        self.cmd = result['cmd'].strip()
        def prefix(string, prefix):
            return '\n'.join([prefix + ': ' + line.rstrip() for line in string.splitlines()])
        self.stdout = prefix(result['stdout'], '    STDOUT')
        self.stderr = prefix(result['stderr'], '    STDERR')
        self.explain = explain
        self.advice = advice
        template = 'git returned with non-zero exit code ({}) when executing "{}"'
        msg = template.format(self.exit_code, self.cmd)
        if len(self.stdout) != 0:
            msg += '\n' + self.stdout
        if len(self.stderr) != 0:
            msg += '\n' + self.stderr
        RuntimeError.__init__(self, msg)


class DetachedHeadException(RuntimeError):
    r"""
    Error raised when a git command can not be executed because the repository
    is in a detached HEAD state.

    EXAMPLES::

        sage: from git_trac.git_error import DetachedHeadException
        sage: raise DetachedHeadException()
        Traceback (most recent call last):
        ...
        git_trac.git_error.DetachedHeadException: unexpectedly, 
        git is in a detached HEAD state
    """
    def __init__(self):
        r"""
        Initialization.

        TESTS::

            sage: from git_trac.git_error import DetachedHeadException
            sage: type(DetachedHeadException())
            <class 'git_trac.git_error.DetachedHeadException'>
        """
        RuntimeError.__init__(self, "unexpectedly, git is in a detached HEAD state")


class InvalidStateError(RuntimeError):
    r"""
    Error raised when a git command can not be executed because the repository
    is not in a clean state.

    EXAMPLES::

        sage: from git_trac.git_error import InvalidStateError
        sage: raise InvalidStateError()
        Traceback (most recent call last):
        ...
        git_trac.git_error.InvalidStateError: unexpectedly, 
        git is in an unclean state
    """
    def __init__(self):
        r"""
        Initialization.

        TESTS::

            sage: from git_trac.git_error import InvalidStateError
            sage: type(InvalidStateError())
            <class 'git_trac.git_error.InvalidStateError'>
        """
        RuntimeError.__init__(self, "unexpectedly, git is in an unclean state")


class UserEmailException(RuntimeError):
    r"""
    Error raised if user/email is not set.

    This means that it is not advisable to make commits to the repository.

    EXAMPLES::

        sage: from git_trac.git_error import UserEmailException
        sage: raise UserEmailException()
        Traceback (most recent call last):
        ...
        git_trac.git_error.UserEmailException: user/email 
        is not configured, cannot make commits
    """
    def __init__(self):
        r"""
        Initialization.

        TESTS::

            sage: from git_trac.git_error import UserEmailException
            sage: type(UserEmailException())
            <class 'git_trac.git_error.UserEmailException'>
        """
        RuntimeError.__init__(self, "user/email is not configured, cannot make commits")

