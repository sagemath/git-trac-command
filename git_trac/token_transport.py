"""
HTTP transport to the Trac server using token-based authentication on each
request.
"""

try:
    import urllib2 as urllib
except ImportError:
    import urllib.request as urllib

try:
    from xmlrpclib import SafeTransport, Fault
except ImportError:
    from xmlrpc.client import SafeTransport, Fault

from .trac_error import (
    TracInternalError, TracAuthenticationError, TracConnectionError)


class TokenAuthHandler(urllib.BaseHandler):
    def __init__(self, token=''):
        super(TokenAuthHandler, self).__init__()
        self._token = token

    def http_request(self, req):
        if not req.has_header('Authorization'):
            auth = 'Bearer ' + self._token
            req.add_unredirected_header(
                'Authorization', auth.strip())

        return req

    https_request = http_request


class TokenAuthenticatedTransport(SafeTransport, object):
    def __init__(self, token):
        super(TokenAuthenticatedTransport, self).__init__()
        self._token = token

    def single_request(self, host, handler, request_body, verbose):
        """
        Issue an XML-RPC request.
        """

        try:
            return super(TokenAuthenticatedTransport, self).single_request(
                    host, handler, request_body, verbose)
        except Fault as e:
            raise TracInternalError(e)
        except IOError as e:
            if hasattr(e, 'code') and e.code == 401:
                raise TracAuthenticationError()
            else:
                raise TracConnectionError(e.reason)

    def get_host_info(self, host):
        host, extra_headers, x509 = super(TokenAuthenticatedTransport,
                self).get_host_info(host)

        if extra_headers:
            headers = dict(extra_headers)
        else:
            headers = {}
            extra_headers = []

        if 'Authorization' not in headers:
            auth = 'Bearer ' + self._token
            extra_headers.append(('Authorization', auth.strip()))

        return host, extra_headers, x509
