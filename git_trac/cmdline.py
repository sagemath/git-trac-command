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
import warnings
import argparse

from .logger import logger
from .ticket_or_branch import TicketOrBranch


def xdg_open(uri):
    import subprocess
    if sys.platform == 'darwin':
        rc = subprocess.call(['open', uri])
        error = 'Failed to run "open", please open {0}'
    else:
        rc = subprocess.call(['xdg-open', uri])
        error = 'Failed to run "xdg-open", please open {0}'
    if rc != 0: 
        print(error.format(uri))


def show_cheat_sheet():
    root_dir = os.path.dirname(os.path.dirname(__file__))
    cheat_sheet = os.path.join(root_dir, 'doc', 'git-cheat-sheet.pdf')
    xdg_open(cheat_sheet)


def debug_shell(app, parser):
    from IPython.terminal.ipapp import TerminalIPythonApp
    ip = TerminalIPythonApp.instance()
    ip.initialize(argv=[])
    ip.shell.user_global_ns['app'] = app
    ip.shell.user_global_ns['logger'] = logger
    ip.shell.user_global_ns['repo'] = app.repo
    ip.shell.user_global_ns['git'] = app.git
    ip.shell.user_global_ns['trac'] = app.trac
    ip.shell.user_global_ns['parser'] = parser
    def ipy_import(module_name, identifier):
        import importlib
        module = importlib.import_module(module_name)
        ip.shell.user_global_ns[identifier] = getattr(module, identifier) 
    ipy_import('git_trac.git_interface', 'GitInterface')
    ipy_import('git_trac.trac_server', 'TracServer')
    ip.start()



description = \
"""
The trac command extension for git
"""

def monkey_patch():
    """
    Monkey patch ArgumentParser
    """
    old_parse_args = argparse.ArgumentParser.parse_args

    def parse_args_override(self, args=None):
        """
        http://bugs.python.org/issue9253 prevents us from just redefining -h
        Workaround by monkey-patching parse_args
        """
        if args is None:
            args = list(sys.argv)[1:]
        if len(args) == 1 and args[-1] == '-h':
            # Convert "git-trac -h" to "git-trac help"
            args[-1] = 'help'
        return old_parse_args(self, args)

    setattr(argparse.ArgumentParser, 'parse_args', parse_args_override)



def make_parser():
    monkey_patch()
    parser = argparse.ArgumentParser(description=description, add_help=False)
    # We cannot handle "git trac --help", this is outside of our control and purely within git
    # redefine to not print '--help' in the online help
    parser.add_argument('-h', dest='option_help', action='store_true',
                        default=False, 
                        help='show this help message and exit')

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
    parser_checkout.add_argument('ticket_or_branch', type=TicketOrBranch, 
                                 help='Ticket number or remote branch name')

    parser_search = subparsers.add_parser('search', help='Search trac')
    parser_search.add_argument('--branch', dest='branch_name', 
                               help='Remote git branch name (default: local branch)', 
                               default=None)

    parser_fetch = subparsers.add_parser('fetch', help='Fetch branch from trac ticket')
    parser_fetch.add_argument('ticket_or_branch', nargs='?', type=TicketOrBranch, 
                             help='Ticket number or remote branch name', default=None)

    parser_pull = subparsers.add_parser('pull', help='Get updates')
    parser_pull.add_argument('ticket_or_branch', nargs='?', type=TicketOrBranch, 
                             help='Ticket number or remote branch name', default=None)

    parser_push = subparsers.add_parser('push', help='Upload changes')
    parser_push.add_argument('--force', dest='force', action='store_true',
                            default=False, help='Force push')
    parser_push.add_argument('--branch', dest='remote',
                            default=None, help='Remote branch name')
    parser_push.add_argument('ticket', nargs='?', type=int, 
                             help='Ticket number', default=None)

    parser_get = subparsers.add_parser('get', help='Print trac page')
    parser_get.add_argument('ticket', nargs='?', type=int, 
                                 help='Ticket number', default=None)

    parser_depends = subparsers.add_parser('depends', help='Print trac dependencies')
    parser_depends.add_argument('ticket', nargs='?', type=int, 
                                help='Ticket number', default=None)

    parser_print = subparsers.add_parser('print', help='Print trac page')
    parser_print.add_argument('ticket', nargs='?', type=int, 
                                 help='Ticket number', default=None)

    parser_browse = subparsers.add_parser('browse', help='Open trac page in browser')
    parser_browse.add_argument('ticket', nargs='?', type=int, 
                               help='Ticket number', default=None)

    parser_review = subparsers.add_parser('review', help='Show code to review')
    parser_review.add_argument('ticket', nargs='?', type=int, 
                               help='Ticket number', default=None)

    parser_find = subparsers.add_parser('find', help='Find trac ticket from SHA1')
    parser_find.add_argument('commit', type=str, help='Commit SHA1')

    parser_try = subparsers.add_parser('try', help='Try out trac ticket in "detached HEAD"')
    parser_try.add_argument('ticket_or_branch', type=TicketOrBranch, 
                            help='Ticket number or remote branch name')

    parser_log = subparsers.add_parser('log', help='Commit log for ticket')
    parser_log.add_argument('ticket', type=int, help='Ticket number')
    parser_log.add_argument('--oneline', dest='oneline', action='store_true',
                            default=False, help='One line per commit')

    parser_config = subparsers.add_parser('config', help='Configure git-trac')
    parser_config.add_argument('--user', dest='trac_user', 
                               help='Trac username', default=None)
    parser_config.add_argument('--pass', dest='trac_pass', 
                               help='Trac password', default=None)

    parser_cheatsheet = subparsers.add_parser('cheat-sheet', help='Show the git trac cheat sheet')

    parser_help = subparsers.add_parser('help', help='Show the git trac help')

    return parser



