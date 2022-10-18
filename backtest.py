from decimal import Decimal

import pandas as pd

from nautilus_trader.backtest.data.providers import TestDataProvider
from nautilus_trader.backtest.data.providers import TestInstrumentProvider
from nautilus_trader.backtest.data.wranglers import TradeTickDataWrangler
from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.engine import BacktestEngineConfig
from nautilus_trader.examples.strategies.ema_cross_trailing_stop import EMACrossTrailingStop
from nautilus_trader.examples.strategies.ema_cross_trailing_stop import EMACrossTrailingStopConfig
from nautilus_trader.model.currencies import ETH
from nautilus_trader.model.currencies import USDT
from nautilus_trader.model.enums import AccountType
from nautilus_trader.model.enums import OMSType
from nautilus_trader.model.identifiers import Venue, InstrumentId
from nautilus_trader.model.objects import Money
from nautilus_trader.adapters.binance.common.enums import BinanceAccountType
from nautilus_trader.adapters.binance.factories import get_cached_binance_http_client
from nautilus_trader.adapters.binance.spot.providers import BinanceSpotInstrumentProvider
from nautilus_trader.common.clock import LiveClock
from nautilus_trader.common.logging import Logger
import asyncio
import os
import keys
from nautilus_trader.model.data.bar import Bar, BarType
from nautilus_trader.model.objects import Money
from nautilus_trader.model.objects import Price
from nautilus_trader.model.objects import Quantity
import json
from nautilus_trader.config import InstrumentProviderConfig


asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def parse_binance_candle_line(line, bar_type: BarType, instrument):
    ts_init = (int(line[0]) * 1000000)
    return Bar(
        bar_type=bar_type,
        open=Price(float(line[1]), precision=instrument.price_precision),
        high=Price(float(line[2]), precision=instrument.price_precision),
        low=Price(float(line[3]), precision=instrument.price_precision),
        close=Price(float(line[4]), precision=instrument.price_precision),
        volume=Quantity(float(line[6]), precision=instrument.size_precision),
        ts_init=ts_init,
        ts_event=ts_init,
    )

async def get_binance_spot_instruments():
        
        clock = LiveClock()

        client = get_cached_binance_http_client(
            loop=asyncio.get_event_loop(),
            clock=clock,
            logger=Logger(clock=clock),
            account_type=BinanceAccountType.SPOT,
            key=keys.key,
            secret=keys.secret,
            is_testnet=False,  # <-- add this argument to use the testnet
        )
        await client.connect()

        provider = BinanceSpotInstrumentProvider(
            client=client,
            logger=Logger(clock=clock),
            config=InstrumentProviderConfig(load_all=True)
        )

        await provider.load_all_async()

        print(provider.count)

        await client.disconnect()

        return provider

if __name__ == "__main__":
    # Configure backtest engine
    config = BacktestEngineConfig(trader_id="BACKTESTER-001")

    # Build the backtest engine
    engine = BacktestEngine(config=config)

    # Add a trading venue (multiple venues possible)
    BINANCE = Venue("BINANCE")
    engine.add_venue(
        venue=BINANCE,
        oms_type=OMSType.NETTING,
        account_type=AccountType.CASH,  # Spot CASH account (not for perpetuals or futures)
        base_currency=None,  # Multi-currency account
        starting_balances=[Money(1_000_000, USDT), Money(10, ETH)],
    )
        
    provider = asyncio.new_event_loop().run_until_complete(get_binance_spot_instruments())

    # Add instruments to engine

    ethusdt = InstrumentId.from_str("ETHUSDT.BINANCE")
    ETHUSDT_BINANCE = provider.find(instrument_id = ethusdt)
    engine.add_instrument(ETHUSDT_BINANCE)

    # Associate data with instruments

    source_address = open(r"C:\Users\Anonymous\Documents\Data Analysis\Backtesting - Final\Final\Backtesting\USDT-Data\ETHUSDT.BINANCE.json")
    data_source = json.load(source_address)

    bartype_source = BarType.from_str("ETHUSDT.BINANCE-1-MINUTE-LAST-EXTERNAL")
    
    bars = [
    parse_binance_candle_line(line=line, bar_type=bartype_source, instrument=ETHUSDT_BINANCE)
    for line in data_source
    ]

    engine.add_data(bars)
   

    # Configure your strategy
    config = EMACrossTrailingStopConfig(
        instrument_id=str(ETHUSDT_BINANCE.id),
        bar_type="ETHUSDT.BINANCE-1-MINUTE-LAST-EXTERNAL",
        trade_size=Decimal("0.05"),
        fast_ema=10,
        slow_ema=20,
        atr_period=20,
        trailing_atr_multiple=3.0,
        trailing_offset_type="PRICE",
        trigger_type="LAST",
    )
    # Instantiate and add your strategy
    strategy = EMACrossTrailingStop(config=config)
    engine.add_strategy(strategy=strategy)

    input("Press Enter to continue...")  # noqa (always Python 3)

    # Run the engine (from start to end of data)
    engine.run()

    # Optionally view reports
    with pd.option_context(
        "display.max_rows",
        100,
        "display.max_columns",
        None,
        "display.width",
        300,
    ):
        print(engine.trader.generate_account_report(BINANCE))
        print(engine.trader.generate_order_fills_report())
        print(engine.trader.generate_positions_report())

    # For repeated backtest runs make sure to reset the engine
    engine.reset()

    # Good practice to dispose of the object
    engine.dispose()