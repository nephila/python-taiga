import json
import requests
import time
from . import exceptions, utils
from distutils.version import LooseVersion
from requests.exceptions import RequestException
from requests.packages.urllib3.exceptions import InsecureRequestWarning


def _requests_compatible_true():
    if LooseVersion(requests.__version__) >= LooseVersion('2.11.0'):
        return 'True'
    else:
        return True


class RequestCacheException(Exception):
    pass


class RequestCacheMissingException(RequestCacheException):
    pass


class RequestCacheInvalidException(RequestCacheException):
    pass


class RequestCache(object):

    def __init__(self, valid_time=60):
        self._valid_time = valid_time
        self._cache = {}

    def put(self, key, value):
        self._cache[key] = {
            'time': time.time(),
            'value': value
        }

    def remove(self, key):
        if key in self._cache:
            del self._cache[key]

    def get(self, key):
        if key not in self._cache:
            raise RequestCacheMissingException()
        if time.time() > self._cache[key]['time'] + self._valid_time:
            self.remove(key)
            raise RequestCacheInvalidException()
        return self._cache[key]['value']


class RequestMakerException(Exception):
    pass


class RequestMaker(object):

    def __init__(self,
                 api_path, host,
                 token,
                 token_type='Bearer',
                 tls_verify=True,
                 enable_pagination=True
                 ):
        self.api_path = api_path
        self.host = host
        self.token = token
        self.token_type = token_type
        self.tls_verify = tls_verify
        self.enable_pagination = enable_pagination
        self._cache = RequestCache()
        if not self.tls_verify:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    @property
    def cache(self):
        return self._cache

    def is_bad_response(self, response):
        return 400 <= response.status_code <= 500

    def headers(self, paginate=True):
        headers = {
            'Content-type': 'application/json',
            'Authorization': '{0} {1}'.format(self.token_type, self.token),
        }
        if self.enable_pagination and paginate:
            headers['x-lazy-pagination'] = _requests_compatible_true()
        else:
            headers['x-disable-pagination'] = _requests_compatible_true()
        return headers

    def urljoin(self, *parts):
        return utils.urljoin(*parts)

    def get_full_url(self, uri, query={}, **parameters):
        full_url = self.urljoin(
            self.host, self.api_path,
            uri.format(**parameters)
        )
        return full_url

    def get(self, uri, query={}, cache=False, paginate=True, **parameters):
        try:
            full_url = self.urljoin(
                self.host, self.api_path,
                uri.format(**parameters)
            )

            result = None

            if cache:
                try:
                    result = self._cache.get(full_url)
                except RequestCacheException:
                    pass

            if not result:
                result = requests.get(
                    full_url,
                    headers=self.headers(paginate),
                    params=query,
                    verify=self.tls_verify
                )
            if cache:
                self._cache.put(full_url, result)
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
                'Authorization': '{0} {1}'.format(self.token_type, self.token),
                'x-disable-pagination': _requests_compatible_true()
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
                files=files,
                verify=self.tls_verify
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
                params=query,
                verify=self.tls_verify
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
                params=query,
                verify=self.tls_verify
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
                params=query,
                verify=self.tls_verify
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
