from datetime import datetime
from enum import Enum
from typing import Sequence, Optional

from mongoengine import DateTimeField, Document, FloatField, StringField, connect

from ..common.datastruct import Exchange, Interval, BarData, TickData, TBTEntrustData, TBTTradeData
from .database import BaseDatabaseManager, Driver


def init(_: Driver, settings: dict):
    database = settings["database"]
    host = settings["host"]
    port = settings["port"]
    username = settings["user"]
    password = settings["password"]
    authentication_source = settings["authentication_source"]

    if not username:  # if username == '' or None, skip username
        username = None
        password = None
        authentication_source = None

    connect(
        db=database,
        host=host,
        port=port,
        username=username,
        password=password,
        authentication_source=authentication_source,
    )

    return MongoManager()


class DbBarData(Document):
    """
    Candlestick bar data for database storage.

    Index is defined unique with datetime, interval, symbol
    """

    symbol: str = StringField()
    exchange: str = StringField()
    datetime: datetime = DateTimeField()
    interval: str = StringField()

    volume: float = FloatField()
    open_interest: float = FloatField()
    open_price: float = FloatField()
    high_price: float = FloatField()
    low_price: float = FloatField()
    close_price: float = FloatField()

    meta = {
        "indexes": [
            {
                "fields": ("datetime", "interval", "symbol", "exchange"),
                "unique": True,
            }
        ]
    }

    @staticmethod
    def from_bar(bar: BarData):
        """
        Generate DbBarData object from BarData.
        """
        db_bar = DbBarData()

        db_bar.symbol = bar.symbol
        db_bar.exchange = bar.exchange.value
        db_bar.datetime = bar.datetime
        db_bar.interval = bar.interval.value
        db_bar.volume = bar.volume
        db_bar.open_interest = bar.open_interest
        db_bar.open_price = bar.open_price
        db_bar.high_price = bar.high_price
        db_bar.low_price = bar.low_price
        db_bar.close_price = bar.close_price

        return db_bar

    def to_bar(self):
        """
        Generate BarData object from DbBarData.
        """
        bar = BarData(
            symbol=self.symbol,
            exchange=Exchange(self.exchange),
            datetime=self.datetime,
            interval=Interval(self.interval),
            volume=self.volume,
            open_interest=self.open_interest,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=self.close_price,
            gateway_name="DB",
        )
        return bar


class DbTBTEntrustData(Document):
    """
    tickbytick data for database storage.

    Index is defined unique with datetime, symbol, exchange
    """

    symbol: str = StringField()
    exchange: str = StringField()
    datetime: datetime = DateTimeField()
    
    channel_no:int = FloatField()
    seq:int = FloatField()
    volume: float = FloatField()
    price: float = FloatField()

    side: str = StringField()
    ord_type: str = StringField()

    meta = {
        "indexes": [
            {
                "fields": ("symbol", "exchange", "datetime"),
                "unique": True,
            }
        ]
    }

    @staticmethod
    def from_tbtentrust(tbte: TBTEntrustData):
        """
        Generate DbBarData object from BarData.
        """
        db_tbte = DbTBTEntrustData()

        db_tbte.symbol = tbte.symbol
        db_tbte.exchange = tbte.exchange.value
        db_tbte.datetime = tbte.datetime
        db_tbte.volume = tbte.volume
        db_tbte.price = tbte.price
        db_tbte.channel_no = tbte.channel_no
        db_tbte.seq = tbte.seq

        db_tbte.side = tbte.side
        db_tbte.ord_type = tbte.ord_type


        return db_tbte

    def to_tbtentrust(self):
        """
        Generate TBTEntrustData object from DbTBTEntrustData.
        """
        tbte = TBTEntrustData(
            symbol=self.symbol,
            exchange=Exchange(self.exchange),
            datetime=self.datetime,
            volume=self.volume,
            price=self.price,
            channel_no=self.channel_no,
            seq=self.seq,
            side=self.side,
            ord_type=self.ord_type,
            gateway_name="DB",
        )
        return tbte

