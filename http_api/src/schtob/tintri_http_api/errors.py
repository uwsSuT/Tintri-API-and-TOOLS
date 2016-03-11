# -*- coding: utf-8 -*-
"""
    schtob.tintri_http_api.errors
    ~~~~~~~~~~~~~~~~~~~~~~

    Tintri HTTP Exception classes.

    :copyright: 2016 Schaefer & Tobies SuC GmbH.
    :author: Uwe W. Schaefer <uws@schaefer-tobies.de>
    :license: LGPL, see LICENSE for details.
"""

Tintri_ErrNumbers = {
    '200' : "Successful API call with non empty result body",
    '204' : "Successful API call with empty result body",
    '400' : "Bad request - Request validation failed. Request content incorrect/invalid",
    '401' : "Non authorized API access - User needs to successfully login with needed privileges to perform the operation",
    '403' : "Forbidden - invalid credentials or licenses. Some APIs, like /v310/vm/sync require a license.",
    '404' : "API not found",
    '500' : "Internal Error - something went wrong in the server side processing",
}

class TintriHTTP_Error(Exception):
    """Base class for Tintri HTTP Exceptions."""
    pass


class API_Failure(TintriHTTP_Error):
    """Exception class for unsuccessful API calls."""

    def __init__(self, err_msg, errno):
        TintriHTTP_Error.__init__(self)
        self.err_msg = err_msg
        self.errno = errno

    def get_error(self):
        """Returns an error message."""
        return """APIFailure (Err Nr. %(errno)s - %(err_msg)s
    TintriInfo : %(terror)s
    """ % {
                'err_msg': self.err_msg,
                'errno': self.errno,
                'terror': Tintri_ErrNumbers[str(self.errno)],
          }

    def get_errno(self):
        """Returns the error number."""
        return self.errno

    def __str__(self):
        return self.get_error()


class HTTP_Failure(TintriHTTP_Error):
    """Exception class for unsuccessful API calls."""

    def __init__(self, err_msg):
        TintriHTTP_Error.__init__(self)
        self.err_msg = err_msg

    def get_error(self):
        """Returns an error message."""
        return """HTTPFailure %(err_msg)s) """ % {
                'err_msg': self.err_msg,
              }

    def __str__(self):
        return self.get_error()

