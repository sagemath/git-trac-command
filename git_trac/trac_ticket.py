"""
A Trac Ticket

EXAMPLES::

    sage: from datetime import datetime
    sage: create_time = datetime.fromtimestamp(1376149000)
    sage: modify_time = datetime.fromtimestamp(1376150000)
    sage: from git_trac.trac_ticket import TracTicket_class
    sage: t = TracTicket_class(123, create_time, modify_time, {})
    sage: t
    <git_trac.trac_ticket.TracTicket_class object at 0x...>
    sage: t.number
    123
    sage: t.title
    '+++ no summary +++'
    sage: t.ctime
    datetime.datetime(2013, 8, 10, 16, 36, 40)
    sage: t.mtime
    datetime.datetime(2013, 8, 10, 16, 53, 20)
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


from datetime import datetime

def make_time(time):
    """
    Convert xmlrpc DateTime objects to datetime.datetime
    """
    if isinstance(time, datetime):
        return time
    return datetime.strptime(time.value, "%Y%m%dT%H:%M:%S")


def TicketChange(changelog_entry):
    time, author, change, data1, data2, data3 = changelog_entry
    # print(time, author, change, data1, data2, data3)
    if change == 'comment':
        return TicketComment_class(time, author, change, data1, data2, data3)
    return TicketChange_class(time, author, change, debug=(data1, data2, data3))


class TicketChange_class(object):
    
    def __init__(self, time, author, change, debug=None):
        self._time = make_time(time)
        self._author = author
        self._change = change
        if debug:
            self._debug = debug

    def get_debug(self):
        try:
            return ' ['+str(self._debug)+']'
        except AttributeError:
            return ''

    @property
    def ctime(self):
        return self._time

    @property
    def author(self):
        return self._author
        
    @property
    def change(self):
        return self._change

    def __repr__(self):
        return self.get_author() + ' changed ' + self.get_change() + self.get_debug()


class TicketComment_class(TicketChange_class):

    def __init__(self, time, author, change, data1, data2, data3):
        TicketChange_class.__init__(self, time, author, change)
        self._number = data1
        self._comment = data2
        if data3 != 1:
            print('TicketComment got data3 =', data3)

    @property
    def number(self):
        return self._number

    @property
    def comment(self):
        return self._comment

    def __repr__(self):
        return self.author + ' commented "' + \
            self.comment + '" [' + self.number   + ']'


def TracTicket(ticket_number, server_proxy):
    ticket_number = int(ticket_number)
    change_log = server_proxy.ticket.changeLog(ticket_number)
    data = server_proxy.ticket.get(ticket_number)
    ticket_changes = [TicketChange(entry) for entry in change_log]
    return TracTicket_class(data[0], data[1], data[2], data[3], ticket_changes)


class TracTicket_class(object):
    
    def __init__(self, number, ctime, mtime, data, change_log=None):
        self._number = number
        self._ctime = make_time(ctime)
        self._mtime = make_time(mtime)
        self._last_viewed = None
        self._download_time = None
        self._data = data
        self._change_log = change_log

    @property
    def number(self):
        return self._number

    __int__ = number

    @property
    def title(self):
        return self._data.get('summary', '+++ no summary +++')

    @property
    def ctime(self):
        return self._ctime

    @property
    def mtime(self):
        return self._mtime

    @property
    def branch(self):
        branch = self._data.get('branch', '')
        return None if len(branch) == 0 else branch

    @property
    def dependencies(self):
        deps = self._data.get('dependencies', '')
        return None if len(deps) == 0 else deps

    @property
    def description(self):
        default = '+++ no description +++'
        return self._data.get('description', default)

    def comment_iter(self):
        for change in self._change_log:
            if isinstance(change, TicketComment_class):
                yield change
        
