import urllib
import requests
import json
import decimal
import datetime

import mtgoxexp

XWRAP_URL = 'http://localhost:8000'

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
        if response.headers['content-type'] == 'application/json':
            error = json.loads(response.content)
        else:
            error = response.reason
        raise APIError(error)
    content = json.loads(response.content)
    if response.status_code < 200 or response.status_code >= 400:
        raise APIError(content['detail'])
    return content


class XWrap(object):
    def __init__(self, baseurl=XWRAP_URL):
        if baseurl.endswith('/'):
            baseurl = baseurl[:-1]
        self.baseurl = baseurl

    def list_exchanges(self):
        """Returns a list of all supported exchange back-ends
        """
        return self._call('/list_exchanges/')

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

    def balance(self, username, password):
        """Returns the balance for each exchange back-end
        """
        ret = self._call('balance', username=username, password=password)
        for entry in ret:
            for key, value in entry['balance'].items():
                entry['balance'][key] = decimal.Decimal(value)
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
                    backend['id'], username, password, backend['exchange'],
                    self.baseurl))
        return ret

    def create_backend(
            self, username, password, exchange, uname, key, secret):
        ret = self._call(
            'exchanges/', method='post',
            username=username, password=password,
            data={
                'account': username,
                'exchange': exchange,
                'username': uname,
                'apikey': key,
                'apisecret': secret,
            })
        return Backend(ret['id'], username, password, ret['exchange'])

    def backend(self, id, username, password):
        """Retrieve a backend by id
        """
        data = self._call(
            'exchanges/%s' % (id,), username=username, password=password)
        return Backend(
            id, username, password, data['exchange'], baseurl=self.baseurl)

    def _call(
            self, path, method='get', username=None, password=None, **kwargs):
        if path.startswith('/'):
            path = path[1:]
        url = '%s/%s' % (self.baseurl, path)
        return call(url, method, username, password, **kwargs)


class Backend(object):
    def __init__(
            self, id, username, password, exchange='unknown',
            baseurl=XWRAP_URL):
        self.id = id
        self.username = username
        self.password = password
        self.exchange = exchange
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
        """Buy assets at this back-end
        """
        return self._call(
            'buy', 'post', currency=currency, asset=asset,
            amount=str(decimal.Decimal(amount)))

    def sell(self, currency, asset, amount):
        """Sell assets at this back-end
        """
        return self._call(
            'sell', 'post', currency=currency, asset=asset,
            amount=str(decimal.Decimal(amount)))

    def send_to_address(self, asset, amount, address):
        """Send assets to a certain address
        """
        return self._call(
            'send_to_address', 'post', asset=asset,
            amount=str(decimal.Decimal(amount)),
            address=address)

    def get_address(self):
        """Return a Bitcoin address for the account

        Depending on the exchange this returns either a new or an existing
        address.
        """
        return self._call('get_address')

    def _call(self, path, method='get', **kwargs):
        url = '%s/exchanges/%s/%s' % (self.baseurl, self.id, path)
        return call(url, method, self.username, self.password, data=kwargs)
