import json
import requests
from . import exceptions
from requests.exceptions import RequestException


class RequestMakerException(Exception):
    pass


class RequestMaker(object):

    def __init__(self, api_path, host, token):
        self.api_path = api_path
        self.host = host
        self.token = token

    def is_bad_response(self, response):
        return 400 <= response.status_code <= 500

    def headers(self):
        headers = {
            'Content-type': 'application/json',
            'Authorization': 'Bearer {0}'.format(self.token),
            'x-disable-pagination': True
        }
        return headers

    def urljoin(self, *parts):
        return '/'.join(part.strip('/') for part in parts)

    def get(self, uri, query={}, **parameters):
        try:
            full_url = self.urljoin(
                self.host, self.api_path,
                uri.format(**parameters)
            )
            result = requests.get(
                full_url,
                headers=self.headers(),
                params=query
            )
        except RequestException:
            raise exceptions.TaigaRestException(
                full_url, 400,
                'Network error!', 'GET'
            )
        if not self.is_bad_response(result):
            return result
        else:
            raise exceptions.TaigaRestException(
                full_url, result.status_code,
                result.text, 'GET'
            )

    def post(self, uri, payload=None, query={}, files={}, **parameters):
        if files:
            headers = {
                'Authorization': 'Bearer {0}'.format(self.token),
                'x-disable-pagination': True
            }
            data = payload
        else:
            headers = self.headers()
            data = json.dumps(payload)
        try:
            full_url = self.urljoin(
                self.host, self.api_path,
                uri.format(**parameters)
            )
            result = requests.post(
                full_url,
                headers=headers,
                data=data,
                params=query,
                files=files
            )
        except RequestException:
            raise exceptions.TaigaRestException(
                full_url, 400,
                'Network error!', 'POST'
            )
        if not self.is_bad_response(result):
            return result
        else:
            raise exceptions.TaigaRestException(
                full_url, result.status_code,
                result.text, 'POST'
            )

    def delete(self, uri, query={}, **parameters):
        try:
            full_url = self.urljoin(
                self.host, self.api_path,
                uri.format(**parameters)
            )
            result = requests.delete(
                full_url,
                headers=self.headers(),
                params=query
            )
        except RequestException:
            raise exceptions.TaigaRestException(
                full_url, 400,
                'Network error!', 'DELETE'
            )
        if not self.is_bad_response(result):
            return result
        else:
            raise exceptions.TaigaRestException(
                full_url, result.status_code,
                result.text, 'DELETE'
            )

    def put(self, uri, payload=None, query={}, **parameters):
        try:
            full_url = self.urljoin(
                self.host, self.api_path,
                uri.format(**parameters)
            )
            result = requests.put(
                full_url,
                headers=self.headers(),
                data=json.dumps(payload),
                params=query
            )
        except RequestException:
            raise exceptions.TaigaRestException(
                full_url, 400,
                'Network error!', 'PUT'
            )
        if not self.is_bad_response(result):
            return result
        else:
            raise exceptions.TaigaRestException(
                full_url, result.status_code,
                result.text, 'PUT'
            )

    def patch(self, uri, payload=None, query={}, **parameters):
        try:
            full_url = self.urljoin(
                self.host, self.api_path,
                uri.format(**parameters)
            )
            result = requests.patch(
                full_url,
                headers=self.headers(),
                data=json.dumps(payload),
                params=query
            )
        except RequestException:
            raise exceptions.TaigaRestException(
                full_url, 400,
                'Network error!', 'PATCH'
            )
        if not self.is_bad_response(result):
            return result
        else:
            raise exceptions.TaigaRestException(
                full_url, result.status_code,
                result.text, 'PATCH'
            )
