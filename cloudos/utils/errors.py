"""
Specific classes to handle errors.
"""

import json


class BadRequestException(Exception):
    """Handle bad request exceptions and shows improved messages.

    Parameters
    ----------
    rv : request variable
        The request variable returned that caused the error.
    """
    def __init__(self, rv):
        msg = "Server returned status {}. Response:\n{}".format(
                    rv.status_code, json.dumps(rv.json())
                )
        super(BadRequestException, self).__init__(msg)
        self.rv = rv


class TimeOutException(Exception):
    """Handle TimeOut exceptions and shows improved messages.

    Parameters
    ----------
    rv : request variable
        The request variable returned that caused the error.
    """
    def __init__(self, rv):
        msg = ("Server exceeded the max time to process request. " +
               "Response:\n{}".format(json.dumps(rv)))
        super(TimeOutException, self).__init__(msg)
        self.rv = rv
