

import re


class VersionString(object):
 
    V_BETA    = re.compile(r'^[0-9]+\.[0-9]+\.beta[0-9]+$')
    V_RC      = re.compile(r'^[0-9]+\.[0-9]+\.rc[0-9]+$')
    V_STABLE  = re.compile(r'^[0-9]+\.[0-9]+$')
    V_STABLE2 = re.compile(r'^[0-9]+\.[0-9]+\.[0-9]+$')
    
    def __init__(self, version):
        self.version = version
        self.validate()

    def is_beta(self):
        """
        Return whether the version is a beta version

        EXAMPLES::

            sage: from git_trac.releasemgr.version_string import VersionString
            sage: VersionString('6.7.beta0').is_beta()
            True
            sage: VersionString('6.7.rc0').is_beta()
            False
            sage: VersionString('6.8').is_beta()
            False
        """
        return bool(self.V_BETA.match(self.version))

    def is_rc(self):
        """
        Return whether the version is a release candidate

        EXAMPLES::

            sage: from git_trac.releasemgr.version_string import VersionString
            sage: VersionString('6.7.beta0').is_rc()
            False
            sage: VersionString('6.7.rc0').is_rc()
            True
            sage: VersionString('6.8').is_rc()
            False
        """
        return bool(self.V_RC.match(self.version))
    
    def is_stable(self):
        """
        Return whether the version is a development version

        EXAMPLES::

            sage: from git_trac.releasemgr.version_string import VersionString
            sage: VersionString('6.7.beta0').is_stable()
            False
            sage: VersionString('6.7.rc0').is_stable()
            False
            sage: VersionString('6.8').is_stable()
            True
        """
        return bool(self.V_STABLE.match(self.version) or
                    self.V_STABLE2.match(self.version))

    def is_devel(self):
        """
        Return whether the version is a development version

        EXAMPLES::

            sage: from git_trac.releasemgr.version_string import VersionString
            sage: VersionString('6.7.beta0').is_devel()
            True
            sage: VersionString('6.7.rc0').is_devel()
            True
            sage: VersionString('6.8').is_devel()
            False
        """
        return not self.is_stable()
    
    def validate(self):
        """
        Raise a ``ValueError`` if the version is not formatted correctly

        EXAMPLES::

            sage: from git_trac.releasemgr.version_string import VersionString
            sage: VersionString('6.7.beta0')
            <git_trac.releasemgr.version_string.VersionString object at 0x...>
            sage: VersionString('6.7.gamma0')
            Traceback (most recent call last):
            ...
            ValueError: version string 6.7.gamma0 is not valid
        """
        if not any([self.is_beta(), self.is_rc(), self.is_stable()]):
            raise ValueError('version string {0} is not valid'.format(self.version))
