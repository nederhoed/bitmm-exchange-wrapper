bitmm-exchange-wrapper
======================

THIS MODULE IS NOT YET READY FOR USE.

Python implementation of the Bitmymoney Exchange Wrapper

Talk from your Python program with the Bitmymoney Exchange Wrapper (XWrap). By
using XWrap, you have a consistent interface to trade on multiple Crypto
exchanges.

We currently support:
* Bitstamp (USD/BTC)
* MtGox (USD/BTC, EUR/BTC)

We plan to add implementations for:
* Bitcoin Central
* BTC-e
* Kraken
* Vircurex

We welcome suggestions for other exchanges to be added.

## Example

An example of how to use the api:

    >>> from bitmm.xwrap.client import XWrap
    >>> xw = XWrap()
    # list all exchanges that can be traded against
    >>> xw.list_exchanges()
    [...]
    # list all of our own backends (exchange registrations) on xwrap
    >>> xw.list_backends('username', 'password')
    [...]
    # retrieve a backend by id
    >>> backend = xw.backend(123, 'username', 'password')
    # backend contains account-specific functionality
    >>> backend.balance()
    {...}
    >>> backend.buy('USD', 'BTC', 1)

## API key security (WIP)

You will need to register you own Exchange API keys with each exchange. Only
add "account info" and "trade" permissions to the API keys you provide. This
will ensure nobody will be able to withdraw money, in case your keys gets
compromised. Note that to register said keys, you will need to create an
account on the exchange wrapper (or have one created for you).

## API reference

The API provides 2 classes, 'XWrap' allows you to perform general actions
such as retrieving all available exchanges, exchange rates for each exchange,
and your back-ends, and 'Backend' allows performing account-specific actions,
so actions on single exchanges you have registered at the exchange wrapper.

If anything goes wrong, an APIError is raised with the reason, which is a
human-readable error if it can be extracted, but may also just be 'server
error' if there's no additional information available.

### XWrap([baseurl])

Create a new interface to the exchange wrapper. The baseurl by default it set
to the main XWrap server.

#### XWrap.list_exchanges()

Returns a list of all exchanges supported by the exchange wrapper. Returns
a list of dicts, each of which has keys 'id' (a string identifying the
exchange, e.g. 'mtgox' or 'bitstamp'), 'name' (a string containing a
human-readable name for the exchange, e.g. 'MtGox' or 'Bitstamp') and
'description' (a human-readable description of the exchange).

#### XWrap.exchange_rates(currency, asset)

Returns exchange rate information for all exchanges. The 'currency' argument
should be a supported currency, as string (e.g. 'EUR', 'USD'), the 'asset'
argument a supported crypto-currency (e.g. 'BTC'). Return value is a list
of dicts, each of which has keys 'exchange' (a string identifying the exchange,
same as the id in the dicts returned by list_exchanges()), 'buy' (Decimal value
of the current buy price of one bitcoin) and 'sell' (Decimal value of the
current selling price of one bitcoin).

#### XWrap.balance(username, password)

Returns your balance of all your accounts. Return value is a list of dicts,
each of which has keys 'id' (integer id of the exchange registration on your
account),'exchange' (the exchange id as a string, same as the 'id' in the
list_exchanges() dicts), and 'balance' (dict with each currency supported by
the exchange as key and the current balance as Decimal value).

#### XWrap.list_backends(username, password[, exchange][, active_only])

Returns information about your registered backends. Use 'exchange' and
'active_only' to filter. Return value is a list of Backend objects for
your account (see Backend object API below).

#### XWrap.create_backend(username, password, exchange, uname, key, secret)

Create a new backend. Username and password are user credentials for the
exchange wrapper, 'exchange' is a string with the exchange id as provided by
'list_exchanges()', 'uname' the username (if required) on the remote exchange,
should be left empty if the exchange doesn't require one, and 'apikey' and
'apisecret' are the key and secret for the exchange APIs as strings.

Returns the full created structure on success, see 'list_backends()' for more
information about the structure.

#### XWrap.backend(id, username, password)

Returns a single Backend object, retrieved by id (integer) and user credentials
for the exchange wrapper.

### Backend(id, username, password[, baseurl])

Create a new Backend instance. Note that generally you will want to use
XWrap.backend() or XWrap.list_backends() to get a Backend instance, though
it's not impossible to instantiate one yourself.

#### Backend.balance()

Returns a dict with as keys all the currencies supported by this backend,
and as values the current account balance on the exchange, as Decimal.

#### Backend.exchange_rate(currency, asset)

Returns a dict with keys 'buy' and 'sell' and as values respectively the buy
and sell value of a single bitcoin, as Decimal.

#### Backend.buy(currency, asset, amount)

Buy 'amount' (Decimal) of 'asset' (crypto-currency string, e.g. 'BTC') using
'currency' (currency string, e.g. 'EUR' or 'USD') against the current buy
price.

#### Backend.sell(currency, asset, amount)

Sell 'amount' (Decimal) of 'asset' (crypto-currency string, e.g. 'BTC') using
'currency' (currency string, e.g. 'EUR' or 'USD') for the current sell price.

#### Backend.send_to_address(asset, amount, address)

Send 'amount' (Decimal) of 'asset' (crypto-currency string, e.g. 'BTC') to
'address' (a valid crypto-currency address). Returns True if the action
was successful.

#### Backend.get_address()

Returns a crypto-currency address attached to your account on the back-end.
Depending on the back-end, this may return a uniquely created address, or
a single address if creating unique addresses is not supported by the
back-end's API.
