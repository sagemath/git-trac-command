"""
Pretty-Print Tickets

EXAMPLES:

    sage: class Ticket(object):
    ....:     number = 1234
    ....:     title = 'Title'
    ....:     description = 'description'
    ....:     reporter = 'Reporter'
    ....:     author = 'Author'
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
    sage: from git_trac.pretty_ticket import format_ticket
    sage: print(format_ticket(ticket))
    ==============================================================================
    Trac #1234: Title
    <BLANKLINE>
    description
    Status: Status                          Component: Component                
    Last modified: modification time string Created: creation time string UTC
    Report upstream: Upstream
    Authors: Author
    Reviewers: Reviewer
    Branch: Branch
    Keywords: Keywords
    Dependencies: Dependencies
    ------------------------------------------------------------------------------
    URL: http://trac.sagemath.org/1234
    ==============================================================================
"""

import re
import textwrap


SEPARATOR_TEMPLATE = '\n' + '-' * 78 + '\n'

#123456789 123456789 123456789 123456789 123456789 123456789 123456789 123456789

DESCRIPTION_TEMPLATE = '=' * 78 + """
Trac #{ticket.number}: {ticket.title}

{ticket.description}
Status: {ticket.status: <25}       Component: {ticket.component: <25}
Last modified: {ticket.mtime_str: <25}Created: {ticket.ctime_str} UTC
Report upstream: {ticket.upstream}
Authors: {ticket.author}
Reviewers: {ticket.reviewer}
Branch: {ticket.branch}
Keywords: {ticket.keywords}
Dependencies: {ticket.dependencies}
"""

"""
Reported by: {ticket.reporter:    <25} Owner: {ticket.owner:          <25}
"""



GENERIC_CHANGE_TEMPLATE = """
[{change.change_capitalized}] {change.change_action}
"""

CHANGE_TEMPLATES = {
    'comment_set':
"""
Comment #{change.number} by {change.author} at {change.ctime} UTC:
{change.comment}
""",


    'author_set': 
"""
[Authors] set to {change.new}
""",
    'author_del': 
"""
[Authors] {change.old} deleted
""",
    'author_mod':
"""
[Authors] changed from {change.old} to {change.new}
""",


    'reviewer_set': 
"""
[Reviewers] set to {change.new}
""",
    'reviewer_mod':
"""
[Reviewers] changed from {change.old} to {change.new}
""",
    'reviewer_del': 
"""
[Reviewers] {change.old} deleted
""",


    'description_set': "[Description] modified",
    'description_mod': "[Description] modified",
    'description_del': "[Description] modified",

    'attachment_set':
"""
[Attachment] "{change.new}" added
""",
    'attachment_mod':
"""
[Attachment] "{change.new}" updated
""",
    'attachment_del':
"""
[Attachment] "{change.old}" deleted
""",

    'summary_set': 
"""
[Summary] set to {change.new}
""",
    'summary_mod': 
"""
[Summary] changed to {change.new}
""",
    'summary_del': 
"""
[Summary] {change.old} deleted
""",

    'upstream_set':
"""
[Report Upstream] set to {change.new}
""",
    'upstream_mod':
"""
[Report Upstream] changed to {change.new}
""",
    'upstream_del':
"""
[Report Upstream] {change.old} deleted
""",
}


COMMENT_TEMPLATE = """
Comment #{change.number} by {change.author} at {change.ctime} UTC:
{change.comment}
"""

FOOTER_TEMPLATE = """
URL: http://trac.sagemath.org/{ticket.number}
""" + '=' * 78


def wrap_lines(text):
    text = text.strip()
    accumulator = []
    for line in text.splitlines():
        line = '\n'.join(textwrap.wrap(line, 78))
        accumulator.append(line)
    return '\n'.join(accumulator)


def format_ticket(ticket):
    result = []
    result.append(DESCRIPTION_TEMPLATE.format(ticket=ticket))
    for change_set in ticket.grouped_comment_iter():
        result.append(SEPARATOR_TEMPLATE.format(ticket=ticket))
        for change in change_set:
            if change.change.startswith('_'):
                # changed comments are returned like this
                continue
            if change.old == '' and change.new == '' and change.change != 'comment':
                continue
            if change.old == '':
                change_type = change.change + '_set'
            elif change.new == '':
                change_type = change.change + '_del'
            else:
                change_type = change.change + '_mod'
            template = CHANGE_TEMPLATES.get(
                change_type, GENERIC_CHANGE_TEMPLATE)
            result.append(template.format(
                ticket=ticket, change=change).strip())
            #result.append('DEBUG ' + str(change.get_data()))
    result.append(SEPARATOR_TEMPLATE.format(ticket=ticket))
    result.append(FOOTER_TEMPLATE.format(ticket=ticket))
    result = '\n'.join(r.strip() for r in result)
    return wrap_lines(result)
