# -*- coding: utf-8 -*-
u"""
Pretty-Print Ticket as Git Commit Message

EXAMPLES::

    sage: class Ticket(object):
    ....:     number = 1234
    ....:     title = 'Title'
    ....:     description = u'description äöü'
    ....:     reporter = 'Reporter'
    ....:     author = u'Ingólfur Eðvarðsson'
    ....:     reviewer = 'Reviewer'
    ....:     branch = 'Branch'
    ....:     keywords = 'Keywords'
    ....:     dependencies = 'Dependencies'
    ....:     ctime_str = 'creation time string'
    ....:     mtime_str = 'modification time string'
    ....:     owner = 'Owner'
    ....:     upstream = 'Upstream'
    ....:     status = 'Status'
    ....:     component = 'Component'
    ....:     def grouped_comment_iter(self):
    ....:         return ()
    sage: ticket = Ticket()
    sage: from git_trac.releasemgr.commit_message import format_ticket
    sage: print(format_ticket(ticket))
    Trac #1234: Title
    <BLANKLINE>
    description äöü
    <BLANKLINE>
    URL: https://trac.sagemath.org/1234
    Reported by: Reporter
    Ticket author(s): Ingólfur Eðvarðsson
    Reviewer(s): Reviewer
"""

import re
import textwrap



#123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789

SUMMARY_TEMPLATE = u"""
Trac #{ticket.number}: {ticket.title}
"""

DESCRIPTION_TEMPLATE = u"""
{ticket.description}

URL: https://trac.sagemath.org/{ticket.number}
Reported by: {ticket.reporter}
Ticket author(s): {ticket.author}
Reviewer(s): {ticket.reviewer}
"""


def wrap_lines(text):
    text = text.strip()
    accumulator = []
    for line in text.splitlines():
        line = '\n'.join(textwrap.wrap(line, 72))
        accumulator.append(line)
    return '\n'.join(accumulator)


def format_ticket(ticket):
    summary = SUMMARY_TEMPLATE.format(ticket=ticket).strip()
    if len(summary) > 72:
        print('Warning: Overlong summary at {0} characters.'.format(len(summary)))
    description = DESCRIPTION_TEMPLATE.format(ticket=ticket)
    description = wrap_lines(description)
    return summary + '\n\n' + description
