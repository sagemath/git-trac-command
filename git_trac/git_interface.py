## -*- encoding: utf-8 -*-
r"""
Git Interface

This module provides a python interface to git. Essentially, it is
a raw wrapper around calls to git and retuns the output as strings.

EXAMPLES::

    sage: git.execute('status', porcelain=True)
    DEBUG cmd: git status --porcelain
    DEBUG stdout:  M foo4.txt
    DEBUG stdout: A  staged_file
    DEBUG stdout: ?? untracked_file
    ' M foo4.txt\nA  staged_file\n?? untracked_file\n'

    sage: git.status(porcelain=True)
    DEBUG cmd: git status --porcelain
    DEBUG stdout:  M foo4.txt
    DEBUG stdout: A  staged_file
    DEBUG stdout: ?? untracked_file
    ' M foo4.txt\nA  staged_file\n?? untracked_file\n'
"""

##############################################################################
#  The "git trac ..." command extension for git
#  Copyright (C) 2013  Volker Braun <vbraun.name@gmail.com>
#                      David Roe <roed.math@gmail.com>
#                      Julian Rueth <julian.rueth@fsfe.org>
#                      Keshav Kini <keshav.kini@gmail.com>
#                      Nicolas M. Thiery <Nicolas.Thiery@u-psud.fr>
#                      Robert Bradshaw <robertwb@gmail.com>
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
import subprocess

from .cached_property import cached_property
from .git_error import GitError, DetachedHeadException, UserEmailException
from .logger import logger


# Modified for doctesting
DEBUG_PRINT = False


class GitInterfaceSilentProxy(object):
    """
    Execute a git command silently, discarding the output.
    """
    def __init__(self, actual_interface):
        self._interface = actual_interface

    def execute(self, *args, **kwds):
        self._interface.execute(*args, **kwds)
        return None  # the "silent" part


class GitInterfaceExitCodeProxy(object):
    """
    Execute a git command silently, return only the exit code.
    """
    def __init__(self, actual_interface):
        self._interface = actual_interface

    def execute(self, cmd, *args, **kwds):
        result = self._interface._run(cmd, args, kwds, 
                                      popen_stdout=subprocess.PIPE, 
                                      popen_stderr=subprocess.PIPE,
                                      exit_code_to_exception=False)
        return result['exit_code']


class GitInterfacePrintProxy(object):
    """
    Execute a git command and print to stdout like the commandline client.
    """
    def __init__(self, actual_interface):
        self._interface = actual_interface

    def execute(self, cmd, *args, **kwds):
        result = self._interface._run(cmd, args, kwds, 
                                      popen_stdout=subprocess.PIPE, 
                                      popen_stderr=subprocess.PIPE)
        print(result['stdout'])
        if result['stderr']:
            WARNING = '\033[93m'
            RESET = '\033[0m'
            print(WARNING+result['stderr']+RESET)
        return None




