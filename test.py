#!/usr/bin/env python3

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
import importlib

sys.path.append(os.getcwd())

from git_trac.doctest_parser import SageDocTestParser, SageOutputChecker

def testmod(module, verbose=False, globs={}):
    if isinstance(module, str):
        module = importlib.import_module(module)
    parser = SageDocTestParser(long=True, optional_tags=('sage',))
    finder = doctest.DocTestFinder(parser=parser)
    checker = SageOutputChecker()
    opts = doctest.NORMALIZE_WHITESPACE|doctest.ELLIPSIS
    runner = doctest.DocTestRunner(checker=checker, optionflags=opts, verbose=verbose)
    for test in finder.find(module):
        test.globs.update(globs)
        runner.run(test)


def test_trac_model():
    testmod('git_trac.trac_error')
    from git_trac.test_builder import TestBuilder
    test = TestBuilder()
    app = test.make_app()
    globs = {'test':test, 'app':app, 'trac':app.trac}
    testmod('git_trac.trac_server', globs=globs)
    
 

def test_git_model():
    testmod('git_trac.git_error')
    from git_trac.test_builder import TestBuilder
    cwd = os.getcwd()
    test = TestBuilder()
    try:
        os.chdir(test.repo_path)
        repo = test.make_repo(verbose=True, user_email_set=True)
        globs = {'test':test, 'repo':repo, 'git':repo.git}
        testmod('git_trac.git_interface', globs=globs)
        repo = test.make_repo(verbose=False, user_email_set=True)
        globs = {'test':test, 'repo':repo, 'git':repo.git}
        testmod('git_trac.git_commit', globs=globs)
        testmod('git_trac.git_repository', globs=globs)
    finally:
        os.chdir(cwd)

def test_app():
    from git_trac.test_builder import TestBuilder
    cwd = os.getcwd()
    test = TestBuilder()
    try:
        os.chdir(test.repo_path)
        app = test.make_app()
        globs = {'test':test, 'app':app}
        testmod('git_trac.app', globs=globs)
    finally:
        os.chdir(cwd)

        
def run_doctests():
    testmod('git_trac.doctest_parser')    
    testmod('git_trac.pretty_ticket')    
    testmod('git_trac.releasemgr.commit_message')    
    test_app()
    return
    test_trac_model()
    test_git_model()


def auto_run_tests():
    import subprocess
    while True:
        subprocess.check_call(['inotifywait', '--recursive', 
                               '--event', 'close_write', '.'])
        print('Running doctests...')
        subprocess.call(sys.argv[0])

if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'auto':
            auto_run_tests()
        else:
            raise ValueError('Usage: test.py auto')
    run_doctests()

