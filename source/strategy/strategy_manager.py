#!/usr/bin/env python
# -*- coding: utf-8 -*-
from mystrategy import strategy_list,strategy_list_reload,startstrategy
from multiprocessing import Process
from source.common.datastruct import *   #EventType
class StrategyManager(object):
    def __init__(self, config_client, outgoing_request_event_engine, order_manager, portfolio_manager):
        self._config_client = config_client
        self._outgoing_request_event_engine = outgoing_request_event_engine
        self._order_manager = order_manager    # get sid from
        self._portfolio_manager = portfolio_manager
        self._strategy_id = 1
        self._strategy_dict = {}            # strategy_id ==> strategy
        # there could be more than one strategy that subscribes to a symbol
        self._tick_strategy_dict = {}  # sym -> list of strategy
        self.sid_oid_dict = {}  # sid => list of (fill) order id
        self.sid_buyqty_dict = {}
        self.sid_sellqty_dict = {}
        self.sid_openpnl_dict = {}
        self.sid_closepnl_dict = {}
        self.sid_process_dict = {}
        self.reset()

    def reset(self):
        self._strategy_id = 1          # 0 is mannual discretionary trade
        self._strategy_dict.clear()
        self.sid_oid_dict.clear()
        self.sid_buyqty_dict.clear() 
        self.sid_sellqty_dict.clear()
        self.sid_openpnl_dict.clear()
        self.sid_closepnl_dict.clear()   

    def load_strategy(self):
        # for s in self._config_client['strategy']:
        #     strategyClass = strategy_list.get(s, None)
        #     if not strategyClass:
        #         print(u'can not find strategy：%s' % s)
        #     else:
        #         strategy = strategyClass(self._outgoing_request_event_engine,self._order_manager,self._portfolio_manager)
        #         # strategy.id = self._strategy_id
        #         strategy.name = s          # assign class name to the strategy

        #         # init strategy
        #         strategy.on_init(self._config_client['strategy'][s])
        #         for sym in strategy.symbols:
        #             if sym in self._tick_strategy_dict:
        #                 self._tick_strategy_dict[sym].append(strategy.id)
        #             else:
        #                 self._tick_strategy_dict[sym] = [strategy.id]

        #         strategy.active = False
        #         self._strategy_dict[strategy.id] = strategy
        #         self.sid_oid_dict[strategy.id] =[]
                # self._strategy_id = self._strategy_id+1
        for key,value in strategy_list.items():
            strategyClass = value
            # strategy = strategyClass(self._outgoing_request_event_engine,self._order_manager,self._portfolio_manager)
            # strategy.name = key          # assign class name to the strategy
            # for sym in strategy.symbols:
            #     if sym in self._tick_strategy_dict:
            #         self._tick_strategy_dict[sym].append(strategy.id)
            #     else:
            #         self._tick_strategy_dict[sym] = [strategy.id]
            # strategy.active = False
            self._strategy_dict[strategyClass.ID] = strategyClass
            if (strategyClass.ID not in self.sid_oid_dict):
                self.sid_oid_dict[strategyClass.ID] =[] 
            # p = Process(target=startstrategy, args=(key,))
            # if (strategy.id not in self.sid_process_dict):
            #     self.sid_process_dict[strategy.id] = p  

    def reload_strategy(self):
        strategy_list_reload()
        self._strategy_dict.clear()
        for key,value in strategy_list.items():
            strategyClass = value
            # strategy = strategyClass(self._outgoing_request_event_engine,self._order_manager,self._portfolio_manager)
            # strategy.name = key          # assign class name to the strategy
            # for sym in strategy.symbols:
            #     if sym in self._tick_strategy_dict:
            #         self._tick_strategy_dict[sym].append(strategy.id)
            #     else:
            #         self._tick_strategy_dict[sym] = [strategy.id]
            # strategy.active = False
            self._strategy_dict[strategyClass.ID] = strategyClass
            if (strategyClass.ID not in self.sid_oid_dict):
                self.sid_oid_dict[strategyClass.ID] =[]
        pass     

    def start_strategy(self, sid):
        gr = GeneralReqEvent()
        gr.req = '.' + str(sid) + '|0|' +  str(MSG_TYPE.MSG_TYPE_STRATEGY_START.value) 
        self._outgoing_request_event_engine.put(gr)
        pass
        # if sid not in self.sid_process_dict:
        #     return
        # self.sid_process_dict[sid].start()
        # print("%s (id = %d) started, pid = %d"%(self._strategy_dict[sid].name, sid, self.sid_process_dict[sid].pid) )
        # self._strategy_dict[sid].on_start()

    def stop_strategy(self, sid):
        gr = GeneralReqEvent()
        gr.req = '.' + str(sid) + '|0|' +  str(MSG_TYPE.MSG_TYPE_STRATEGY_END.value) 
        self._outgoing_request_event_engine.put(gr)
        pass
        # if sid not in self.sid_process_dict:
        #     return
        # if (self.sid_process_dict[sid].is_alive()):
        #     self.sid_process_dict[sid].terminate()
        #     print("%s (id = %d) stopped, pid = %d"%(self._strategy_dict[sid].name, sid, self.sid_process_dict[sid].pid) )
        #     name = self._strategy_dict[sid].name
        #     p = Process(target=startstrategy, args=(name,))  
        #     self.sid_process_dict[sid] = p 
          
        # self._strategy_dict[sid].on_stop()

    def flat_strategy(self, sid):
        pass

    def start_all(self):
        pass

    def stop_all(self):
        pass

    def flat_all(self):
        pass

    def cancel_all(self):
        pass

    def on_tick(self, k):        
        # if k.full_symbol in self._tick_strategy_dict:
        #     # foreach strategy that subscribes to this tick
        #     s_list = self._tick_strategy_dict[k.full_symbol]
        #     for sid in s_list:
        #         if self._strategy_dict[sid].active:
        #             self._strategy_dict[sid].on_tick(k)
        pass

    def update_position(self):
        for sid in self._strategy_dict.keys():
            buyqty,sellqty,openpnl,closepnl = self._portfolio_manager.get_live_posinfo_bysid(sid)
            # print("sm on p cal ",buyqty,sellqty,openpnl,closepnl)
            self.sid_buyqty_dict[sid] = buyqty
            self.sid_sellqty_dict[sid] = sellqty
            self.sid_openpnl_dict[sid] = openpnl
            self.sid_closepnl_dict[sid] = closepnl

    def on_position(self,pos):
        # if pos.full_symbol in self._tick_strategy_dict:
        #     # foreach strategy that subscribes to this tick
        #     s_list = self._tick_strategy_dict[pos.full_symbol]
            # for sid in s_list:
            #     if self._strategy_dict[sid].active:
            #         self._strategy_dict[sid].on_position(pos)
        pass

    def on_order_status(self, os):
        # if os.client_order_id in self._oid_sid_dict:
        #     self._strategies_dict[os.client_order_id].on_order_status(os)
        # else:
        #     print('strategy manager doesnt hold the oid, possibly from outside of the system')
        pass
    def on_cancel(self, oid):
        pass

    def on_fill(self, fill):
        if fill.source in self.sid_oid_dict:
            self.sid_oid_dict[fill.source].append(fill)
        else:
            self.sid_oid_dict[fill.source] = [fill]

        # if fill.full_symbol in self._tick_strategy_dict:
        #     # foreach strategy that subscribes to this tick
        #     s_list = self._tick_strategy_dict[fill.full_symbol]
        #     for sid in s_list:
        #         if self._strategy_dict[sid].active:
        #             self._strategy_dict[sid].on_fill(fill)   

