# Nautilus-Trader-Example
Confused on how to use Nautilus? No stress fam

Nautilus is generally a fairly complex package and will require you to understand a number of underlying packages including asyncio (hell).

Main.py contains the core backtesting code. Keys.py should contain your API keys for the Binance SPOT LIVE exchange (do not use testnet keys, it won't work because testnet does not have a function to request instrumetns).

Finally, ETHUSDT.BINANCE.JSON contains a very small number of bars for the ETH-USDT pair. This data is actually from OKX but is renamed to work here.

This strategy does a silly EMA Cross. But more importantly, shows you how to use the live exchange API to get instruments but then associate that with local data for backtesting.

This is the most sustainable approach to using Nautilus IMO because instruments are such an important (read: annoying) component of Nautilus and messing them up will destroy everything. So importing live from the API is the best approach, then you can associate them with local bar or tick data.
