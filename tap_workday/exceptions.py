class workdayError(Exception):
    """class representing Generic Http error."""

    def __init__(self, message=None, response=None):
        super().__init__(message)
        self.message = message
        self.response = response


class workdayBackoffError(workdayError):
    """class representing backoff error handling."""

    pass


class workdayBadRequestError(workdayError):
    """class representing 400 status code."""

    pass


class workdayUnauthorizedError(workdayError):
    """class representing 401 status code."""

    pass


class workdayForbiddenError(workdayError):
    """class representing 403 status code."""

    pass


class workdayNotFoundError(workdayError):
    """class representing 404 status code."""

    pass


class workdayConflictError(workdayError):
    """class representing 409 status code."""

    pass


class workdayUnprocessableEntityError(workdayBackoffError):
    """class representing 422 status code."""

    pass


class workdayRateLimitError(workdayBackoffError):
    """class representing 429 status code."""

    pass


class workdayInternalServerError(workdayBackoffError):
    """class representing 500 status code."""

    pass


class workdayNotImplementedError(workdayBackoffError):
    """class representing 501 status code."""

    pass


class workdayBadGatewayError(workdayBackoffError):
    """class representing 502 status code."""

    pass


class workdayServiceUnavailableError(workdayBackoffError):
    """class representing 503 status code."""

    pass


ERROR_CODE_EXCEPTION_MAPPING = {
    400: {
        "raise_exception": workdayBadRequestError,
        "message": "A validation exception has occurred.",
    },
    401: {
        "raise_exception": workdayUnauthorizedError,
        "message": "The access token provided is expired, revoked, malformed or invalid for other reasons.",
    },
    403: {
        "raise_exception": workdayForbiddenError,
        "message": "You are missing the following required scopes: read",
    },
    404: {
        "raise_exception": workdayNotFoundError,
        "message": "The resource you have specified cannot be found.",
    },
    409: {
        "raise_exception": workdayConflictError,
        "message": "The API request cannot be completed because the requested operation would conflict with an existing item.",
    },
    422: {
        "raise_exception": workdayUnprocessableEntityError,
        "message": "The request content itself is not processable by the server.",
    },
    429: {
        "raise_exception": workdayRateLimitError,
        "message": "The API rate limit for your organisation/application pairing has been exceeded.",
    },
    500: {
        "raise_exception": workdayInternalServerError,
        "message": "The server encountered an unexpected condition which prevented"
        " it from fulfilling the request.",
    },
    501: {
        "raise_exception": workdayNotImplementedError,
        "message": "The server does not support the functionality required to fulfill the request.",
    },
    502: {
        "raise_exception": workdayBadGatewayError,
        "message": "Server received an invalid response.",
    },
    503: {
        "raise_exception": workdayServiceUnavailableError,
        "message": "API service is currently unavailable.",
    },
}
