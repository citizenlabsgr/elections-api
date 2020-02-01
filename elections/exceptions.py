from rest_framework.exceptions import APIException


class ServiceUnavailable(APIException):
    status_code = 503
    default_code = 'service_unavailable'
    default_detail = f'The Michigan Secretary of State website is temporarily unavailable, please try again later.'


class UnhandledData(RuntimeError):
    pass


class MissingData(RuntimeError):
    pass
