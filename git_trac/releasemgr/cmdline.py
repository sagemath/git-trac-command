## -*- encoding: utf-8 -*-
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
import logging



def debug_shell(app):
    from IPython.frontend.terminal.ipapp import TerminalIPythonApp
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

    parser_print = subparsers.add_parser('print', help='Print as commit message')
    parser_print.add_argument('ticket', type=int, help='Ticket number')

    parser_merge = subparsers.add_parser('merge', help='Merge branch')
    parser_merge.add_argument('--close', dest='close', action='store_false',
                               help='Close ticket', default=False)
    parser_merge.add_argument('ticket', type=int, help='Ticket number')
    args = parser.parse_args()
    print(args)

    if args.log is not None:
        level = getattr(logging, args.log)
        logging.basicConfig(level=level)

    if args.subcommand is None:
        return parser.print_help()

    from .app import ReleaseApplication
    app = ReleaseApplication()

    if args.debug:
        debug_shell(app)
    elif args.subcommand == 'print':
        app.print_ticket(args.ticket)
    elif args.subcommand == 'merge':
        app.merge(args.ticket, close=args.close)
