## -*- encoding: utf-8 -*-
"""
Handle Command Line Options
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
The trac command extension for git
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

    parser_create = subparsers.add_parser('create', help='Create new ticket')
    parser_create.add_argument('-b', '--branch', dest='branch_name', 
                               help='Branch name', 
                               default=None)
    parser_create.add_argument('summary', type=str, help='Ticket summary')

    parser_checkout = subparsers.add_parser('checkout', help='Download branch')
    parser_checkout.add_argument('-b', '--branch', dest='branch_name', 
                                 help='Local branch name', 
                                 default=None)
    parser_checkout.add_argument('ticket', type=int, help='Ticket number')

    parser_search = subparsers.add_parser('search', help='Search trac')
    parser_search.add_argument('--branch', dest='branch_name', 
                               help='Remote git branch name (default: local branch)', 
                               default=None)

    parser_pull = subparsers.add_parser('pull', help='Get updates')
    parser_pull.add_argument('ticket', nargs='?', type=int, 
                             help='Ticket number', default=None)

    parser_push = subparsers.add_parser('push', help='Upload changes')
    parser_push.add_argument('ticket', nargs='?', type=int, 
                             help='Ticket number', default=None)

    parser_get = subparsers.add_parser('get', help='Print trac field')
    parser_get.add_argument('ticket', nargs='?', type=int, 
                                 help='Ticket number', default=None)

    parser_find = subparsers.add_parser('find', help='Find trac ticket')
    parser_find.add_argument('commit', type=str, help='Commit SHA1')

    parser_log = subparsers.add_parser('log', help='Commit log for ticket')
    parser_log.add_argument('ticket', type=int, help='Ticket number')
    parser_log.add_argument('--oneline', dest='oneline', action='store_true',
                            default=False, help='One line per commit')

    parser_config = subparsers.add_parser('config', help='Configure git-trac')
    parser_config.add_argument('--user', dest='trac_user', 
                               help='Trac username', default=None)
    parser_config.add_argument('--pass', dest='trac_pass', 
                               help='Trac password', default=None)

    args = parser.parse_args()

    print(args)

    if args.log is not None:
        level = getattr(logging, args.log)
        logging.basicConfig(level=level)

    from .app import Application
    app = Application()

    if args.debug:
        debug_shell(app)
    elif args.subcommand == 'create':
        app.create(args.summary, args.branch_name)
    elif args.subcommand == 'checkout':
        app.checkout(args.ticket, args.branch_name)
    elif args.subcommand == 'pull':
        ticket_number = app.guess_ticket_number(args.ticket)
        app.pull(ticket_number)
    elif args.subcommand == 'push':
        ticket_number = app.guess_ticket_number(args.ticket)
        print('Pushing to Trac #{0}...'.format(ticket_number)) 
        app.push(ticket_number)
    elif args.subcommand == 'get':
        ticket_number = app.guess_ticket_number(args.ticket)
        app.print_ticket(ticket_number)
    elif args.subcommand == 'log':
        app.log(args.ticket, oneline=args.oneline)
    elif args.subcommand == 'find':
        app.find(args.commit)
    elif args.subcommand == 'search':
        try:
            app.search(branch=args.branch_name)
        except ValueError:
            parser_search.print_help()
            raise
    elif args.subcommand == 'config':
        if args.trac_user is not None:
            app.save_trac_username(args.trac_user)
        if args.trac_pass is not None:
            app.save_trac_password(args.trac_pass)
        app.print_config()
    else:
        print('Unknown subcommand "{0}"'.format(args.subcommand))
        parser.print_help()
