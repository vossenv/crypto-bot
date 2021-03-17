from datetime import datetime
from http import HTTPStatus


class ApiError(Exception):
    status_code = 400
    __name__ = "ApiError"

    def __init__(self, message=None, error=None, status_code=None, payload=None):
        Exception.__init__(self)
        if isinstance(error, Exception):
            self.error_msg = str(error)

        self.args = self.message = (message,)
        self.status_code = status_code
        self.payload = payload
        self.timestamp = datetime.now()

    def serialize(self):
        rv = dict(self.payload or ())

        if self.status_code:
            rv['status_code'] = str(self.status_code)
            rv['reply'] = HTTPStatus(self.status_code).phrase

        if self.message:
            rv['message'] = self.message

        if hasattr(self, 'error'):
            rv['error'] = self.error
            rv['error_message'] = self.error_msg
        rv['timestamp'] = str(self.timestamp)
        return rv
