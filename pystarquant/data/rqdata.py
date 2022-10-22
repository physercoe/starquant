from datetime import datetime, timedelta
from typing import List

from rqdatac import init as rqdata_init
from rqdatac.services.basic import all_instruments as rqdata_all_instruments
from rqdatac.services.get_price import get_price as rqdata_get_price

from pystarquant.common.config import SETTINGS
from pystarquant.common.datastruct import BarData, TickData,HistoryRequest
from pystarquant.common.constant import Exchange, Interval
from pystarquant.common.utility import generate_full_symbol

INTERVAL_VT2RQ = {
    'tick':'tick',
    '1m': "1m",
    '1h': "60m",
    'd': "1d",
}

INTERVAL_ADJUSTMENT_MAP = {
    'tick':timedelta(),
    '1m': timedelta(minutes=1),
    '1h': timedelta(hours=1),
    'd': timedelta()         # no need to adjust for daily bar
}


class RqdataClient:
    """
    Client for querying history data from RQData.
    """

    def __init__(self):
        """"""
        self.username = SETTINGS["rqdata.username"]
        self.password = SETTINGS["rqdata.password"]

        self.inited = False
        self.symbols = set()

    def init(self):
        """"""
        if self.inited:
            return True

        if not self.username or not self.password:
            return False

        rqdata_init(self.username, self.password,
                    ('rqdatad-pro.ricequant.com', 16011))

        try:
            df = rqdata_all_instruments(date=datetime.now())
            for ix, row in df.iterrows():
                self.symbols.add(row['order_book_id'])
        except RuntimeError:
            return False

        self.inited = True
        return True

    def to_rq_symbol(self, symbol: str, exchange: Exchange):
        """
        CZCE product of RQData has symbol like "TA1905" while
        vt symbol is "TA905.CZCE" so need to add "1" in symbol.
        """
        if exchange in [Exchange.SSE, Exchange.SZSE]:
            if exchange == Exchange.SSE:
                rq_symbol = f"{symbol}.XSHG"
            else:
                rq_symbol = f"{symbol}.XSHE"
        else:
            if exchange is not Exchange.CZCE or symbol.endswith('88'):
                return symbol.upper()

            for count, word in enumerate(symbol):
                if word.isdigit():
                    break

            # noinspection PyUnboundLocalVariable
            product = symbol[:count]
            year = symbol[count]
            month = symbol[count + 1:]

            if year == "9":
                year = "1" + year
            else:
                year = "2" + year

            rq_symbol = f"{product}{year}{month}".upper()

        return rq_symbol

    def query_bar(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        start: datetime,
        end: datetime
    ):
        """
        Query bar data from RQData.
        """
        rq_symbol = self.to_rq_symbol(symbol, exchange)
        if rq_symbol not in self.symbols:
            return None

        end += timedelta(1)     # For querying night trading period data

        df = rqdata_get_price(
            rq_symbol,
            frequency=interval.value,
            fields=["open", "high", "low", "close", "volume","open_interest"],
            start_date=start,
            end_date=end
        )

        data: List[BarData] = []
        for ix, row in df.iterrows():
            bar = BarData(
                symbol=symbol,
                exchange=exchange,
                interval=interval,
                datetime=row.name.to_pydatetime(),
                open_price=row["open"],
                high_price=row["high"],
                low_price=row["low"],
                close_price=row["close"],
                volume=row["volume"],
                open_interest=row["open_interest"],
                gateway_name="RQ"
            )
            data.append(bar)

        return data

    def query_history(self, req: HistoryRequest):
        """
        Query history bar data from RQData.
        """
        full_symbol = req.full_symbol
        symbol = req.symbol
        exchange = req.exchange
        interval = req.interval
        start = req.start
        end = req.end

        # full_symbol = generate_full_symbol(exchange,symbol)

        rq_symbol = self.to_rq_symbol(symbol, exchange)
        if rq_symbol not in self.symbols:
            return None
        rq_interval = INTERVAL_VT2RQ.get(interval, None)
        if not rq_interval:
            return None

        # For adjust timestamp from bar close point (RQData) to open point (VN Trader)
        adjustment = INTERVAL_ADJUSTMENT_MAP[interval]

        # For querying night trading period data
        end += timedelta(1)
        data = []

        if interval == 'tick':
            df = rqdata_get_price(
                rq_symbol,
                frequency=rq_interval,
                fields=[
                    "open", 
                    "high", 
                    "low", 
                    "last", 
                    "volume",
                    "open_interest",
                    'limit_up',
                    'limit_down',
                    'a1',
                    'b1',
                    'a1_v',
                    'b1_v'
                    ],
                start_date=start,
                end_date=end
            )
            if  df is None or df.empty:
                return data  
            for ix, row in df.iterrows():
                tick = TickData(
                    full_symbol=full_symbol,
                    symbol=symbol,
                    exchange=exchange,
                    datetime=row.name.to_pydatetime(),
                    open_price=row["open"],
                    high_price=row["high"],
                    low_price=row["low"],
                    last_price=row["last"],
                    volume=row["volume"],
                    open_interest=row["open_interest"],
                    limit_down=row["limit_down"],
                    limit_up=row["limit_up"],
                    ask_price_1 = row['a1'],
                    ask_volume_1=row["a1_v"],
                    bid_price_1=row["b1"],
                    bid_volume_1=row["b1_v"],
                    gateway_name="RQ"
                )
                data.append(tick)

        else:
            df = rqdata_get_price(
                rq_symbol,
                frequency=rq_interval,
                fields=["open", "high", "low", "close", "volume","open_interest"],
                start_date=start,
                end_date=end
            )
            if df is None or df.empty:
                return data
            for ix, row in df.iterrows():
                bar = BarData(
                    full_symbol=full_symbol,
                    symbol=symbol,
                    exchange=exchange,
                    interval=Interval(interval),
                    datetime=row.name.to_pydatetime() - adjustment,
                    open_price=row["open"],
                    high_price=row["high"],
                    low_price=row["low"],
                    close_price=row["close"],
                    volume=row["volume"],
                    open_interest=row["open_interest"],
                    gateway_name="RQ"
                )
                data.append(bar)

        return data


rqdata_client = RqdataClient()