class GitInterface(object):
    r"""
    A wrapper around the ``git`` command line tool.

    Most methods of this class correspond to actual git commands. Some add
    functionality which is not directly available in git. However, all of the
    methods should be non-interactive. If interaction is required the method
    should live in :class:`saged.dev.sagedev.SageDev`.

    EXAMPLES::

        sage: git
        Interface to git repo
    """

    # commands that cannot change the repository even with
    # some crazy flags set - these commands should be safe
    _safe_commands = (
        'config',    'diff',   'grep',       'log', 
        'ls_remote', 'remote', 'reset',      'show', 
        'show_ref',  'status', 'symbolic_ref', 
        'rev_parse', 
    )
        
    _unsafe_commands = (
        'add',          'am',       'apply',       'bisect',
        'branch',       'checkout', 'cherry_pick', 'clean',
        'clone',        'commit',   'fetch',       'for_each_ref',
        'format_patch', 'init',     'ls_files',    'merge',
        'mv',           'pull',     'push',        'rebase',
        'rev_list',     'rm',       'stash',       'tag'
    )

    def __init__(self, verbose=False, git_cmd=None):
        self._verbose = verbose
        self._git_cmd = 'git' if git_cmd is None else git_cmd
        self._user_email_set = False
        self.silent = GitInterfaceSilentProxy(self)
        self.exit_code = GitInterfaceExitCodeProxy(self)
        self.echo = GitInterfacePrintProxy(self)

    @property
    def git_cmd(self):
        """
        The git executable
        
        EXAMPLES::

            sage: git.git_cmd
            'git'
        """
        return self._git_cmd

    def __repr__(self):
        r"""
        Return a printable representation of this object.
        
        TESTS::

            sage: repr(git)
            'Interface to git repo'
        """
        return 'Interface to git repo'

    def _log(self, prefix, log):
        for line in log.splitlines():
            logger.debug('%s = %s', prefix, line)
            if DEBUG_PRINT:
                print('DEBUG {0}: {1}'.format(prefix, line))

    def _run_unsafe(self, cmd, args, kwds={}, popen_stdout=None, popen_stderr=None):
        r"""
        Run git

        INPUT:

        - ``cmd`` -- git command run

        - ``args`` -- extra arguments for git

        - ``kwds`` -- extra keywords for git

        - ``popen_stdout`` -- Popen-like keywords.

        - ``popen_stderr`` -- Popen-like keywords.
        
        OUTPUT:

        A dictionary with keys ``exit_code``, ``stdout``, ``stderr``, ``cmd``.

        .. WARNING::

            This method does not raise an exception if the git call returns a
            non-zero exit code.

        EXAMPLES::

            sage: import subprocess
            sage: result = git._run('status', (), {}, popen_stdout=subprocess.PIPE)
            DEBUG cmd: git status
            DEBUG stdout: # On branch public/1002/anything
            DEBUG stdout: # Changes to be committed:
            DEBUG stdout: #   (use "git reset HEAD <file>..." to unstage)
            DEBUG stdout: #
            DEBUG stdout: #     new file:   staged_file
            DEBUG stdout: #
            DEBUG stdout: # Changes not staged for commit:
            DEBUG stdout: #   (use "git add <file>..." to update what will be committed)
            DEBUG stdout: #   (use "git checkout -- <file>..." to discard changes in working directory)
            DEBUG stdout: #
            DEBUG stdout: #     modified:   foo4.txt
            DEBUG stdout: #
            DEBUG stdout: # Untracked files:
            DEBUG stdout: #   (use "git add <file>..." to include in what will be committed)
            DEBUG stdout: #
            DEBUG stdout: #     untracked_file
            sage: result == \
            ....:     {'exit_code': 0, 'stdout': '# On branch public/1002/anything\n# Changes to be committed:\n#   (use "git reset HEAD <file>..." to unstage)\n#\n#\tnew file:   staged_file\n#\n# Changes not staged for commit:\n#   (use "git add <file>..." to update what will be committed)\n#   (use "git checkout -- <file>..." to discard changes in working directory)\n#\n#\tmodified:   foo4.txt\n#\n# Untracked files:\n#   (use "git add <file>..." to include in what will be committed)\n#\n#\tuntracked_file\n', 'cmd': 'git status', 'stderr': None}
            True
        """ 
        env = kwds.pop('env', {})
        s = [self.git_cmd, cmd]
        for k, v in kwds.items():
            if len(k) == 1:
                k = '-' + k
            else:
                k = '--' + k.replace('_', '-')
            if v is True:
                s.append(k)
            elif v is not False:
                s.append(k+'='+str(v))
        if args:
            s.extend(a for a in args if a is not None)
        s = [str(arg) for arg in s]
        complete_cmd = ' '.join(s)
        self._log('cmd', complete_cmd)

        env.update(os.environ)
        process = subprocess.Popen(s, stdout=popen_stdout, stderr=popen_stderr, env=env)
        stdout, stderr = process.communicate()
        retcode = process.poll()
        if stdout is not None and popen_stdout is subprocess.PIPE:
            stdout = stdout.decode('utf-8')
            self._log('stdout', stdout)
        if stderr is not None and popen_stderr is subprocess.PIPE:
            stderr = stderr.decode('utf-8')
            self._log('stderr', stderr)
        return {'exit_code':retcode, 'stdout':stdout, 'stderr':stderr, 'cmd':complete_cmd}

    def _run(self, cmd, args, kwds={}, popen_stdout=None, popen_stderr=None, exit_code_to_exception=True):
        result = self._run_unsafe(cmd, args, kwds,
                                  popen_stdout=popen_stdout,
                                  popen_stderr=popen_stderr)
        if exit_code_to_exception and result['exit_code']:
            raise GitError(result)
        return result

    def execute(self, cmd, *args, **kwds):
        r"""
        Run git on a command given by a string.

        Raises an exception if git has non-zero exit code.

        INPUT:

        - ``cmd`` -- string. The git command to run

        - ``*args`` -- list of strings. Extra arguments for git.

        - ``**kwds`` -- keyword arguments. Extra keywords for git. Will be rewritten 
          such that ``foo='bar'`` becomes the git commandline argument ``--foo='bar'``. 
          As a special case, ``foo=True`` becomes just ``--foo``.

        EXAMPLES::

            sage: git.execute('status')
            DEBUG cmd: git status
            DEBUG stdout: # On branch public/1002/anything
            DEBUG stdout: # Changes to be committed:
            DEBUG stdout: #   (use "git reset HEAD <file>..." to unstage)
            DEBUG stdout: #
            DEBUG stdout: #	new file:   staged_file
            DEBUG stdout: #
            DEBUG stdout: # Changes not staged for commit:
            DEBUG stdout: #   (use "git add <file>..." to update what will be committed)
            DEBUG stdout: #   (use "git checkout -- <file>..." to discard changes in working directory)
            DEBUG stdout: #
            DEBUG stdout: #	modified:   foo4.txt
            DEBUG stdout: #
            DEBUG stdout: # Untracked files:
            DEBUG stdout: #   (use "git add <file>..." to include in what will be committed)
            DEBUG stdout: #
            DEBUG stdout: #	untracked_file
            '# On branch public/1002/anything\n# Changes to be committed:\n#   (use "git reset HEAD <file>..." to unstage)\n#\n#\tnew file:   staged_file\n#\n# Changes not staged for commit:\n#   (use "git add <file>..." to update what will be committed)\n#   (use "git checkout -- <file>..." to discard changes in working directory)\n#\n#\tmodified:   foo4.txt\n#\n# Untracked files:\n#   (use "git add <file>..." to include in what will be committed)\n#\n#\tuntracked_file\n'

            sage: git.execute('status', foo=True) # --foo is not a valid parameter
            Traceback (most recent call last):
            ...
            git_trac.git_error.GitError: git returned with non-zero exit code (129) 
            when executing "git status --foo"
                STDERR: error: unknown option `foo'
                STDERR: usage: git status [options] [--] <pathspec>...
                STDERR: 
                STDERR:     -v, --verbose         be verbose
                STDERR:     -s, --short           show status concisely
                STDERR:     -b, --branch          show branch information
                STDERR:     --porcelain           machine-readable output
                STDERR:     --long                show status in long format (default)
                STDERR:     -z, --null            terminate entries with NUL
                STDERR:     -u, --untracked-files[=<mode>]
                STDERR:                           show untracked files, optional modes: all, normal, no. (Default: all)
                STDERR:     --ignored             show ignored files
                STDERR:     --ignore-submodules[=<when>]
                STDERR:                           ignore changes to submodules, optional when: all, dirty, untracked. (Default: all)
                STDERR:     --column[=<style>]    list untracked files in columns
                STDERR: 
        """
        result = self._run(cmd, args, kwds,
                           popen_stdout=subprocess.PIPE,
                           popen_stderr=subprocess.PIPE)
        return result['stdout']

    __call__ = execute



def create_wrapper(git_cmd_underscore):
    r"""
    Create a wrapper for ``git_cmd_underscore``.
    """
    git_cmd = git_cmd_underscore.replace('_', '-')
    def meth(self, *args, **kwds):
        return self.execute(git_cmd, *args, **kwds)
    meth.__doc__ = r"""
    Call `git {0}`.

    OUTPUT:

    See :meth:`execute` for more information.

    EXAMPLES:

        sage: git.{1}() # not tested
    """.format(git_cmd, git_cmd_underscore)
    return meth



for command in GitInterface._safe_commands + GitInterface._unsafe_commands:
    setattr(GitInterface, command, create_wrapper(command))
    setattr(GitInterfaceSilentProxy, command, create_wrapper(command))
    setattr(GitInterfaceExitCodeProxy, command, create_wrapper(command))
    setattr(GitInterfacePrintProxy, command, create_wrapper(command))
