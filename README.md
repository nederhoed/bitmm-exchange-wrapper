bitmm-exchange-wrapper
======================

THIS MODULE IS NOT YET READY FOR USE.

Python implementation of the Bitmymoney Exchange Wrapper

Talk from your Python program with the Bitmymoney Exchange Wrapper (XWrap). By using XWrap, you have a consistent interface to trade on multiple Crypto exchanges.

We currently support:
* Bitstamp (USD/BTC)
* MtGox (USD/BTC, EUR/BTC)

We plan to add implementations for:
* Bitcoin Central
* BTC-e
* Kraken
* Vircurex

We welcome suggestions for other exchanges to be added.

## API key security
You will need to register you own Exchange API keys with each exchange. Only add "account info" and "trade" permissions to the API keys you provide. This will ensure nobody will be able to withdraw money, in case your keys gets compromised.