class DbTBTTradeData(Document):
    """
    tickbytick data for database storage.

    Index is defined unique with datetime, symbol, exchange
    """

    symbol: str = StringField()
    exchange: str = StringField()
    datetime: datetime = DateTimeField()
    
    channel_no:int = FloatField()
    seq:int = FloatField()
    volume: float = FloatField()
    price: float = FloatField()

    money: str = FloatField()
    bid_no: str = FloatField()
    ask_no: str = FloatField()
    trade_flag: str = StringField()

    meta = {
        "indexes": [
            {
                "fields": ("symbol", "exchange", "datetime"),
                "unique": True,
            }
        ]
    }

    @staticmethod
    def from_tbttrade(tbt: TBTTradeData):
        """
        Generate DbBarData object from BarData.
        """
        db_tbt = DbTBTEntrustData()

        db_tbt.symbol = tbt.symbol
        db_tbt.exchange = tbt.exchange.value
        db_tbt.datetime = tbt.datetime
        db_tbt.volume = tbt.volume
        db_tbt.price = tbt.price
        db_tbt.channel_no = tbt.channel_no
        db_tbt.seq = tbt.seq

        db_tbt.money = tbt.money
        db_tbt.bid_no = tbt.bid_no
        db_tbt.ask_no = tbt.ask_no
        db_tbt.trade_flag = tbt.trade_flag

        return db_tbt

    def to_tbttrade(self):
        """
        Generate TBTEntrustData object from DbTBTEntrustData.
        """
        tbt = TBTTradeData(
            symbol=self.symbol,
            exchange=Exchange(self.exchange),
            datetime=self.datetime,
            volume=self.volume,
            price=self.price,
            channel_no=self.channel_no,
            seq=self.seq,
            money=self.money,
            bid_no=self.bid_no,
            ask_no=self.ask_no,
            trade_flag=self.trade_flag,
            gateway_name="DB",
        )
        return tbt


