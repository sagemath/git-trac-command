"""
Run doctests as part of the unittests
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


import doctest
import sys
import os 
import logging
import re

try:
    from importlib import import_module
except ImportError:
    from git_trac.py26_compat import import_module

try:
    import unittest
except ImportError:
    import unittest2 as unittest


from git_trac.test.doctest_parser import SageDocTestParser, SageOutputChecker
from git_trac.test.builder import GitRepoBuilder
from git_trac.logger import logger


def sage_testmod(module, verbose=False, globs={}):
    """
    Run doctest with sage prompts
    """
    if isinstance(module, str):
        module = import_module(module)
    parser = SageDocTestParser(long=True, optional_tags=('sage',))
    finder = doctest.DocTestFinder(parser=parser)
    checker = SageOutputChecker()
    opts = doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS|doctest.IGNORE_EXCEPTION_DETAIL
    runner = doctest.DocTestRunner(checker=checker, optionflags=opts, verbose=verbose)
    for test in finder.find(module):
        test.globs.update(globs)
        rc = runner.run(test)
        if rc.failed:
            return False
    return True


class RemainingDoctests(GitRepoBuilder, unittest.TestCase):
    
    MODULE_FILENAME_RE = re.compile('^.*/[a-zA-Z0-9][a-zA-Z0-9_]*.py$')

    already_handled = (
        'git_trac.git_interface',
        'git_trac.git_commit', 
        'git_trac.git_repository',
        'git_trac.trac_server', 
        'git_trac.app', 
    )

    notest = (
        'git_trac.digest_transport',
        'git_trac.digest_transport_py2',
        'git_trac.test.doctest_parser',
    )

    @property
    def root_path(self):
        GIT_TRAC_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        return os.path.abspath(GIT_TRAC_DIR)

    def file_to_module(self, filename):
        """
        Convert filename to module name
        """
        cwd = self.root_path
        fqn = os.path.abspath(filename)
        assert fqn.startswith(cwd)
        fqn = fqn[len(cwd) : -len('.py')].lstrip(os.path.sep)
        module = fqn.replace(os.path.sep, '.')
        if module.endswith('.__init__'):
            module = module[:-len('.__init__')]
        return module

    def relative_path(self, filename):
        cwd = self.root_path
        fqn = os.path.abspath(filename)
        assert fqn.startswith(cwd)
        fqn = fqn[len(cwd):].lstrip(os.path.sep)
        return fqn

    def add_file(self, filename):
        return self.file_to_module(filename)

    def add_dir(self, *test_paths):
        modules = []
        for test_path in test_paths:
            for name in os.listdir(test_path):
                name = os.path.join(test_path, name)
                if os.path.isdir(name):
                    modules.extend(self.add_dir(name))
                elif self.MODULE_FILENAME_RE.match(name):
                    modules.append(self.add_file(name))
        return modules

    def is_py3(self):
        return sys.version_info[0] >= 3
    
    def find_modules(self):
        modules = self.add_dir(os.path.join(self.root_path, 'git_trac'))
        modules = set(modules).difference(self.already_handled + self.notest)
        return modules

    def test_finder(self):
        modules = self.find_modules()
        required = (
            'git_trac.trac_error',
            'git_trac.git_error',
            'git_trac.pretty_ticket',
            'git_trac.releasemgr.commit_message',
        )
        not_found = set(required).difference(modules)
        self.assertTrue(not_found == set())
        self.assertFalse(any(name in modules for name in self.already_handled))

    def test_remaining_doctests(self):
        for module in self.find_modules():
            rc = sage_testmod(module)
            self.assertTrue(rc)
    

class GitDebugDoctests(GitRepoBuilder, unittest.TestCase):

    def setUp(self):
        super(GitDoctests, self).setUp()
        import git_trac.git_interface
        git_trac.git_interface.DEBUG_PRINT = True

    def tearDown(self):
        import git_trac.git_interface
        git_trac.git_interface.DEBUG_PRINT = False
        super(GitDoctests, self).tearDown()


class GitDoctests(GitRepoBuilder, unittest.TestCase):

    def test_utils(self):
        repo = self.make_repo(verbose=False, user_email_set=True)
        globs = {'reset_repo': self.reset_repo, 'repo':repo, 'git':repo.git}
        rc = sage_testmod('git_trac.git_commit', globs=globs)
        self.assertTrue(rc)
        rc = sage_testmod('git_trac.git_repository', globs=globs)
        self.assertTrue(rc)
    

class TracDoctests(GitRepoBuilder, unittest.TestCase):

    def test_trac_model(self):
        globs = {'trac':self.make_trac()}
        rc = sage_testmod('git_trac.trac_server', globs=globs)
        self.assertTrue(rc)


class AppDoctests(GitRepoBuilder, unittest.TestCase):

    def test_app(self):
        from git_trac.app import Application
        app = Application()
        globs = {'app':app}
        rc = sage_testmod('git_trac.app', globs=globs)
        self.assertTrue(rc)



if __name__ == '__main__':
    unittest.main()

    
 