def launch():
    parser = make_parser()
    args = parser.parse_args(sys.argv[1:])
    if args.log is not None:
        import logging
        level = getattr(logging, args.log)
        logger.setLevel(level=level)

    from .app import Application
    app = Application()

    if args.debug:
        print(args)
        app.config.debug = True
        debug_shell(app, parser)
    elif args.option_help:
        parser.print_help()
    elif args.subcommand == 'create':
        app.create(args.summary, args.branch_name)
    elif args.subcommand == 'checkout':
        app.checkout(args.ticket_or_branch, args.branch_name)
    elif args.subcommand == 'fetch':
        app.fetch(args.ticket_or_branch)
    elif args.subcommand == 'pull':
        app.pull(args.ticket_or_branch)
    elif args.subcommand == 'push':
        ticket_number = app.guess_ticket_number(args.ticket)
        print('Pushing to Trac #{0}...'.format(ticket_number)) 
        app.push(ticket_number, remote=args.remote, force=args.force)
    elif args.subcommand == 'review':
        ticket_number = app.guess_ticket_number(args.ticket)
        app.review_diff(ticket_number)
    elif args.subcommand == 'try':
        app.tryout(args.ticket_or_branch)
    elif args.subcommand == 'get':
        warnings.warn('deprecated; use "git trac print" instead')
        ticket_number = app.guess_ticket_number(args.ticket)
        app.print_ticket(ticket_number)
    elif args.subcommand == 'print':
        ticket_number = app.guess_ticket_number(args.ticket)
        app.print_ticket(ticket_number)
    elif args.subcommand == 'depends':
        ticket_number = app.guess_ticket_number(args.ticket)
        app.print_dependencies(ticket_number)
    elif args.subcommand == 'browse':
        ticket_number = app.guess_ticket_number(args.ticket)
        xdg_open('https://trac.sagemath.org/{0}'.format(ticket_number))
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
        app.add_remote()
        if args.trac_user is not None:
            app.save_trac_username(args.trac_user)
        if args.trac_pass is not None:
            app.save_trac_password(args.trac_pass)
        app.print_config()
    elif args.subcommand == 'cheat-sheet':
        show_cheat_sheet()
    elif args.subcommand == 'help':
        parser.print_help()
    else:
        print('Unknown subcommand "{0}"'.format(args.subcommand))
        parser.print_help()
