#!/usr/bin/env python
# -*- coding: utf-8 -*-
from pandas import Timestamp
import os,sys
import yaml
sys.path.insert(0,"../..")

from source.common.datastruct import EventType
from source.engine.backtest_event_engine import BacktestEventEngine
from source.data.backtest_data_feed_quandl import BacktestDataFeedQuandl
from source.data.backtest_data_feed_local import BacktestDataFeedLocal
from source.data.backtest_data_feed_tushare import BacktestDataFeedTushare
from source.data.data_board import DataBoard
from source.trade.backtest_brokerage import BacktestBrokerage
from source.trade.portfolio_manager import PortfolioManager
from source.trade.performance_manager import PerformanceManager
from source.trade.risk_manager import PassThroughRiskManager
from source.trade.order_manager import OrderManager
from mystrategy import strategy_list

class Backtest(object):
    """
    Event driven backtest engine
    """
    def __init__(self, config):
        """
        1. read in configs
        2. Set up backtest event engine
        """
        self._current_time = Timestamp('1900-01-01')

        ## 0. read in configs
        self._initial_cash = config['cash']
        self._symbols = config['tickers']
        self._benchmark = config['benchmark']
        #self.start_date = datetime.datetime.strptime(config['start_date'], "%Y-%m-%d")
        #self.end_date = datetime.datetime.strptime(config['end_date'], "%Y-%m-%d")
        start_date = config['start_date']
        send_date = config['end_date']
        strategy_name = config['strategy']
        datasource = str(config['datasource'])
        self._hist_dir = config['hist_dir']
        self._output_dir = config['output_dir']

        ## 1. data_feed
        symbols_all = self._symbols[:]   # copy
        if self._benchmark is not None:
            symbols_all.append(self._benchmark)
        self._symbols = [str(s) for s in self._symbols]
        symbols_all = [str(s) for s in symbols_all]

        if (datasource.upper() == 'LOCAL'):
            self._data_feed = BacktestDataFeedLocal(
                hist_dir=self._hist_dir,
                start_date=start_date, end_date=send_date
            )
        elif (datasource.upper() == 'TUSHARE'):
            self._data_feed = BacktestDataFeedTushare(
                start_date=start_date, end_date=send_date
            )
        else:
            self._data_feed = BacktestDataFeedQuandl(
                start_date=start_date, end_date=send_date
            )

        self._data_feed.subscribe_market_data_tick(symbols_all)

        ## 2. event engine
        self._events_engine = BacktestEventEngine(self._data_feed)

        ## 3. brokerage
        self._data_board = DataBoard()
        self._backtest_brokerage = BacktestBrokerage(
            self._events_engine, self._data_board
        )
        self._order_manager = OrderManager()
        ## 4. portfolio_manager
        self._portfolio_manager = PortfolioManager(self._initial_cash,symbols_all)

        ## 5. performance_manager
        self._performance_manager = PerformanceManager(symbols_all)

        ## 6. risk_manager
        self._risk_manager = PassThroughRiskManager()

        ## 7. load all strategies
        strategyClass = strategy_list.get(strategy_name, None)
        if not strategyClass:
            print(u'can not find strategy：%s' % strategy_name)
            return
        #self._strategy = strategyClass(self._symbols, self._events_engine)
        self._strategy = strategyClass(self._events_engine,self._order_manager, self._portfolio_manager,start_date,send_date)
        self._strategy.set_symbols(self._symbols)
        self._strategy.set_capital(self._initial_cash)
        self._strategy.on_init()
        self._strategy.on_start()

        ## 8. trade recorder
        #self._trade_recorder = ExampleTradeRecorder(output_dir)

        ## 9. wire up event handlers
        self._events_engine.register_handler(EventType.TICK, self._tick_event_handler)
        self._events_engine.register_handler(EventType.BAR, self._bar_event_handler)
        self._events_engine.register_handler(EventType.ORDER, self._order_event_handler)
        self._events_engine.register_handler(EventType.FILL, self._fill_event_handler)

    # ------------------------------------ private functions -----------------------------#
    #@profile
    def _tick_event_handler(self, tick_event):
        self._current_time = tick_event.timestamp

        # performance update goes before position updates because it updates previous day performance
        self._performance_manager.update_performance(self._current_time, self._portfolio_manager, self._data_board)
        #print("perf on tick")
        self._portfolio_manager.mark_to_market(self._current_time, tick_event.full_symbol, tick_event.price)
        #print("port on tick")
        self._data_board.on_tick(tick_event)
        if self._backtest_brokerage.on_tick(tick_event):
            return
        #print("databoard on tick")
        self._strategy.on_tick(tick_event)
        #print("str on tick")

    def _bar_event_handler(self, bar_event):
        self._current_time = bar_event.bar_end_time()

        # performance update goes before position updates because it updates previous day
        self._performance_manager.update_performance(self._current_time, self._portfolio_manager, self._data_board)
        #print("update performance")
        self._portfolio_manager.mark_to_market(self._current_time, bar_event.full_symbol, bar_event.adj_close_price)
        #print("m2m")
        self._data_board.on_bar(bar_event)
        #print("databoard on bar")
        self._strategy.on_bar(bar_event)
        #print("stategy on bar")

    def _order_event_handler(self, order_event):
        #self._backtest_brokerage.place_order(order_event)
        self._backtest_brokerage.put(order_event)
    #@profile
    def _fill_event_handler(self, fill_event):
        self._portfolio_manager.on_fill(fill_event)
        self._performance_manager.on_fill(fill_event)

    # -------------------------------- end of private functions -----------------------------#

    # -------------------------------------- public functions -------------------------------#
    def run(self):
        """
        Run backtest
        """
        self._events_engine.run()
        self._performance_manager.update_final_performance(self._current_time, self._portfolio_manager, self._data_board)
        self._performance_manager.save_results(self._symbols,self._hist_dir,self._output_dir)
        self._performance_manager.create_tearsheet(self._output_dir)

    # ------------------------------- end of public functions -----------------------------#

if __name__ == '__main__':
    config = None
    try:
        path = os.path.abspath(os.path.dirname(__file__))
        config_file = os.path.join(path, '../../etc/config_backtest.yaml')
        with open(os.path.expanduser(config_file)) as fd:
            config = yaml.load(fd)
    except IOError:
        print("config.yaml is missing")

    backtest = Backtest(config)
    backtest.run()