import json


class TaigaException(Exception):
    pass


class TaigaRestException(TaigaException):
    def __init__(self, uri, status_code, message="", method="GET"):
        self.uri = uri
        self.status_code = status_code
        self.method = method
        try:
            json_message = json.loads(message)
            if "_error_message" in json_message:
                message = json_message["_error_message"]
        except ValueError:
            pass
        if not message:
            message = "Status: {} on URI: {}".format(status_code, uri)
        super().__init__(message)
