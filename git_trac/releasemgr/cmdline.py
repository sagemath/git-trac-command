# -*- encoding: utf-8 -*-
"""
Handle Command Line Options
"""

##############################################################################
#  The "git releasemgr ..." command extension for git
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
import os
import importlib

from ..logger import logger



def debug_shell(app):
    from IPython.terminal.ipapp import TerminalIPythonApp
    ip = TerminalIPythonApp.instance()
    ip.initialize(argv=[])
    ip.shell.user_global_ns['app'] = app
    ip.shell.user_global_ns['repo'] = app.repo
    ip.shell.user_global_ns['git'] = app.git
    ip.shell.user_global_ns['trac'] = app.trac
    def ipy_import(module_name, identifier):
        module = importlib.import_module(module_name)
        ip.shell.user_global_ns[identifier] = getattr(module, identifier) 
    ipy_import('git_trac.git_interface', 'GitInterface')
    ipy_import('git_trac.trac_server', 'TracServer')
    ip.start()



description = \
"""
The Sage release management command extension for git
"""



def launch():
    from argparse import ArgumentParser
    parser = ArgumentParser(description=description)
    parser.add_argument('--debug', dest='debug', action='store_true',
                        default=False, 
                        help='debug')
    parser.add_argument('--log', dest='log', default=None,
                        help='one of [DEBUG, INFO, ERROR, WARNING, CRITICAL]')
    subparsers = parser.add_subparsers(dest='subcommand')

    # git releasemgr print
    parser_print = subparsers.add_parser('print', help='Print as commit message')
    parser_print.add_argument('ticket', type=int, help='Ticket number')

    # git releasemgr merge
    parser_merge = subparsers.add_parser('merge', help='Merge branch from ticket')
    parser_merge.add_argument('--close', dest='close', action='store_true',
                               help='Close ticket', default=False)
    parser_merge.add_argument('--allow-empty', dest='allow_empty', 
                              action='store_true',
                              help='Allow empty commits', default=False)
    parser_merge.add_argument('--ignore-dependencies', dest='ignore_dependencies', 
                              action='store_true',
                              help='Do not check whether dependencies are merged', default=False)
    parser_merge.add_argument('--ignore-name', dest='ignore_name', 
                              action='store_true',
                              help='Do not sanity-check names', default=False)
    parser_merge.add_argument('tickets', type=int, nargs='+', help='Ticket number(s)')

    # git releasemgr merge-all
    parser_merge_all = subparsers.add_parser('merge-all', help='Merge all tickets that are ready')

    # git releasemgr test
    parser_test = subparsers.add_parser('test', help='Test merge unreview ticket')
    parser_test.add_argument('ticket', type=int, help='Ticket number')

    # git releasemgr unmerge
    parser_unmerge = subparsers.add_parser('unmerge', help='Unmerge branch from ticket')
    parser_unmerge.add_argument('ticket', type=int, help='Ticket number')

    # git releasemgr close
    parser_close = subparsers.add_parser('close', help='Close merged tickets')
    parser_close.add_argument('--head', dest='head', default='HEAD',
                               help='Head commit')
    parser_close.add_argument('--exclude', dest='exclude', default='trac/develop',
                               help='Exclude commit')

    # git releasemgr todo
    parser_todo = subparsers.add_parser('todo', help='Print list of tickets ready to merge')

    # git releasemgr upstream <url>
    parser_upstream = subparsers.add_parser('upstream', help='Upload upstream tarball')
    parser_upstream.add_argument('url', type=str, help='Tarball URL')

    # git releasemgr dist <tarball>
    parser_dist = subparsers.add_parser('dist', help='Upload Sage source tarball')
    parser_dist.add_argument('tarball', type=str, help='Tarball filename')

    # git releasemgr release <version>
    parser_release = subparsers.add_parser('release', help='Create new release')
    parser_release.add_argument('--check', action='store_true', 
                                default=False, help='Extra checks')
    parser_release.add_argument('version', type=str, help='New version string')

    # git releasemgr publish
    parser_publish = subparsers.add_parser('publish', help='Publish version')

    args = parser.parse_args()
    print(args)

    if args.log is not None:
        import logging
        level = getattr(logging, args.log)
        logger.setLevel(level=level)

    if args.subcommand is None:
        return parser.print_help()

    from .app import ReleaseApplication
    app = ReleaseApplication()

    if args.debug:
        debug_shell(app)
    elif args.subcommand == 'print':
        app.print_ticket(args.ticket)
    elif args.subcommand == 'merge':
        app.merge_multiple(args.tickets, close=args.close, 
                           allow_empty=args.allow_empty,
                           ignore_dependencies=args.ignore_dependencies,
                           ignore_name=args.ignore_name)
    elif args.subcommand == 'test':
        app.test_merge(args.ticket)
    elif args.subcommand == 'unmerge':
        app.unmerge(args.ticket)
    elif args.subcommand == 'close':
        app.close_tickets(args.head, args.exclude)
    elif args.subcommand == 'publish':
        app.publish()
    elif args.subcommand == 'todo':
        app.todo()
    elif args.subcommand == 'merge-all':
        app.merge_all()
    elif args.subcommand == 'upstream':
        app.upstream(args.url)
    elif args.subcommand == 'dist':
        app.dist(args.tarball)
    elif args.subcommand == 'release':
        app.release(args.version, check=args.check)
    else:
        print('Unknown subcommand "{0}"'.format(args.subcommand))
        parser.print_help()
