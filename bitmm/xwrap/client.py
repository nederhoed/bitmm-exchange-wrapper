import urllib
import requests
import json
import decimal
import datetime

import mtgoxexp

def toqs(data):
    """Convert a dict to a (GET) query string
    """
    ret = []
    for key, value in data.iteritems():
        if type(value) not in (list, tuple):
            value = [value]
        for subvalue in value:
            ret.append('%s=%s' % (urllib.quote(key), urllib.quote(subvalue)))
    return '&'.join(ret)


class APIError(Exception):
    """Raised when something went wrong on the server
    """


def call(url, method='get', username=None, password=None, data=None):
    kwargs = {}
    if data is not None:
        data = toqs(data)
        if method.lower() == 'post':
            kwargs['data'] = data
            kwargs['headers'] = {
                'Content-Type': 'application/x-www-form-urlencoded'}
        elif '?' in url:
            url = '%s&%s' % (url, data)
        else:
            url = '%s?%s' % (url, data)
    if username:
        kwargs['auth'] = (username, password)
    reqmethod = getattr(requests, method)
    response = reqmethod(url, **kwargs)
    if response.status_code >= 500:
        # server error, we assume no JSON has been returned
        raise APIError(response.content or response.reason)
    content = json.loads(response.content)
    if response.status_code < 200 or response.status_code >= 400:
        raise APIError(content['detail'])
    return content


class XWrap(object):
    def __init__(self, baseurl='http://localhost:8000'):
        if baseurl.endswith('/'):
            baseurl = baseurl[:-1]
        self.baseurl = baseurl

    def list_exchanges(self):
        """Returns a list of all supported exchange back-ends
        """
        return self._call('/list_exchanges/')

    def balance(self, username, password):
        """Returns the balance for each exchange back-end
        """
        ret = self._call('balance', username=username, password=password)
        for entry in ret:
            for key, value in entry['balance'].items():
                entry['balance'][key] = decimal.Decimal(value)
        return ret

    def exchange_rates(self, currency, asset):
        """Returns a list of exchange rates for all supported back-ends
        """
        response = self._call(
            '/exchange_rates/?from=%s&to=%s' % (
                urllib.quote(currency), urllib.quote(asset)))
        ret = []
        for rateinfo in response:
            ret.append({
                'id': rateinfo['id'],
                'exchange': rateinfo['exchange'],
                'buy': decimal.Decimal(rateinfo['buy']),
                'sell': decimal.Decimal(rateinfo['sell']),
            })
        return ret

    def list_backends(
            self, username, password, exchange=None, active_only=True):
        """Returns a list of backends for the user
        """
        ret = []
        for backend in self._call(
                'exchanges/', username=username, password=password):
            if exchange is None or exchange == backend['exchange']:
                ret.append(Backend(
                    backend['id'], username, password,
                    backend['exchange'], backend['username'],
                    backend['apikey'], self.baseurl))
        return ret

    def create_backend(
            self, username, password, exchange, uname, key, secret):
        return self._call(
            'exchanges/', method='post',
            username=username, password=password,
            data={
                'account': username,
                'exchange': exchange,
                'username': uname,
                'apikey': key,
                'apisecret': secret,
            })

    def backend(self, id, username, password):
        """Retrieve a backend by id
        """
        data = self._call(
            'exchanges/%s' % (id,), username=username, password=password)
        return Backend(
            id, username, password, apiusername=data['username'],
            apikey=data['apikey'], baseurl=self.baseurl)

    def _call(
            self, path, method='get', username=None, password=None, **kwargs):
        if path.startswith('/'):
            path = path[1:]
        url = '%s/%s' % (self.baseurl, path)
        return call(url, method, username, password, **kwargs)


class Backend(object):
    def __init__(
            self, id, username, password, exchange=None,
            apiusername=None, apikey=None,
            baseurl='http://localhost:8000'):
        self.id = id
        self.username = username
        self.password = password
        self.exchange = exchange
        self.apiusername = apiusername
        self.apikey = apikey
        if baseurl.endswith('/'):
            baseurl = baseurl[:-1]
        self.baseurl = baseurl

    def balance(self):
        """Returns balance information for this back-end
        """
        ret = self._call('balance')
        for key, value in ret.items():
            ret[key] = decimal.Decimal(value)
        return ret

    def exchange_rate(self, currency, asset):
        """Returns exchange rate information for this back-end
        """
        return self._call('exchange_rate', **{'from': currency, 'to': asset})

    def buy(self, currency, asset, amount):
        """Buy bitcoins at this back-end
        """

    def sell(self, currency, asset, amount):
        """Sell bitcoins at this back-end
        """

    def _call(
            self, path, method='get', username=None, password=None, **kwargs):
        url = '%s/exchanges/%s/%s' % (self.baseurl, self.id, path)
        return call(url, method, self.username, self.password, data=kwargs)
