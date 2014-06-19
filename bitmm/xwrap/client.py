import urllib
import requests
import json
import decimal
import datetime

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
        if response.get(
                'content-type', '').startswith('application/json'):
            error = json.loads(response.content)
        else:
            error = response.reason
        raise APIError(error)
    content = None
    if response.content:
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
        return self._call('supported-exchanges/')

    def account(self, username, password):
        return Account(username, password, baseurl=self.baseurl)

    def _call(self, path, method='get', **kwargs):
        if path.startswith('/'):
            path = path[1:]
        url = '%s/%s' % (self.baseurl, path)
        return call(url, method, **kwargs)


class Account(object):
    def __init__(self, username, password, baseurl=XWRAP_URL):
        self.username = username
        self.password = password
        if baseurl.endswith('/'):
            baseurl = baseurl[:-1]
        self.baseurl = baseurl

    def exchange_rates(self, assetpair):
        """Returns a list of exchange rates for all supported back-ends
        """
        response = self._call(
            'exchange-rate/%s/' % (urllib.quote(assetpair),))
        ret = []
        for rateinfo in response:
            ret.append({
                'exchange': rateinfo['exchange'],
                'buy': decimal.Decimal(rateinfo['buy']),
                'sell': decimal.Decimal(rateinfo['sell']),
            })
        return ret

    def balance(self):
        """Returns the balance for each exchange back-end
        """
        ret = self._call('balance/')
        for entry in ret:
            for key, value in entry['balance'].items():
                entry['balance'][key] = decimal.Decimal(value)
        return ret

    def list_backends(self, exchange=None, only_enabled=True):
        """Returns a list of backends for the user
        """
        ret = []
        for backend in self._call('exchange/'):
            if only_enabled and not backend['enabled']:
                continue
            if exchange is None or exchange == backend['exchange']:
                ret.append(Backend(
                    backend['id'], self.username, self.password,
                    backend['exchange'], backend['apikey'],
                    backend['enabled'], backend['available'],
                    self.baseurl))
        return ret

    def create_backend(
            self, exchange, uname, key, secret):
        ret = self._call(
            'exchange/', method='post',
            data={
                'account': username,
                'exchange': exchange,
                'username': uname,
                'apikey': key,
                'apisecret': secret,
            })
        return Backend(
            ret['id'], self.username, self.password, ret['exchange'],
            ret['apikey'], ret['enabled'], ret['available'],
            baseurl=self.baseurl)

    def backend(self, id):
        """Retrieve a backend by id
        """
        data = self._call('exchange/%s/' % (id,))
        return Backend(
            id, self.username, self.password,
            data['exchange'], data['apikey'],
            data['enabled'], data['available'],
            baseurl=self.baseurl)

    def _call(self, path, method='get', **kwargs):
        if path.startswith('/'):
            path = path[1:]
        url = '%s/account/%s' % (self.baseurl, path)
        return call(url, method, self.username, self.password, **kwargs)


class Backend(object):
    def __init__(
            self, id, username, password, exchange='unknown',
            apikey='unknown', enabled=True, available=True,
            baseurl=XWRAP_URL):
        self.id = id
        self.username = username
        self.password = password
        self.exchange = exchange
        self.enabled = enabled
        self.available = available
        if baseurl.endswith('/'):
            baseurl = baseurl[:-1]
        self.baseurl = baseurl

    def balance(self):
        """Returns balance information for this back-end
        """
        ret = self._call('balance/')
        for key, value in ret.items():
            ret[key] = decimal.Decimal(value)
        return ret

    def exchange_rate(self, assetpair):
        """Returns exchange rate information for this back-end
        """
        data = self._call('exchange_rate/%s/' % (urllib.quote(assetpair),))
        return {
            'buy': decimal.Decimal(data['buy']),
            'sell': decimal.Decimal(data['sell']),
        }

    def withdraw_limits(self):
        data = self._call('withdraw_limits/')
        if data is None:
            return None
        for key, value in data.iteritems():
            data[key] = decimal.Decimal(value)
        return data

    def buy(self, assetpair, amount):
        """Buy assets at this back-end
        """
        return self._call(
            'buy/%s/' % (urllib.quote(assetpair),), 'post',
            amount=str(decimal.Decimal(amount)))

    def sell(self, assetpair, amount):
        """Sell assets at this back-end
        """
        return self._call(
            'sell/%s/' % (urllib.quote(assetpair),), 'post',
            amount=str(decimal.Decimal(amount)))

    def send_to_address(self, asset, amount, address):
        """Send assets to a certain address
        """
        return self._call(
            'send/%s/' % (urllib.quote(asset),), 'post',
            amount=str(decimal.Decimal(amount)),
            address=address)

    def get_address(self, asset):
        """Return a Bitcoin address for the account

        Depending on the exchange this returns either a new or an existing
        address.
        """
        return self._call('get_address/%s/' % (urllib.quote(asset),))

    def _call(self, path, method='get', **kwargs):
        url = '%s/account/exchange/%s/%s' % (self.baseurl, self.id, path)
        return call(url, method, self.username, self.password, data=kwargs)