class DbTickData(Document):
    """
    Tick data for database storage.

    Index is defined unique with (datetime, symbol)
    """

    symbol: str = StringField()
    exchange: str = StringField()
    datetime: datetime = DateTimeField()

    name: str = StringField()
    volume: float = FloatField()
    open_interest: float = FloatField()
    last_price: float = FloatField()
    last_volume: float = FloatField()
    limit_up: float = FloatField()
    limit_down: float = FloatField()

    open_price: float = FloatField()
    high_price: float = FloatField()
    low_price: float = FloatField()
    close_price: float = FloatField()
    pre_close: float = FloatField()

    bid_price_1: float = FloatField()
    bid_price_2: float = FloatField()
    bid_price_3: float = FloatField()
    bid_price_4: float = FloatField()
    bid_price_5: float = FloatField()

    ask_price_1: float = FloatField()
    ask_price_2: float = FloatField()
    ask_price_3: float = FloatField()
    ask_price_4: float = FloatField()
    ask_price_5: float = FloatField()

    bid_volume_1: float = FloatField()
    bid_volume_2: float = FloatField()
    bid_volume_3: float = FloatField()
    bid_volume_4: float = FloatField()
    bid_volume_5: float = FloatField()

    ask_volume_1: float = FloatField()
    ask_volume_2: float = FloatField()
    ask_volume_3: float = FloatField()
    ask_volume_4: float = FloatField()
    ask_volume_5: float = FloatField()

    meta = {
        "indexes": [
            {
                "fields": ("datetime", "symbol", "exchange"),
                "unique": True,
            }
        ],
    }

    @staticmethod
    def from_tick(tick: TickData):
        """
        Generate DbTickData object from TickData.
        """
        db_tick = DbTickData()

        db_tick.symbol = tick.symbol
        db_tick.exchange = tick.exchange.value
        db_tick.datetime = tick.datetime
        db_tick.name = tick.name
        db_tick.volume = tick.volume
        db_tick.open_interest = tick.open_interest
        db_tick.last_price = tick.last_price
        db_tick.last_volume = tick.last_volume
        db_tick.limit_up = tick.limit_up
        db_tick.limit_down = tick.limit_down
        db_tick.open_price = tick.open_price
        db_tick.high_price = tick.high_price
        db_tick.low_price = tick.low_price
        db_tick.pre_close = tick.pre_close

        db_tick.bid_price_1 = tick.bid_price_1
        db_tick.ask_price_1 = tick.ask_price_1
        db_tick.bid_volume_1 = tick.bid_volume_1
        db_tick.ask_volume_1 = tick.ask_volume_1

        if tick.bid_price_2:
            db_tick.bid_price_2 = tick.bid_price_2
            db_tick.bid_price_3 = tick.bid_price_3
            db_tick.bid_price_4 = tick.bid_price_4
            db_tick.bid_price_5 = tick.bid_price_5

            db_tick.ask_price_2 = tick.ask_price_2
            db_tick.ask_price_3 = tick.ask_price_3
            db_tick.ask_price_4 = tick.ask_price_4
            db_tick.ask_price_5 = tick.ask_price_5

            db_tick.bid_volume_2 = tick.bid_volume_2
            db_tick.bid_volume_3 = tick.bid_volume_3
            db_tick.bid_volume_4 = tick.bid_volume_4
            db_tick.bid_volume_5 = tick.bid_volume_5

            db_tick.ask_volume_2 = tick.ask_volume_2
            db_tick.ask_volume_3 = tick.ask_volume_3
            db_tick.ask_volume_4 = tick.ask_volume_4
            db_tick.ask_volume_5 = tick.ask_volume_5

        return db_tick

    def to_tick(self):
        """
        Generate TickData object from DbTickData.
        """
        tick = TickData(
            symbol=self.symbol,
            exchange=Exchange(self.exchange),
            datetime=self.datetime,
            name=self.name,
            volume=self.volume,
            open_interest=self.open_interest,
            last_price=self.last_price,
            last_volume=self.last_volume,
            limit_up=self.limit_up,
            limit_down=self.limit_down,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            pre_close=self.pre_close,
            bid_price_1=self.bid_price_1,
            ask_price_1=self.ask_price_1,
            bid_volume_1=self.bid_volume_1,
            ask_volume_1=self.ask_volume_1,
            gateway_name="DB",
        )

        if self.bid_price_2:
            tick.bid_price_2 = self.bid_price_2
            tick.bid_price_3 = self.bid_price_3
            tick.bid_price_4 = self.bid_price_4
            tick.bid_price_5 = self.bid_price_5

            tick.ask_price_2 = self.ask_price_2
            tick.ask_price_3 = self.ask_price_3
            tick.ask_price_4 = self.ask_price_4
            tick.ask_price_5 = self.ask_price_5

            tick.bid_volume_2 = self.bid_volume_2
            tick.bid_volume_3 = self.bid_volume_3
            tick.bid_volume_4 = self.bid_volume_4
            tick.bid_volume_5 = self.bid_volume_5

            tick.ask_volume_2 = self.ask_volume_2
            tick.ask_volume_3 = self.ask_volume_3
            tick.ask_volume_4 = self.ask_volume_4
            tick.ask_volume_5 = self.ask_volume_5

        return tick


