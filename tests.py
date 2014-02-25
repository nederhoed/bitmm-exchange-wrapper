from unittest import TestCase

import json
import requests
import httplib
import decimal

from bitmm.xwrap import client


class XWrapTestBase(TestCase):
    def setUp(self):
        self._org_get = requests.get
        self._org_post = requests.post
        self._org_put = requests.put

        requests.get = self._get
        requests.post = self._post
        requests.put = self._put

        # fill these for each request
        self.responses = []
        # request tests are optional, add None to skip for one request
        self.request_tests = []

    def _get(self, url, **kwargs):
        return self._request(url, 'get', **kwargs)

    def _post(self, url, data, **kwargs):
        return self._request(url, 'post', **kwargs)

    def _put(self, url, data, **kwargs):
        return self._request(url, 'put', **kwargs)

    def _request(self, url, method, **kwargs):
        if self.request_tests:
            test = self.request_tests.pop(0)
            if test is not None:
                test(url, method, kwargs)
        status, headers, body = self.responses.pop(0)
        response = requests.Response()
        response.status_code = status
        response.reason = httplib.responses[status]
        response._content = body
        return response


class XWrapTestCase(XWrapTestBase):
    def setUp(self):
        super(XWrapTestCase, self).setUp()
        self.client = c = client.XWrap()
        self.account = c.account('foo', 'bar')

    def test_balance(self):
        self.responses = [
            (200, {'Content-Type': 'application/json'},
                json.dumps([
                    {'exchange': 'mtgox',
                        'balance': {
                            'EUR': '100.10',
                            'BTC': '2.0',
                        },
                    },
                    {'exchange': 'bitstamp',
                        'balance': {
                            'USD': '1000.10',
                            'BTC': '2.1',
                        },
                    },
                ])),
        ]
        balance = self.account.balance()
        self.assertEquals(len(balance), 2)
        self.assertEquals(
            balance[0], {
                'exchange': 'mtgox',
                'balance': {
                    'EUR': decimal.Decimal('100.10'),
                    'BTC': decimal.Decimal('2.0'),
                },
            })
        self.assertEquals(
            balance[1], {
                'exchange': 'bitstamp',
                'balance': {
                    'USD': decimal.Decimal('1000.1'),
                    'BTC': decimal.Decimal('2.1'),
                },
            })

    def test_list_exchanges(self):
        self.responses = [
            (200, {'Content-Type': 'application/json'}, json.dumps([
                {'id': 'dummy',
                    'name': 'Dummy',
                    'description': 'Dummy exchange for testing purposes'},
                {'id': 'mtgox',
                    'name': 'MtGox',
                    'description': 'MtGox exchange'},
            ])),
        ]
        exchanges = self.client.list_exchanges()
        self.assertEquals(len(exchanges), 2)
        self.assertEquals(exchanges[0]['id'], 'dummy')
        self.assertEquals(exchanges[1]['id'], 'mtgox')

    def test_exchange_rates(self):
        self.responses = [
            (200, {'Content-Type': 'application/json'}, json.dumps([{
                    'exchange': 'Test',
                    'buy': '0.123',
                    'sell': '0.120',
                }])),
        ]
        result = self.account.exchange_rates('EURBTC')
        self.assertEquals(
            result, [{
                'exchange': 'Test',
                'buy': decimal.Decimal('0.123'),
                'sell': decimal.Decimal('0.120'),
            }])

        self.responses = [
            (500, {}, 'Something went wrong'),
        ]
        self.assertRaises(
            client.APIError, self.account.exchange_rates, '')

    def test_list_backends(self):
        account = self.client.account('','')
        self.responses = [
            (401, {}, '{"detail": "Authentication creds missing"}'),
        ]
        self.assertRaises(
            client.APIError, account.list_backends, '', '')

        self.responses = [
            (200, {'Content-Type': 'application/json'}, json.dumps([
                {'id': 1,
                    'account': 1,
                    'username': '',
                    'apikey': 'apikey',
                    'apisecret': '<hidden>',
                    'enabled': True,
                    'available': True,
                    'exchange': 'dummy',
                    'url': 'http://example.com/exchanges/1/',
                    'exchange_rate_url':
                        'http://example.com/exchanges/1/exchange_rate',
                }])),
        ]
        result = self.account.list_backends()
        self.assertEquals(len(result), 1)
        self.assert_(isinstance(result[0], client.Backend))
        self.assertEquals(result[0].exchange, 'dummy')

    def test_backend(self):
        self.responses = [
            (200, {'Content-Type': 'application/json'},
                json.dumps({
                    'id': 1,
                    'account': 1,
                    'username': '',
                    'apikey': 'apikey',
                    'apisecret': '<hidden>',
                    'enabled': True,
                    'available': True,
                    'exchange': 'dummy',
                })),
        ]
        backend = self.account.backend(1)
        self.assertEquals(backend.id, 1)
        self.assertEquals(backend.apikey, 'foo')
        self.assertEquals(backend.apisecret, 'bar')

    def test_backend_balance(self):
        self.responses = [
            (200, {'Content-Type': 'application/json'},
                json.dumps({
                    'id': 1,
                    'account': 1,
                    'username': '',
                    'apikey': 'apikey',
                    'apisecret': '<hidden>',
                    'enabled': True,
                    'available': True,
                    'exchange': 'bitstamp',
                })),
            (200, {'Content-Type': 'application/json'},
                json.dumps({
                    'BTC': '1.1',
                    'USD': '1000.20',
                })),
        ]
        backend = self.account.backend(1)
        balance = backend.balance()
        self.assertEquals(
            balance,
            {'USD': decimal.Decimal('1000.20'),
                'BTC': decimal.Decimal('1.1')})


if __name__ == '__main__':
    from unittest import main
    main()
