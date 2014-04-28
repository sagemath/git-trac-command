"""
A Trac Ticket

EXAMPLES::

    sage: from datetime import datetime
    sage: create_time = datetime.utcfromtimestamp(1376149000)
    sage: modify_time = datetime.utcfromtimestamp(1376150000)
    sage: from git_trac.trac_ticket import TracTicket_class
    sage: t = TracTicket_class(123, create_time, modify_time, {})
    sage: t
    <git_trac.trac_ticket.TracTicket_class object at 0x...>
    sage: t.number
    123
    sage: t.title
    '<no summary>'
    sage: t.ctime
    datetime.datetime(2013, 8, 10, 15, 36, 40)
    sage: t.mtime
    datetime.datetime(2013, 8, 10, 15, 53, 20)
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

import textwrap
from datetime import datetime

def format_trac(text):
    text = text.strip()
    accumulator = []
    for line in text.splitlines():
        line = '\n'.join(textwrap.wrap(line, 78))
        accumulator.append(line)
    return '\n'.join(accumulator)

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
    return TicketChange_class(time, author, change, data=(data1, data2, data3))


class TicketChange_class(object):
    
    def __init__(self, time, author, change, data=None):
        self._time = make_time(time)
        self._author = author
        self._change = change
        if data:
            self._data = data
        else:
            self._data = ('', '', 1)

    def get_data(self):
        try:
            return ' ['+str(self._data)+']'
        except AttributeError:
            return ''

    @property
    def ctime(self):
        return self._time

    @property
    def ctime_str(self):
        return str(self.ctime)

    @property
    def author(self):
        return self._author
        
    @property
    def change(self):
        return self._change

    @property
    def change_capitalized(self):
        return self._change.capitalize()

    @property
    def old(self):
        return self._data[0]

    @property
    def new(self):
        return self._data[1]

    @property
    def change_action(self):
        if self.old == '':
            return u'set to {change.new}'.format(change=self)
        elif self.new == '':
            return u'{change.old} deleted'.format(change=self)
        else:
            return u'changed from {change.old} to {change.new}'.format(change=self)

    def __repr__(self):
        return self.get_author() + u' changed ' + self.get_change() + self.get_data()


class TicketComment_class(TicketChange_class):

    def __init__(self, time, author, change, data1, data2, data3):
        TicketChange_class.__init__(self, time, author, change)
        self._number = data1
        self._comment = data2

    @property
    def number(self):
        return self._number

    @property
    def comment(self):
        return self._comment

    @property
    def comment_formatted(self):
        return format_trac(self.comment)

    def __repr__(self):
        return self.author + ' commented "' + \
            self.comment + '" [' + self.number   + ']'


def TracTicket(ticket_number, server_proxy):
    from xml.parsers.expat import ExpatError
    ticket_number = int(ticket_number)
    try:
        change_log = server_proxy.ticket.changeLog(ticket_number)
    except ExpatError:
        print('Failed to parse the trac changelog, malformed XML!')
        change_log = []
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
    def timestamp(self):
        """
        Timestamp for XML-RPC calls
        
        The timestamp is an integer that must be set in subsequent
        ticket.update() XMLRPC calls to trac.
        """
        return self._data['_ts']

    @property
    def number(self):
        return self._number

    __int__ = number

    @property
    def title(self):
        return self._data.get('summary', '<no summary>')

    @property
    def ctime(self):
        return self._ctime

    @property
    def mtime(self):
        return self._mtime

    @property
    def ctime_str(self):
        return str(self.ctime)

    @property
    def mtime_str(self):
        return str(self.mtime)

    @property
    def branch(self):
        return self._data.get('branch', '').strip()

    @property
    def dependencies(self):
        return self._data.get('dependencies', '')

    @property
    def description(self):
        default = '+++ no description +++'
        return self._data.get('description', default)

    @property
    def description_formatted(self):
        return format_trac(self.description)

    def change_iter(self):
        for change in self._change_log:
            yield change

    def comment_iter(self):
        for change in self._change_log:
            if isinstance(change, TicketComment_class):
                yield change

    def grouped_comment_iter(self):
        change_iter = iter(self._change_log)
        change = next(change_iter)
        def sort_key(c):
            return (-int(c.change == 'comment'), c.change)
        while True:
            stop = False
            time = change.ctime
            accumulator = [(sort_key(change), change)]
            while True:
                try:
                    change = next(change_iter)
                except StopIteration:
                    stop = True
                    break
                if change.ctime == time:
                    accumulator.append((sort_key(change), change))
                else:
                    break
            yield tuple(c[1] for c in sorted(accumulator))
            if stop:
                raise StopIteration
        
    @property
    def author(self):
        return self._data.get('author', '<no author>')

    @property
    def cc(self):
        return self._data.get('cc', '')

    @property
    def component(self):
        return self._data.get('component', '')

    @property
    def reviewer(self):
        return self._data.get('reviewer', '<no reviewer>')

    @property
    def reporter(self):
        return self._data.get('reporter', '<no reporter>')

    @property
    def milestone(self):
        return self._data.get('milestone', '<no milestone>')

    @property
    def owner(self):
        return self._data.get('owner', '<no owner>')

    @property
    def priority(self):
        return self._data.get('priority', '<no priority>')

    @property
    def commit(self):
        return self._data.get('commit', '')

    @property
    def keywords(self):
        return self._data.get('keywords', '')

    @property
    def ticket_type(self):
        return self._data.get('type', '<no type>')

    @property
    def upstream(self):
        return self._data.get('upstream', '<no upstream status>')

    @property
    def status(self):
        return self._data.get('status', '<no status>')

    @property
    def work_issues(self):
        return self._data.get('work_issues', '')
