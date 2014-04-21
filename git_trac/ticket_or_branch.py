"""
Ticket Number or Remote Branch Name
"""


class TicketOrBranch(object):

    def __init__(self, name):
        self._name = name
        self._validate()

    def __int__(self):
        try:
            return int(self._name)        
        except ValueError:
            pass

    def __str__(self):
        return self._name

    def is_number(self):
        try:
            int(self._name)
            return True
        except ValueError:
            return False

    def is_branch(self):
        for prefix in ['u/', 'public/']:
            if self._name.startswith(prefix):
                return True
        if self._name in ['master', 'develop']:
            return True
        return False

    def _validate(self):
        if self.is_number() or self.is_branch():
            return
        raise ValueError('Not a valid ticket number or remote branch name')
            
