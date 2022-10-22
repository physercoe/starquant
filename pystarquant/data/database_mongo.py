from datetime import datetime, date
from enum import Enum
from typing import Sequence, Optional

from mongoengine import DateTimeField, Document, FloatField, StringField, IntField, connect
import pymongo

from arctic import Arctic
import arctic
import pandas as pd
from tzlocal import get_localzone


from pystarquant.common.datastruct import Exchange, Interval, BarData, TBTBarData, TickData, TBTEntrustData, TBTTradeData
from pystarquant.data.database import BaseDatabaseManager, Driver


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

    # connect(
    #     db=database,
    #     host=host,
    #     port=port,
    #     username=username,
    #     password=password,
    #     authentication_source=authentication_source,
    # )

    return MongoManager(settings)


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



class DbTbtbarData(Document):
    """
    user defined bar data for database storage.

    Index is defined unique with datetime, interval, full_symbol, bigmoney
    """
    full_symbol:str = StringField()
    symbol: str = StringField()
    exchange: str = StringField()
    datetime: datetime = DateTimeField()
    interval: str = StringField()
    bigmoney: int = IntField()

    open_interest: float = FloatField()
    volume: float = FloatField()
    open_price: float = FloatField()
    high_price: float = FloatField()
    low_price: float = FloatField()
    close_price: float = FloatField()

    ask_totalqty: float = FloatField()
    bid_totalqty: float = FloatField()
    ask_totalmoney: float = FloatField()
    bid_totalmoney: float = FloatField()
    ask_bigmoney: float = FloatField()
    bid_bigmoney: float = FloatField()
    ask_bigleft: float = FloatField()
    bid_bigleft: float = FloatField()


    meta = {
        "indexes": [
            {
                "fields": ("datetime", "interval", "full_symbol", "bigmoney"),
                "unique": True,
            }
        ]
    }

    @staticmethod
    def from_bar(bar: TBTBarData):
        """
        Generate DbBarData object from BarData.
        """
        db_bar = DbTbtbarData()

        db_bar.full_symbol = bar.full_symbol
        db_bar.symbol = bar.symbol
        db_bar.exchange = bar.exchange.value
        db_bar.datetime = bar.datetime
        db_bar.interval = bar.interval.value
        db_bar.bigmoney = bar.bigmoney

        db_bar.volume = bar.volume
        db_bar.open_interest = bar.open_interest
        db_bar.open_price = bar.open_price
        db_bar.high_price = bar.high_price
        db_bar.low_price = bar.low_price
        db_bar.close_price = bar.close_price

        db_bar.ask_totalqty = bar.ask_totalqty
        db_bar.bid_totalqty = bar.bid_totalqty
        db_bar.ask_totalmoney = bar.ask_totalmoney
        db_bar.bid_totalmoney = bar.bid_totalmoney
        db_bar.ask_bigmoney = bar.ask_bigmoney
        db_bar.bid_bigmoney = bar.bid_bigmoney
        db_bar.ask_bigleft = bar.ask_bigleft
        db_bar.bid_bigleft = bar.bid_bigleft

        return db_bar

    def to_bar(self):
        """
        Generate BarData object from DbBarData.
        """
        bar = TBTBarData(
            full_symbol=self.full_symbol,
            symbol=self.symbol,
            exchange=Exchange(self.exchange),
            datetime=self.datetime,
            interval=Interval(self.interval),
            bigmoney=self.bigmoney,
            volume=self.volume,
            open_interest=self.open_interest,
            open_price=self.open_price,
            high_price=self.high_price,
            low_price=self.low_price,
            close_price=self.close_price,
            ask_totalqty=self.ask_totalqty,
            bid_totalqty=self.bid_totalqty,
            ask_totalmoney=self.ask_totalmoney,
            bid_totalmoney=self.bid_totalmoney,
            ask_bigmoney=self.ask_bigmoney,
            bid_bigmoney=self.bid_bigmoney,
            ask_bigleft=self.ask_bigleft,
            bid_bigleft=self.bid_bigleft,
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
    def __init__(self,settings:dict):
        super().__init__()
        self.database = settings["database"]
        self.host = settings["host"]
        self.port = settings["port"]
        self.username = settings["user"]
        self.password = settings["password"]
        self.authentication_source = settings["authentication_source"]

    def arctic_load_tick(
        self,
        full_symbol: str, 
        start: datetime, 
        end: datetime,
        collectionname:str = 'tick',     
    
    ):
        store = Arctic(self.host)
        libnames = store.list_libraries()
        if collectionname not in  libnames:
            return pd.DataFrame(),[]
        lib = store[collectionname]
        tz= get_localzone()
        pdrange = pd.date_range(start=start, end=end,freq='s',tz=tz)
        readtick = lib.read(full_symbol,chunk_range=pdrange)
        if readtick is None or readtick.empty:
            return pd.DataFrame(),[]
        readtick.index = readtick.index.tz_localize('UTC')
        readtick.index = readtick.index.tz_convert(tz)
        
        # also get tradeday list 
        startendtuplelist = list(
            lib.get_chunk_ranges(full_symbol,chunk_range=pdrange)
        )
        tradedaylist = [ pd.to_datetime(t[0].decode()).date() for t in startendtuplelist]


        return readtick,tradedaylist

    def arctic_load_bar(
        self,
        full_symbol: str, 
        start: datetime, 
        end: datetime,
        collectionname:str = 'bar1min88', 
    ):
        store = Arctic(self.host)
        libnames = store.list_libraries()
        if (collectionname not in  libnames) or (not collectionname.startswith('bar')):
            return pd.DataFrame(),[]
        lib = store[collectionname]
        tz= get_localzone()
        pdrange = pd.date_range(start=start, end=end,freq='s',tz=tz)
        readbar = lib.read(full_symbol,chunk_range=pdrange)
        if readbar is None or readbar.empty:
            return pd.DataFrame(),[]
        readbar.index = readbar.index.tz_localize('UTC')
        readbar.index = readbar.index.tz_convert(tz)
        
        # also get tradeday list 
        
        tradedaylist = list(pd.unique(readbar.index.date))


        return readbar,tradedaylist



    def load_bar_data(
        self,
        full_symbol: str,
        interval: Interval,
        start: datetime,
        end: datetime,
        collectionname:str ='db_bar_data',
        using_in: bool = False,
        using_cursor: bool = False        
    ) -> Sequence[BarData]:
        # s = DbBarData.objects(
        #     symbol=symbol,
        #     exchange=exchange.value,
        #     interval=interval.value,
        #     datetime__gte=start,
        #     datetime__lte=end,
        # )
        # data = [db_bar.to_bar() for db_bar in s]
        # return data
        if not full_symbol: 
            return []
        if type(start) == date:
            start = datetime(start.year, start.month, start.day)
        if type(end) == date:
            end = datetime(end.year,end.month,end.day)

        fullsym = full_symbol
        filter = '$in'
        if type(full_symbol) != list:
            filter = '$regex'
            if using_in:
                filter = '$in'            
                fullsym = full_symbol.split(';')


        client = pymongo.MongoClient(host=self.host, port=self.port)
        db = client[self.database]
        collection = db[collectionname]
        # results = collection.find(
        #     {'datetime': {'$gte': start, "$lte":end},
        #     'symbol':{'$in':symbolfilter},
        #     'interval':interval.value,
        #     'exchange':{'$in':exlist}
        #     }) 
        results = collection.find(
            {'datetime': {'$gte': start, "$lte":end},
            'full_symbol':{filter:fullsym},
            'interval':interval.value,
            })
        results = results.sort([('datetime',1)])
        if using_cursor:
            return results     
        bars = []
        for data in results:
            bar = BarData(
                symbol=data["symbol"],
                full_symbol=data["full_symbol"],
                datetime=data["datetime"],
                exchange=Exchange(data["exchange"]),
                interval=interval,
                volume=data["volume"],
                open_interest=data["open_interest"],
                open_price=data["open_price"],
                high_price=data["high_price"],
                low_price=data["low_price"],
                close_price=data["close_price"]
                )
            bars.append(bar)
        # bars.sort(key=lambda x:x.datetime)
        return bars


    def load_tbtbar_data(
        self,
        full_symbol: str,
        interval: Interval,
        start: datetime,
        end: datetime,
        collectionname:str = 'db_tbtbar_data',
        using_cursor: bool = False
    ) -> Sequence[TBTBarData]:
        # s = DbTbtbarData.objects(
        #     full_symbol=full_symbol,
        #     interval=interval.value,
        #     bigmoney=bigmoney,
        #     datetime__gte=start,
        #     datetime__lte=end,
        # )
        # data = [db_bar.to_bar() for db_bar in s]
        # return data
        if not full_symbol: 
            return []
        client = pymongo.MongoClient(host=self.host, port=self.port)
        db = client[self.database]
        collection = db[collectionname]

        filter = '$in'
        if type(full_symbol) != list:
            filter = '$regex'

        results = collection.find(
            {'datetime': {'$gte': start, "$lte":end},
            'full_symbol': {filter:full_symbol},     # {'$in': re.complile(full_symbol)}
            'interval':interval.value,
                }
            )
        results = results.sort([('datetime',1)])
        if using_cursor:
            return results
        bars = []

        for data in results:
            bar = TBTBarData(
                full_symbol=data["full_symbol"],
                datetime=data["datetime"],
                interval=interval,
                volume=data["volume"],
                open_price=data["open_price"],
                high_price=data["high_price"],
                low_price=data["low_price"],
                close_price=data["close_price"],
                ask_totalqty=data["ask_totalqty"],
                bid_totalqty=data["bid_totalqty"],
                ask_totalmoney=data["ask_totalmoney"],
                bid_totalmoney=data["bid_totalmoney"],
                ask_bigmoney=data["ask_bigmoney"],
                bid_bigmoney=data["bid_bigmoney"],
                ask_bigleft=data["ask_bigleft"],
                bid_bigleft=data["bid_bigleft"],
                user_defined_1=data["user_defined_1"] if "user_defined_1" in data else 0.0
                )
            bars.append(bar)
        # bars.sort(key=lambda x:x.datetime)
        return bars





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
        self, 
        full_symbol: str, 
        start: datetime, 
        end: datetime,
        collectionname:str = 'db_tick_data',
        using_in: bool= False,
        using_cursor: bool = False
    ) -> Sequence[TickData]:
        # s = DbTickData.objects(
        #     symbol=symbol,
        #     exchange=exchange.value,
        #     datetime__gte=start,
        #     datetime__lte=end,
        # )
        # data = [db_tick.to_tick() for db_tick in s]
        # return data
        if not full_symbol: 
            return []
        fullsym = full_symbol
        filter = '$in'
        if type(full_symbol) != list:
            filter = '$regex'
            if using_in:
                filter = '$in'            
                fullsym = full_symbol.split(';')



        client = pymongo.MongoClient(host=self.host, port=self.port)
        db = client[self.database]
        collection = db[collectionname]
        results = collection.find(
            {'datetime': {'$gte': start, "$lte":end},
            'full_symbol':{filter:fullsym},
            })
        results = results.sort([('datetime',1)])
        if using_cursor:
            return results      
        ticks = []
        # TODO: consider depth = 5 data
        for data in results:
            tick = TickData(
                full_symbol=data["full_symbol"],
                symbol=data["symbol"],
                datetime=data["datetime"],
                exchange=Exchange(data["exchange"]),
                ask_price_1=data["ask_price_1"],
                ask_volume_1=data["ask_volume_1"],
                bid_price_1=data["bid_price_1"],
                bid_volume_1=data["bid_volume_1"],
                last_price=data["last_price"],
                volume=data["volume"],
                open_interest=data["open_interest"],
                limit_up=data["limit_up"],
                limit_down=data["limit_down"],
                open_price=data["open_price"],
                pre_close=data["pre_close"],
                high_price=data["high_price"],
                low_price=data["low_price"]
                )
            ticks.append(tick)
        # ticks.sort(key=lambda x:x.datetime)        
        return ticks

    @staticmethod
    def to_update_param(d):
        return {
            "set__" + k: v.value if isinstance(v, Enum) else v
            for k, v in d.__dict__.items()
        }

    def save_bar_data(self, datas: Sequence[BarData], updatemode:bool=False,collectionname:str='db_bar_data'):
        client = pymongo.MongoClient(host=self.host, port=self.port)
        db = client[self.database]
        collection = db[collectionname]
        # collection.create_index([("symbol",1),("datetime",1),('interval',1),('exchange',1)], unique=True)
        collection.create_index([("full_symbol",1),("datetime",1),('interval',1)], unique=True)
        if not updatemode:
            docs = [{
                "symbol":bar.symbol,
                "full_symbol":bar.full_symbol,
                "datetime":bar.datetime,
                "interval":bar.interval.value,
                "exchange":bar.exchange.value,
                "open_price":bar.open_price, 
                "high_price":bar.high_price,
                "low_price":bar.low_price,
                "close_price":bar.close_price,
                "volume":bar.volume,
                "open_interest":bar.open_interest,
                } 
            for bar in datas
            ]
            collection.insert_many(docs)
        else:
            update_operations = []
            for bar in datas:
                op = pymongo.UpdateOne(
                    {"full_symbol":bar.full_symbol,
                    'datetime':bar.datetime,
                    'interval':bar.interval.value
                    },
                    {'$set':
                        {
                        "symbol":bar.symbol,
                        "full_symbol":bar.full_symbol,
                        "datetime":bar.datetime,
                        "interval":bar.interval.value,
                        "exchange":bar.exchange.value,
                        "open_price":bar.open_price, 
                        "high_price":bar.high_price,
                        "low_price":bar.low_price,
                        "close_price":bar.close_price,
                        "volume":bar.volume,
                        "open_interest":bar.open_interest
                        }
                    },
                    upsert=True                               
                )
                update_operations.append(op)
            collection.bulk_write(update_operations, bypass_document_validation=True)  
        # for d in datas:
        #     updates = self.to_update_param(d)
        #     updates.pop("set__gateway_name")
        #     updates.pop("set__vt_symbol")
        #     updates.pop("set__full_symbol")
        #     updates.pop("set__adj_close_price")
        #     updates.pop("set__bar_start_time")
        #     (
        #         DbBarData.objects(
        #             symbol=d.symbol, interval=d.interval.value, datetime=d.datetime
        #         ).update_one(upsert=True, **updates)
        #     )




    def save_tbtbar_data(self, datas: Sequence[TBTBarData],updatemode:bool=False,collectionname:str='db_tbtbar_data'):
        client = pymongo.MongoClient(host=self.host, port=self.port)
        db = client[self.database]        
        collection = db[collectionname]
        collection.create_index([("full_symbol",1),("datetime",1),('interval',1),('bigmoney',1)], unique=True)
        if not updatemode:
            docs = [{
                "full_symbol":bar.full_symbol,
                "datetime":bar.datetime,
                "interval":bar.interval.value,
                "bigmoney":bar.bigmoney,
                "open_price":bar.open_price, 
                "high_price":bar.high_price,
                "low_price":bar.low_price,
                "close_price":bar.close_price,
                "volume":bar.volume,
                "ask_totalqty":bar.ask_totalqty,
                "bid_totalqty":bar.bid_totalqty,
                "ask_totalmoney":bar.ask_totalmoney,
                "bid_totalmoney":bar.bid_totalmoney,
                "ask_bigmoney":bar.ask_bigmoney,
                "bid_bigmoney":bar.bid_bigmoney,
                "ask_bigleft":bar.ask_bigleft,
                "bid_bigleft":bar.bid_bigleft
                } 
            for bar in datas
            ]
            collection.insert_many(docs)
        else:
            update_operations = []
            for bar in datas:
                op = pymongo.UpdateOne(
                    {"full_symbol":bar.full_symbol,
                    'datetime':bar.datetime,
                    'interval':bar.interval.value,
                    'bigmoney':bar.bigmoney},
                    {'$set':{
                        "open_price":bar.open_price, 
                        "high_price":bar.high_price,
                        "low_price":bar.low_price,
                        "close_price":bar.close_price,
                        "volume":bar.volume,
                        "ask_totalqty":bar.ask_totalqty,
                        "bid_totalqty":bar.bid_totalqty,
                        "ask_totalmoney":bar.ask_totalmoney,
                        "bid_totalmoney":bar.bid_totalmoney,
                        "ask_bigmoney":bar.ask_bigmoney,
                        "bid_bigmoney":bar.bid_bigmoney,
                        "ask_bigleft":bar.ask_bigleft,
                        "bid_bigleft":bar.bid_bigleft
                        }
                    },
                    upsert=True                               
                )
                update_operations.append(op)
            collection.bulk_write(update_operations, bypass_document_validation=True)

        # for d in datas:
        #     updates = self.to_update_param(d)
        #     updates.pop("set__gateway_name")
        #     updates.pop("set__vt_symbol")
        #     updates.pop("set__adj_close_price")
        #     (
        #         DbTbtbarData.objects(
        #             full_symbol=d.full_symbol, interval=d.interval.value, 
        #             datetime=d.datetime, bigmoney=d.bigmoney
        #         ).update_one(upsert=True, **updates)
        #     )


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


    def save_tick_data(self, datas: Sequence[TickData], updatemode:bool=False,collectionname:str='db_tick_data'):
        client = pymongo.MongoClient(host=self.host, port=self.port)
        db = client[self.database]        
        collection = db[collectionname]
        # collection.create_index([("symbol",1),("datetime",1),('exchange',1)], unique=True)
        collection.create_index([("full_symbol",1),("datetime",1)], unique=True)
        # TODO: add 5 depth markdet
        if not updatemode:
            docs = [{
                "symbol":data.symbol,
                "full_symbol":data.full_symbol,
                "datetime":data.datetime,
                "exchange":data.exchange.value,
                "name":data.name,
                "last_price":data.last_price,
                "last_volume":data.last_volume,
                "ask_price_1":data.ask_price_1,
                "ask_volume_1":data.ask_volume_1,
                "bid_price_1":data.bid_price_1,
                "bid_volume_1":data.bid_volume_1,
                "limit_up":data.limit_up,
                "limit_down":data.limit_down,
                "open_price":data.open_price, 
                "high_price":data.high_price,
                "low_price":data.low_price,
                "pre_close":data.pre_close,
                "volume":data.volume,
                "open_interest":data.open_interest,
                } 
            for data in datas
            ]
            collection.insert_many(docs)
        else:
            update_operations = []
            for data in datas:
                op = pymongo.UpdateOne(
                    {"full_symbol":data.full_symbol,
                    'datetime':data.datetime
                    },
                    {'$set':{
                        "symbol":data.symbol,
                        "full_symbol":data.full_symbol,
                        "datetime":data.datetime,
                        "exchange":data.exchange.value,
                        "name":data.name,
                        "last_price":data.last_price,
                        "last_volume":data.last_volume,
                        "ask_price_1":data.ask_price_1,
                        "ask_volume_1":data.ask_volume_1,
                        "bid_price_1":data.bid_price_1,
                        "bid_volume_1":data.bid_volume_1,
                        "limit_up":data.limit_up,
                        "limit_down":data.limit_down,
                        "open_price":data.open_price, 
                        "high_price":data.high_price,
                        "low_price":data.low_price,
                        "pre_close":data.pre_close,
                        "volume":data.volume,
                        "open_interest":data.open_interest,
                        }
                    },
                    upsert=True                               
                )
                update_operations.append(op)
            collection.bulk_write(update_operations, bypass_document_validation=True) 


        # for d in datas:
        #     updates = self.to_update_param(d)
        #     updates.pop("set__gateway_name")
        #     updates.pop("set__vt_symbol")
        #     updates.pop("set__depth")
        #     updates.pop("set__full_symbol")
        #     updates.pop("set__timestamp")
        #     (
        #         DbTickData.objects(
        #             symbol=d.symbol, exchange=d.exchange.value, datetime=d.datetime
        #         ).update_one(upsert=True, **updates)
        #     )

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
