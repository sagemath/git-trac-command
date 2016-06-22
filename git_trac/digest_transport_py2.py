r"""
Python 2.7 version of the HTTP transport to the trac server

AUTHORS:

- David Roe, Julian Rueth, Robert Bradshaw: initial version

"""
#*****************************************************************************
#       Copyright (C) 2013 David Roe <roed.math@gmail.com>
#                          Julian Rueth <julian.rueth@fsfe.org>
#                          Robert Bradshaw <robertwb@gmail.com>
#
#  Distributed under the terms of the GNU General Public License (GPL)
#  as published by the Free Software Foundation; either version 2 of
#  the License, or (at your option) any later version.
#                  http://www.gnu.org/licenses/
#*****************************************************************************

import sys
from xmlrpclib import SafeTransport, Fault
import urllib2

# Monkey patch http://bugs.python.org/issue8194
if (sys.version_info[0] == 2 and
    sys.version_info[1] == 7 and
    sys.version_info[2] <= 1):

    import httplib
    class patched_addinfourl(urllib2.addinfourl):

        def getheader(self, name, default=None):
            if self.headers is None:
                raise httplib.ResponseNotReady()
            return self.headers.getheader(name, default)

        def getheaders(self):
            if self.headers is None:
                raise httplib.ResponseNotReady()
            return self.headers.items()

    urllib2.addinfourl = patched_addinfourl



from .trac_error import \
    TracInternalError, TracAuthenticationError, TracConnectionError
from .cached_property import cached_property


class DigestTransport(object, SafeTransport):
    """
    Handles an HTTP transaction to an XML-RPC server.

    EXAMPLES::

        sage: from sage.dev.digest_transport import DigestTransport
        sage: DigestTransport()
        <sage.dev.digest_transport.DigestTransport object at ...>
    """
    def __init__(self):
        """
        Initialization.

        EXAMPLES::

            sage: from sage.dev.digest_transport import DigestTransport
            sage: type(DigestTransport())
            <class 'sage.dev.digest_transport.DigestTransport'>
        """
        super(DigestTransport, self).__init__()
        self._use_datetime = 0

    @cached_property
    def opener(self):
        """
        Create an opener object.

        By calling :meth:`add_authentication` before calling this property for
        the first time, authentication credentials can be set.

        EXAMPLES::

            sage: from sage.dev.digest_transport import DigestTransport
            sage: DigestTransport().opener
            <urllib2.OpenerDirector instance at 0x...>
        """
        return urllib2.build_opener(urllib2.HTTPDigestAuthHandler())

    def single_request(self, host, handler, request_body, verbose):
        """
        Issue an XML-RPC request.

        EXAMPLES::

            sage: from sage.dev.digest_transport import DigestTransport
            sage: from sage.env import TRAC_SERVER_URI
            sage: import urlparse
            sage: url = urlparse.urlparse(TRAC_SERVER_URI).netloc
            sage: d = DigestTransport()
            sage: d.single_request(url, 'xmlrpc', "<?xml version='1.0'?><methodCall><methodName>ticket.get</methodName><params><param><value><int>1000</int></value></param></params></methodCall>", 0) # optional: internet
            ([1000,
              <DateTime '20071025T16:48:05' at ...>,
              <DateTime '...' at ...>,
              {'status': 'closed',
               'changetime': <DateTime '...' at ...>,
               'description': '...',
               'reporter': 'was',
               'cc': '',
               'type': 'defect',
               'milestone': 'sage-2.10',
               '_ts': '...',
               'component': 'distribution',
               'summary': 'Sage does not have 10000 users yet.',
               'priority': 'major',
               'owner': 'was',
               'time': <DateTime '20071025T16:48:05' at ...>,
               'keywords': '',
               'resolution': 'fixed'}],)
        """
        try:
            import urlparse
            req = urllib2.Request(
                    urlparse.urlunparse(('https', host, handler, '', '', '')),
                    request_body, {'Content-Type': 'text/xml',
                        'User-Agent': self.user_agent})
            response = self.opener.open(req)
            self.verbose = verbose
            return self.parse_response(response)
        except Fault as e:
            raise TracInternalError(e)
        except urllib2.HTTPError as e:
            if e.code == 401:
                raise TracAuthenticationError()
            else:
                raise TracConnectionError(e.reason)



class AuthenticatedDigestTransport(DigestTransport):

    def __init__(self, realm, url, username, password):
        """
        Set authentication credentials for the opener returned by
        :meth:`opener`.

        EXAMPLES::

            sage: from sage.dev.digest_transport import DigestTransport
            sage: dt = DigestTransport()
            sage: dt.add_authentication("realm", "url", "username", "password")
            sage: dt.opener
        """
        super(AuthenticatedDigestTransport, self).__init__()
        self._realm = realm
        self._url = url
        self._username = username
        self._password = password

    @cached_property
    def opener(self):
        authhandler = urllib2.HTTPDigestAuthHandler()
        authhandler.add_password(
            self._realm, self._url, self._username, self._password)
        return urllib2.build_opener(authhandler)
