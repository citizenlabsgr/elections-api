from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class ServiceUnavailable(APIException):
    status_code = 503
    default_code = "service_unavailable"
    default_detail = "The Michigan Secretary of State website is temporarily unavailable, please try again later."

    def __init__(self, detail=None, code=None):
        super().__init__(detail, code)
        self.headers = {"Retry-After": "60"}


class UnhandledData(RuntimeError):
    pass


class MissingData(RuntimeError):
    pass


class DuplicateData(RuntimeError):
    pass


def custom_exception_handler(exc, context):
    """Add custom headers to the error response."""
    response = exception_handler(exc, context)

    if isinstance(exc, ServiceUnavailable) and response is not None:
        for header, value in exc.headers.items():
            response[header] = value

    return response