class MongoManager(BaseDatabaseManager):
    def load_bar_data(
        self,
        symbol: str,
        exchange: Exchange,
        interval: Interval,
        start: datetime,
        end: datetime,
    ) -> Sequence[BarData]:
        s = DbBarData.objects(
            symbol=symbol,
            exchange=exchange.value,
            interval=interval.value,
            datetime__gte=start,
            datetime__lte=end,
        )
        data = [db_bar.to_bar() for db_bar in s]
        return data

    def load_tbte_data(
        self,
        symbol: str,
        exchange: Exchange,
        start: datetime,
        end: datetime,
    ) -> Sequence[TBTEntrustData]:
        s = DbTBTEntrustData.objects(
            symbol=symbol,
            exchange=exchange.value,
            datetime__gte=start,
            datetime__lte=end,
        )
        data = [db_tbt.to_tbtentrust() for db_tbt in s]
        return data

    def load_tbtt_data(
        self,
        symbol: str,
        exchange: Exchange,
        start: datetime,
        end: datetime,
    ) -> Sequence[TBTTradeData]:
        s = DbTBTTradeData.objects(
            symbol=symbol,
            exchange=exchange.value,
            datetime__gte=start,
            datetime__lte=end,
        )
        data = [db_tbt.to_tbttrade() for db_tbt in s]
        return data


    def load_tick_data(
        self, symbol: str, exchange: Exchange, start: datetime, end: datetime
    ) -> Sequence[TickData]:
        s = DbTickData.objects(
            symbol=symbol,
            exchange=exchange.value,
            datetime__gte=start,
            datetime__lte=end,
        )
        data = [db_tick.to_tick() for db_tick in s]
        return data

    @staticmethod
    def to_update_param(d):
        return {
            "set__" + k: v.value if isinstance(v, Enum) else v
            for k, v in d.__dict__.items()
        }

    def save_bar_data(self, datas: Sequence[BarData]):
        for d in datas:
            updates = self.to_update_param(d)
            updates.pop("set__gateway_name")
            updates.pop("set__vt_symbol")
            updates.pop("set__full_symbol")
            updates.pop("set__adj_close_price")
            updates.pop("set__bar_start_time")
            (
                DbBarData.objects(
                    symbol=d.symbol, interval=d.interval.value, datetime=d.datetime
                ).update_one(upsert=True, **updates)
            )

    def save_tbte_data(self, datas: Sequence[TBTEntrustData]):
        for d in datas:
            updates = self.to_update_param(d)
            updates.pop("set__gateway_name")
            updates.pop("set__full_symbol")
            # updates.pop("set__channel_no")
            # updates.pop("set__seq")
            (
                DbTBTEntrustData.objects(
                    symbol=d.symbol, exchange=d.exchange.value, datetime=d.datetime
                ).update_one(upsert=True, **updates)
            )

    def save_tbtt_data(self, datas: Sequence[TBTTradeData]):
        for d in datas:
            updates = self.to_update_param(d)
            updates.pop("set__gateway_name")
            updates.pop("set__full_symbol")
            # updates.pop("set__bid_no")
            # updates.pop("set__ask_no")
            # updates.pop("set__channel_no")
            # updates.pop("set__seq")

            (
                DbTBTTradeData.objects(
                    symbol=d.symbol, exchange=d.exchange.value, datetime=d.datetime
                ).update_one(upsert=True, **updates)
            )


    def save_tick_data(self, datas: Sequence[TickData]):
        for d in datas:
            updates = self.to_update_param(d)
            updates.pop("set__gateway_name")
            updates.pop("set__vt_symbol")
            updates.pop("set__depth")
            updates.pop("set__full_symbol")
            updates.pop("set__timestamp")
            (
                DbTickData.objects(
                    symbol=d.symbol, exchange=d.exchange.value, datetime=d.datetime
                ).update_one(upsert=True, **updates)
            )

    def get_newest_bar_data(
        self, symbol: str, exchange: "Exchange", interval: "Interval"
    ) -> Optional["BarData"]:
        s = (
            DbBarData.objects(symbol=symbol, exchange=exchange.value)
            .order_by("-datetime")
            .first()
        )
        if s:
            return s.to_bar()
        return None

    def get_newest_tick_data(
        self, symbol: str, exchange: "Exchange"
    ) -> Optional["TickData"]:
        s = (
            DbTickData.objects(symbol=symbol, exchange=exchange.value)
            .order_by("-datetime")
            .first()
        )
        if s:
            return s.to_tick()
        return None

    def clean(self, symbol: str):
        DbTickData.objects(symbol=symbol).delete()
        DbBarData.objects(symbol=symbol).delete()
