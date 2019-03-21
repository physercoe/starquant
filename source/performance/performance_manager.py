#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import pandas as pd
import pyfolio as pf
import matplotlib.pyplot as plt
import os
from datetime import timedelta
from dateutil.parser import parse
from matplotlib.pylab import date2num

import matplotlib as mpl
import matplotlib.ticker as mtk
#import matplotlib.finance as mpf # lower version
import mpl_finance as mpf
class PerformanceManager(object):
    """
    Record equity, positions, and trades in accordance to pyfolio format
    First date will be the first data start date
    """
    def __init__(self, symbols):
        self._symbols = symbols
        self._slippage = 0.0
        self._commission_rate = 0.0
        self.reset()

    # ------------------------------------ public functions -----------------------------#
    #  or each sid
    def reset(self):
        self._realized_pnl = 0.0
        self._unrealized_pnl = 0.0

        self._equity = pd.Series()      # equity line
        self._df_positions = pd.DataFrame(columns=self._symbols+['cash'])
        self._df_trades = pd.DataFrame(columns=['datetime','symbol','amount', 'price','positioneffect','profit'])
        self._equitylist=[]
        self._timelist=[]
        self._positionslist= {'cash':[]}
        for sym in self._symbols:
            self._positionslist.update({sym:[]})

    def set_splippage(self, slippage):
        self._slippage = slippage

    def set_commission_rate(self, commission_rate):
        self._commission_rate = commission_rate
    #@profile
    def update_performance(self, current_time, position_manager, data_board):
        #print("entering update performance")
        # if self._equity.empty:
        #     self._equity[current_time] = 0.0
        #     return
        # # on a new time/date, calculate the performances for the last date
        # elif current_time != self._equity.index[-1]:
        #     performance_time = self._equity.index[-1]

        #     equity = 0.0
        #     self._df_positions.loc[performance_time] = [0] * (len(self._symbols) + 1)
        #     for sym, pos in position_manager.positions.items():
        #         #equity += pos.size * data_board.get_last_price(sym)
        #         equity += pos.unrealized_pnl
        #         #self._df_positions.loc[performance_time, sym] = pos.size * data_board.get_last_price(sym)
        #         self._df_positions.loc[performance_time, sym] = pos.unrealized_pnl
        #     self._df_positions.loc[performance_time, 'cash'] = position_manager.cash

        #     self._equity[performance_time] = equity + position_manager.cash + position_manager.margin

        #     self._equity[current_time] = 0.0
        # self._timelist.append(current_time)
        # equity = 0.0
        # for sym, pos in position_manager.positions.items():
        #         equity += pos.unrealized_pnl
        # equity += position_manager.cash + position_manager.margin
        self._timelist.append(current_time)
        self._equitylist.append(position_manager.get_total_value())
        self._positionslist['cash'].append(position_manager.cash)
        for sym, pos in position_manager.positions.items():
            # if sym in self._symbols:
            self._positionslist[sym].append(pos.unrealized_pnl)
        #self._df_positions = self._df_positions.append(pd.DataFrame(tmp,index = [current_time]))



        


    def on_fill(self, fill_event):
        # self._df_trades.loc[fill_event.timestamp] = [fill_event.fill_size, fill_event.fill_price, fill_event.full_symbol]
        self._df_trades = self._df_trades.append(pd.DataFrame(
            {'symbol': [fill_event.full_symbol],'amount': [fill_event.fill_size], 'price': [fill_event.fill_price],'positioneffect': [fill_event.fill_flag.name],'profit':[fill_event.fill_pnl], \
            'datetime':[fill_event.timestamp] } ) )

    def update_final_performance(self, current_time, position_manager, data_board):
        """
        When a new data date comes in, it calcuates performances for the previous day
        This leaves the last date not updated.
        So we call the update explicitly
        """
        # performance_time = current_time

        # equity = 0.0
        # self._df_positions.loc[performance_time] = [0] * (len(self._symbols) + 1)
        # for sym, pos in position_manager.positions.items():
        #     equity += pos.unrealized_pnl
        #     self._df_positions.loc[performance_time, sym] = pos.unrealized_pnl
        #     #equity += pos.size * data_board.get_last_price(sym)
        #     #self._df_positions.loc[performance_time, sym] = pos.size * data_board.get_last_price(sym)
        # self._df_positions.loc[performance_time, 'cash'] = position_manager.cash

        # self._equity[performance_time] = equity + position_manager.cash + position_manager.margin

        # self._timelist.append(current_time)
        # equity = 0.0
        # for sym, pos in position_manager.positions.items():
        #         equity += pos.unrealized_pnl
        # equity += position_manager.cash + position_manager.margin
        # self._equitylist.append(equity)
        # self._equity=pd.Series(self._equitylist,index=self._timelist)

        self._timelist.append(current_time)
        self._equitylist.append(position_manager.get_total_value())
        self._positionslist['cash'].append(position_manager.cash)
        for sym, pos in position_manager.positions.items():
            self._positionslist[sym].append(pos.unrealized_pnl) 
        self._equity=pd.Series(self._equitylist,index=pd.Index(self._timelist,name='time'))
        self._df_positions = pd.DataFrame(self._positionslist,index=self._timelist)
        self._df_trades.reset_index(drop=True,inplace=True)

    def create_tearsheet(self,output_dir):
        #rets = self._equity.pct_change()
        #rets =pd.Series(self._equitylist,index=self._timelist)
        rets = self._equity
        # rets = rets[1:]
        rets.index = rets.index.tz_localize('UTC')
        #print(rets.index)
        # self._df_positions.index = self._df_positions.index.tz_localize('UTC')
        #self._df_trades.index = self._df_trades.index.tz_localize('UTC')
        # self._df_trades.index = pd.DatetimeIndex(self._df_trades.index).tz_localize('UTC')
        #print(self._df_trades.index)
        #pf.create_full_tear_sheet(rets, self._df_positions, self._df_trades)
        #pf.create_simple_tear_sheet(rets,benchmark_rets=rets)

        rets.plot()
        plt.savefig(output_dir + "/total equity.png")
        plt.close()
        # plt.show()
        









    def save_results(self, symbols, hist_dir,output_dir):
        self._equity.to_csv(output_dir + '/equity.csv',header=['equity'])
        self._df_positions.index.rename('time',inplace=True)
        self._df_positions.to_csv(output_dir + '/positions.csv')
        # self._df_trades.index.rename('time',inplace=True)
        self._df_trades.to_csv(output_dir + '/trades.csv')
#zwf draw 
        data = self._df_trades
        
        long_data_raw = pd.DataFrame(columns = data.columns)
        short_data_raw = pd.DataFrame(columns = data.columns)
        proorloss_longlist = []
        proorloss_shortlist = []
        for i in range(0,len(data.index)):
            if (data['amount'].iat[i] >0) and (np.mod(i,2) == 0) :
                proorloss = data['price'][i+1] - data['price'].iat[i]
                proorloss_longlist.append(proorloss)
                long_data_raw = long_data_raw.append(data.iloc[i])
                
            if (data['amount'].iat[i] <0 ) and (np.mod(i,2) == 0) :
                proorloss = data['price'].iat[i] - data['price'].iat[i+1]
                proorloss_shortlist.append(proorloss)
                short_data_raw = short_data_raw.append(data.iloc[i])
                
        long_data_raw['deltaprice'] = proorloss_longlist
        short_data_raw['deltaprice'] = proorloss_shortlist
        
        
        
        long_point_stat = long_data_raw['deltaprice'].value_counts()  # 点数 vs 次数分布
        short_point_stat = short_data_raw['deltaprice'].value_counts()
        
        long_deal_stat = long_data_raw['datetime'].value_counts()  #统计交易次数
        short_deal_stat = short_data_raw['datetime'].value_counts()
        
        long_deal_point_vs_date = long_data_raw['deltaprice'].groupby(long_data_raw['datetime']).sum() #统计 盈亏点数 vs time
        short_deal_point_vs_date = short_data_raw['deltaprice'].groupby(short_data_raw['datetime']).sum()
        
        #long_data_raw['absdeltaprice'] = list(map(abs,proorloss_longlist))
        #short_data_raw['absdeltaprice'] = list(map(abs,proorloss_longlist))
        long_deal_point_max_vs_date = long_data_raw.groupby(long_data_raw['datetime'])['deltaprice'].max() #统计 最大盈亏 vs 日期
        long_deal_point_min_vs_date = long_data_raw.groupby(long_data_raw['datetime'])['deltaprice'].min()
        long_deal_point_max_vs_date[long_deal_point_max_vs_date < 0] = 0
        long_deal_point_min_vs_date[long_deal_point_min_vs_date > 0] = 0
        short_deal_point_max_vs_date = short_data_raw.groupby(short_data_raw['datetime'])['deltaprice'].max() #统计 最大盈亏 vs 日期
        short_deal_point_min_vs_date = short_data_raw.groupby(short_data_raw['datetime'])['deltaprice'].min()
        short_deal_point_max_vs_date[short_deal_point_max_vs_date < 0] = 0
        short_deal_point_min_vs_date[short_deal_point_min_vs_date > 0] = 0
        
        
        #############      作图         ##################
        
        fig,ax = plt.subplots(4,2, figsize=(15,20))
        #fig,ax = plt.subplots(3,2)
        plt.subplot(4,2,1)
        plt.bar(long_point_stat.index, long_point_stat)
        plt.xlabel('Point')
        plt.ylabel('Times')
        plt.title('long point')
        
        plt.subplot(4,2,2)
        plt.bar(short_point_stat.index, short_point_stat)
        plt.xlabel('Point')
        plt.ylabel('Times')
        plt.title('short point')
        
        plt.subplot(4,2,3)
        plt.bar(long_deal_stat.index, long_deal_stat)
        plt.xticks(rotation = 90)
        plt.tick_params(labelsize=10)
        plt.xlabel('Date')
        plt.ylabel('Times')
        plt.title('long deal date stat')
        
        plt.subplot(4,2,4)
        plt.bar(short_deal_stat.index, short_deal_stat)
        plt.xticks(rotation = 90)
        plt.xlabel('Date')
        plt.ylabel('Times')
        plt.title('short deal date stat')
        
        plt.subplot(4,2,5)
        plt.bar(long_deal_point_vs_date.index, long_deal_point_vs_date)
        plt.xticks(rotation = 90)
        plt.xlabel('Date')
        plt.ylabel('Point')
        plt.title('long deal point vs date')
        
        plt.subplot(4,2,6)
        plt.bar(short_deal_point_vs_date.index, short_deal_point_vs_date)
        plt.xticks(rotation = 90)
        plt.xlabel('Date')
        plt.ylabel('Point')
        plt.title('short deal point vs date')
        
        plt.subplot(4,2,7)
        plt.bar(long_deal_point_max_vs_date.index, long_deal_point_max_vs_date)
        plt.bar(long_deal_point_min_vs_date.index, long_deal_point_min_vs_date)
        plt.xticks(rotation = 90)
        plt.xlabel('Date')
        plt.ylabel('Point')
        plt.title('long deal point max min vs date')
        
        
        plt.subplot(4,2,8)
        plt.bar(short_deal_point_max_vs_date.index, short_deal_point_max_vs_date)
        plt.bar(short_deal_point_min_vs_date.index, short_deal_point_min_vs_date)
        plt.xticks(rotation = 90)
        plt.xlabel('Date')
        plt.ylabel('Point')
        plt.title('short deal point max min vs date')
        
        plt.subplots_adjust(hspace = 0.5)
        # workbook_root_dir = '/home/yanchao/武器库/zwf-program/test/'
        save_root_dir = output_dir
        workbook = 'starquantbactest'
        pltsavename = workbook[:-5] + '.png'
        # plt.savefig(save_root_dir + workbook[:-5] + '/' + pltsavename) 
        plt.savefig(save_root_dir +  '/'+ pltsavename)
        plt.close()        
        
# zwf kline analysis
        resample_timescale = '1min'  # '5min', 
        ShortTimePeriod = 5 # min
        LongTimePeriod = 50 # min
        for sym in symbols:
            hist_file = os.path.join(hist_dir, "%s.csv" % sym)
            data = pd.io.parsers.read_csv(
                hist_file, header=0, parse_dates=True,
                names=(
                    "datetime", "price", "quantity","totalq","position","b1price","b1size",
                    "s1price", "s1size", "bors"
                )
            )
            data["datetime"]=pd.to_datetime(data["datetime"],format='%Y-%m-%d %H:%M:%S')
            
            data_raw = data
            data_raw['date'] = data_raw['datetime'].apply(lambda x: x.strftime('%Y-%m-%d'))
            data_raw['time'] = data_raw['datetime'].apply(lambda x: x.strftime('%H:%M:%S'))
            data_raw.set_index('datetime',inplace=True)            
            days = (data_raw.drop_duplicates(['date']).date).reset_index(drop=True)  # 日期数组
            deal_data = self._df_trades
            #deal_data['datetime'] = pd.to_datetime(deal_data["datetime"],format='%Y-%m-%d %H:%M:%S')
            deal_data['date'] = deal_data['datetime'].apply(lambda x: x.strftime('%Y-%m-%d'))
            deal_data['time'] = deal_data['datetime'].apply(lambda x: x.strftime('%H:%M:%S'))
            #deal_data['date'] = deal_data['date'].apply(pd.Timestamp.date)
            #deal_data['time'] = deal_data['time'].apply(pd.Timestamp.time)            
            for date in deal_data.drop_duplicates(['date']).date:
                end_time = date + ' 23:59:00'
                #end_time = pd.Timestamp(date) + timedelta(hours=23,minutes = 59)
               # end_time = (pd.Timestamp(date) + timedelta(hours=23,minutes = 59)).strftime('%Y-%m-%d %H:%M:%S')  #string
        #       start_time =(parse(end_time) - timedelta(1,14*3600+59*60)).strftime('%Y-%m-%d %H:%M:%S')  #前一天的09:00
                #start_time_day = ''.join(days[days[days == date].index-1].values)
                #start_time = (parse(start_time_day + ' 09:00:00') - timedelta(0,12*3600)).strftime('%Y-%m-%d %H:%M:%S')
                start_time_day = ''.join(days[days[days == date].index-1].values)
                #start_time_day = days[days[days == date].index-1].values
                start_time = (parse(start_time_day + ' 09:00:00') - timedelta(0,12*3600)).strftime('%Y-%m-%d %H:%M:%S')
                #print(start_time_day)
                #type(start_time_day)
                #start_time = pd.Timestamp(start_time_day) - timedelta(0,3*3600)
                in_date = deal_data[(deal_data['date'] == date) & (np.mod(deal_data.index,2) == 0)]
                Time_in_deal = list(in_date.date + ' ' + in_date.time)
                
                #in_date.set_index('datetime',inplace=True,drop=False)
                #print(in_date)
                #in_date.info()
                #Time_in_deal = in_date['datetime']
                #Time_in_deal.index.rename('Time',inplace=True)
                #Time_in_deal_pd = Time_in_deal
                datestimeInd_Time_in_deal = pd.DatetimeIndex(Time_in_deal)
                Time_in_deal_pd = pd.DataFrame(Time_in_deal,\
                                   columns = ['Time'], index = datestimeInd_Time_in_deal)
                
                Time_in_deal_resample = (Time_in_deal_pd.resample(resample_timescale).max()).dropna(axis = 0, how = 'any')
            
                out_date = deal_data[(deal_data['date'] == date) & (np.mod(deal_data.index,2) == 1)]
                #out_date.set_index('datetime',inplace=True,drop=False)
                #Time_out_deal = out_date['datetime']
                Time_out_deal = list(out_date.date + ' ' + out_date.time)
                #Time_out_deal.index.rename('Time',inplace=True)
                #Time_out_deal_pd = Time_out_deal
                datestimeInd_Time_out_deal = pd.DatetimeIndex(Time_out_deal)
                Time_out_deal_pd = pd.DataFrame(Time_out_deal,\
                                   columns = ['Time'], index = datestimeInd_Time_out_deal)
                Time_out_deal_resample = (Time_out_deal_pd.resample(resample_timescale).max()).dropna(axis = 0, how = 'any')
            
            # 出场出场价格
        #    Price_in_deal_pd = pd.DataFrame(list(in_date.price),\
        #                          columns = ['price'], index = datestimeInd_Time_in_deal)
        #    Price_in_deal_resample = (Price_in_deal_pd.resample(resample_timescale).max()).dropna(axis = 0, how = 'any')
        #    Price_out_deal_pd = pd.DataFrame(list(out_date.price),\
        #                          columns = ['price'], index = datestimeInd_Time_out_deal)
        #    Price_out_deal_resample = (Price_out_deal_pd.resample(resample_timescale).max()).dropna(axis = 0, how = 'any')    
            
                #printtime = start_time.strftime('%Y%m%d')  + '_to_' + end_time.strftime('%Y%m%d')   #  输出时间
                printtime = start_time[:10]  + '_to_' + end_time[:10]
            
            #持仓过夜  
        #    if out_date['开/平'].iloc[0] == '平' :    #持仓过夜
                if (out_date['positioneffect'] == 'CLOSE').any():
                    end_time = date + ' 23:59:00'
                    openqty_day = deal_data.iloc[out_date.iloc[0:1].index - 1]['date'].tolist()[0]
                    start_time_day = ''.join(days[days[days == openqty_day].index].values)
                    start_time = (parse(start_time_day + ' 09:00:00') - timedelta(0,12*3600)).strftime('%Y-%m-%d %H:%M:%S')
                    
                    in_date_lastdate = deal_data.iloc[out_date.iloc[0:1].index - 1]
                    in_date = pd.merge(in_date_lastdate, in_date, how='outer')
                    Time_in_deal = list(in_date.date + ' ' + in_date.time)
                    datestimeInd_Time_in_deal = pd.DatetimeIndex(Time_in_deal)
                    Time_in_deal_pd = pd.DataFrame(Time_in_deal,\
                                        columns = ['Time'], index = datestimeInd_Time_in_deal)
                    Time_in_deal_resample = (Time_in_deal_pd.resample(resample_timescale).max()).dropna(axis = 0, how = 'any')
                    
                    #printtime = start_time.strftime('%Y%m%d')  + '_to_' + end_time.strftime('%Y%m%d') + 'notClose'
                    printtime = start_time[:10]  + '_to_' + end_time[:10] + 'notClose'
                
            #        out_date = out_date[:1]
            #        Time_out_deal = list(out_date.日期 + ' ' + out_date.时间)
            #        datestimeInd_Time_out_deal = pd.DatetimeIndex(Time_out_deal)
            #        Time_out_deal_pd = pd.DataFrame(Time_out_deal,\
            #                              columns = ['Time'], index = datestimeInd_Time_out_deal)
            #        Time_out_deal_resample = (Time_out_deal_pd.resample(resample_timescale).max()).dropna(axis = 0, how = 'any')   
                #持仓过夜 end    
                    
                # 入场出场价格     
                Price_in_deal_pd = pd.DataFrame(np.array(in_date[['price','amount']]),\
                                                columns = ['price','amount'], index = datestimeInd_Time_in_deal)
                Price_in_deal_resample = (Price_in_deal_pd.resample(resample_timescale).max()).dropna(axis = 0, how = 'any')
                Price_out_deal_pd = pd.DataFrame(np.array(out_date[['price','amount']]),\
                                                columns = ['price','amount'], index = datestimeInd_Time_out_deal)
                Price_out_deal_resample = (Price_out_deal_pd.resample(resample_timescale).max()).dropna(axis = 0, how = 'any')  
                # 入场出场价格 end    
            
           
            
            
             # 特殊时间点
                Time_special = [start_time_day + ' 9:01:00', start_time_day + ' 11:29:00', start_time_day + ' 14:59:00', date + ' 09:01:00' ,date + ' 11:29:00', date + ' 14:59:00']   # 特殊时间点
                Time_special_resample = (pd.DataFrame(Time_special,\
                                    columns = ['Time'], index = pd.DatetimeIndex(Time_special)).resample(resample_timescale).max()).dropna(axis = 0, how = 'any')
                
                ##################### K line ######################
                
                
                #
                #
                in_time_list = list(Time_in_deal_resample.index)
                out_time_list = list(Time_out_deal_resample.index)
                special_time_list = list(Time_special_resample.index)
                #in_time_list = ['2016-10-25 09:31:00', '2016-10-25 09:34:00', '2016-10-25 10:00:00', 
                #           '2016-10-25 10:31:00', '2016-10-25 10:36:00', '2016-10-25 13:31:00',
                #           '2016-10-25 21:13:00', '2016-10-25 21:48:00']
                #out_time_list = ['2016-10-25 09:34:00', '2016-10-25 09:53:00', '2016-10-25 10:05:00',
                #            '2016-10-25 10:32:00', '2016-10-25 10:41:00', '2016-10-25 14:51:00',
                #            '2016-10-25 21:16:00', '2016-10-25 21:52:00']
                #
                id_in = []; time_in = []; 
                id_out = []; time_out = []; 
                in_price = pd.DataFrame(columns = ['price','amount']); 
                out_price = pd.DataFrame(columns = ['price','amount']); 
                id_special = []; time_special = [];
            
            
            
            #  切片    
                data = data_raw[start_time : end_time]
                Time = data.date + ' ' + data.time
                
                datestimeInd = pd.DatetimeIndex(Time)
                
                # 重取样
                tseries_price = pd.Series(np.array(data['price']),\
                                        index = datestimeInd)
                tseries_quan = pd.DataFrame(np.array(data[['quantity']]),\
                                    columns = ['quantity'], index = datestimeInd)
                tseries_position = pd.DataFrame(np.array(data[['position']]),\
                                    columns = ['position'], index = datestimeInd)
                
                tseries_price_resample_unwash = tseries_price.resample(resample_timescale).ohlc()
                tseries_quan_resample_unwash = tseries_quan.resample(resample_timescale).sum(min_count = 1)
                tseries_position_resample_unwash = tseries_position.resample(resample_timescale).sum(min_count = 1)
                
                tseries_price_resample = tseries_price_resample_unwash.dropna(axis = 0, how = 'any')
                tseries_quan_resample = tseries_quan_resample_unwash.dropna(axis = 0, how = 'any')
                tseries_position_resample2 = tseries_position_resample_unwash.dropna(axis = 0, how = 'any')
                

                #tseries_position_resample = tseries_position_resample2.cumsum()

                tseries_position_resample = (pd.DataFrame(np.array(tseries_position_resample2['position'] * (tseries_position_resample2.position < 100000)),\
                            columns = ['position'], index = tseries_position_resample2.index)).cumsum()   ##### 处理掉 开盘前 的position
                
                del(tseries_price, tseries_quan, tseries_position, tseries_price_resample_unwash, tseries_quan_resample_unwash,tseries_position_resample_unwash)
                
                
                ################################### 作图  ###########################################
                time_ktimescale_str = list(map(str, tseries_price_resample.index))
                time_future_ktimescale = list(map(parse, time_ktimescale_str))
                
                
                t = date2num(time_future_ktimescale)  
                #t_in = date2num(parse(in_time_list)) 
                #t_out = date2num(parse(out_time_list))
                t_continuous = np.arange(t[0],t[0] + (t[1] - t[0])*len(t),t[1] - t[0])
                tseries_price_resample.insert(0, 'time', t_continuous)
                
                tseries_quan_resample.insert(0, 'time', tseries_quan_resample.index)
                tseries_quan_resample_up = pd.DataFrame(np.array(tseries_quan_resample['quantity'] * (tseries_price_resample.open <= tseries_price_resample.close)),\
                            columns = ['quantity_up'], index = tseries_quan_resample.index)
                tseries_quan_resample_up.insert(0, 'time', tseries_quan_resample.index)
                tseries_quan_resample_down = pd.DataFrame(np.array(tseries_quan_resample['quantity'] * (tseries_price_resample.open > tseries_price_resample.close)),\
                            columns = ['quantity_down'], index = tseries_quan_resample.index)
                tseries_quan_resample_down.insert(0, 'time', tseries_quan_resample.index)
                
                tseries_position_resample.insert(0, 'time', tseries_position_resample.index)
                
                # 标注开始结束时间
                tseries_price_resample.insert(0, 'id', np.arange(tseries_price_resample.shape[0]))
                
                counter = 0
                for in_time in in_time_list:
                    id_in.append(tseries_price_resample[in_time:in_time]['id'][0])
                    time_in.append(tseries_price_resample[in_time:in_time]['time'][0])  # time_in 是kline 里面的假时间
            #        in_price = in_price.append(Price_in_deal_resample[in_time:in_time]['price','amount'][0])
                    counter = counter + 1
                
                counter = 0
                for out_time in out_time_list:
                    id_out.append(tseries_price_resample[out_time:out_time]['id'][0])
                    time_out.append(tseries_price_resample[out_time:out_time]['time'][0])  # time_out 是kline 里面的假时间
            #        out_price = out_price.append(Price_out_deal_resample[out_time:out_time]['price','amount'][0])
                    counter = counter + 1
                    
                in_price = Price_in_deal_resample
                out_price = Price_out_deal_resample
                
                    
            #    id_in_maxprice = tseries_price_resample['high'].max()
            #    id_in_minprice = tseries_price_resample['high'].min()
                id_in_maxquan = tseries_quan_resample['quantity'].max()
                id_in_minquan = tseries_quan_resample['quantity'].min()
            #    id_out_maxprice = id_in_maxprice
            #    id_out_minprice = id_in_minprice
                id_out_maxquan = id_in_maxquan
                id_out_minquan = id_in_minquan
                
                id_special_minprice = tseries_price_resample['high'].min()
                
                for special_time in special_time_list:
                    id_special.append(tseries_price_resample[special_time:special_time]['id'][0])
                    time_special.append(tseries_price_resample[special_time:special_time]['time'][0])
                
                
                # 一天最大最小值标注
                dayone_max = tseries_price_resample[start_time: start_time_day + ' 15:00:00'] \
                    [tseries_price_resample[start_time: start_time_day + ' 15:00:00']['high']  \
                    == tseries_price_resample[start_time: start_time_day + ' 15:00:00']['high'].max()][['id','time','high']]
                    
                dayone_min = tseries_price_resample[start_time: start_time_day + ' 15:00:00'] \
                    [tseries_price_resample[start_time: start_time_day + ' 15:00:00']['low']  \
                    == tseries_price_resample[start_time: start_time_day + ' 15:00:00']['low'].min()][['id','time','low']] 
                    
                daytwo_max = tseries_price_resample[start_time_day + ' 21:00:00' : date + ' 21:00:00'] \
                    [tseries_price_resample[start_time_day + ' 21:00:00' : date + ' 21:00:00']['high']  \
                    == tseries_price_resample[start_time_day + ' 21:00:00' : date + ' 21:00:00']['high'].max()][['id','time','high']]
                    
                daytwo_min = tseries_price_resample[start_time_day + ' 21:00:00' : date + ' 21:00:00'] \
                    [tseries_price_resample[start_time_day + ' 21:00:00' : date + ' 21:00:00']['low']  \
                    == tseries_price_resample[start_time_day + ' 21:00:00' : date + ' 21:00:00']['low'].min()][['id','time','low']]     
                
                
                
    #            daymaxmin = start_time[:10]
    #            maxmin_night_start_time = start_time
    #            maxmin_night_end_time = start_time[:10] + ' 23:00:00'   #有夜盘
    #            dayone_max = dayone_max.append(tseries_price_resample[maxmin_night_start_time : maxmin_night_end_time] \
    #                [tseries_price_resample[maxmin_night_start_time : maxmin_night_end_time]['high']  \
    #                == tseries_price_resample[maxmin_night_start_time : maxmin_night_end_time]['high'].max()][['id','time','high']])
    #            
    #            daymaxmin = (parse(daymaxmin + ' 00:00:01') + timedelta(0,24*3600)).strftime('%Y-%m-%d')
    #            maxmin_day_start_time = daymaxmin + ' 09:00:00'
    #            maxmin_day_end_time = daymaxmin + ' 15:00:00'
    #            
    #            dayone_max = dayone_max.append(tseries_price_resample[maxmin_day_start_time : maxmin_day_end_time] \
    #                [tseries_price_resample[maxmin_day_start_time : maxmin_day_end_time]['high']  \
    #                == tseries_price_resample[maxmin_day_start_time : maxmin_day_end_time]['high'].max()][['id','time','high']])
                    
                
                    
                
                idx_pxy = np.arange(tseries_position_resample.shape[0])
                def x_fmt_func(x, pos=None):
                    idx = np.clip(int(x+0.5), 0, tseries_position_resample.shape[0]-1)
                    return tseries_position_resample['time'].iat[idx]
                
                datas = [tuple(x) for x in tseries_price_resample[['time', 'open', 'high', 'low', 'close']].to_records(index=False)]
                
                
                
                #        fig, (ax1, ax2) = plt.subplots(2, sharex=True, figsize=(15,8))
                fig, (ax1, ax2) = plt.subplots(2, figsize=(30,16))
                
                #        ax1.xaxis_date()  
                ax1.set_title(start_time + ' to ' + end_time +'-' + resample_timescale)
                mpf.candlestick_ohlc(ax1,datas,width=30*0.8/4500/tseries_position_resample.shape[0],colorup='lightslategray',colordown='black', alpha=1.0) 
            #    plt.tick_params(labelsize=15)
            #    for time_in_i in time_in:
            #        ax1.plot([time_in_i,time_in_i],[id_in_minprice,id_in_maxprice],linestyle='-',color='blue', linewidth = 1)
            #    for time_out_i in time_out:   
            #        ax1.plot([time_out_i,time_out_i],[id_out_minprice,id_out_maxprice],linestyle='--',color='red', linewidth = 1)
                
                #  进出场标记
                counter = 0
                for  counter in range(len(time_in)):
                    if in_price['amount'].iloc[counter] > 0 :
                        ax1.annotate('%s' % (in_price['price'].iloc[counter]) , 
                                    xy=(time_in[counter], in_price['price'].iloc[counter] + 0),
                                    xytext=(0, +35), textcoords='offset points', fontsize=10, color = 'blue',
                                    arrowprops=dict(ec='blue', arrowstyle="<-"), horizontalalignment = 'center', verticalalignment = 'top')
                    elif in_price['amount'].iloc[counter] < 0 :
                        ax1.annotate('%s' % (in_price['price'].iloc[counter]) ,
                                    xy=(time_in[counter], in_price['price'].iloc[counter] + 0),
                                    xytext=(0, +35), textcoords='offset points', fontsize=10, color = 'blue',
                                    arrowprops=dict(ec='blue', arrowstyle="->"), horizontalalignment = 'center', verticalalignment = 'top')
                    counter = counter + 1
                    
                counter = 0
                for counter in range(len(time_out)):
                    if out_price['amount'].iloc[counter] > 0 :
                        ax1.annotate('%s' % (out_price['price'].iloc[counter]) ,
                                    xy=(time_out[counter], out_price['price'].iloc[counter] - 0),
                                    xytext=(0, -35), textcoords='offset points', fontsize=10, color = 'red',
                                    arrowprops=dict(ec='red', arrowstyle="->"), horizontalalignment = 'center', verticalalignment = 'top')
                    elif out_price['amount'].iloc[counter] < 0 :
                        ax1.annotate('%s' % (out_price['price'].iloc[counter]) ,
                                    xy=(time_out[counter], out_price['price'].iloc[counter] - 0),
                                    xytext=(0, -35), textcoords='offset points', fontsize=10, color = 'red',
                                    arrowprops=dict(ec='red', arrowstyle="<-"), horizontalalignment = 'center', verticalalignment = 'top')
                    counter = counter + 1
                
                
                #   最大最小值 标记 
                ax1.annotate('%s' % (dayone_max['high'][0]) ,
                        xy=(dayone_max['time'][0], dayone_max['high'][0]),
                        xytext=(0, +50), textcoords='offset points', fontsize=10, color = 'black',
                        arrowprops=dict(ec='black', arrowstyle="->"), horizontalalignment = 'center', verticalalignment = 'top')
                ax1.annotate('%s' % (dayone_min['low'][0]) ,
                        xy=(dayone_min['time'][0], dayone_min['low'][0]),
                        xytext=(0, -50), textcoords='offset points', fontsize=10, color = 'black',
                        arrowprops=dict(ec='black', arrowstyle="->"), horizontalalignment = 'center', verticalalignment = 'top')
                # ax1.annotate('%s' % (daytwo_max['high'][0]) ,
                #         xy=(daytwo_max['time'][0], daytwo_max['high'][0]),
                #         xytext=(0, +50), textcoords='offset points', fontsize=10, color = 'black',
                #         arrowprops=dict(ec='black', arrowstyle="->"), horizontalalignment = 'center', verticalalignment = 'top')
                # ax1.annotate('%s' % (daytwo_min['low'][0]) ,
                #         xy=(daytwo_min['time'][0], daytwo_min['low'][0]),
                #         xytext=(0, -50), textcoords='offset points', fontsize=10, color = 'black',
                #         arrowprops=dict(ec='black', arrowstyle="->"), horizontalalignment = 'center', verticalalignment = 'top')
                
                
                
                #移动平均线
                kline_rolling_mean1 = tseries_price_resample.rolling(window= ShortTimePeriod,center=False).mean();
                kline_rolling_mean1.drop(['id','time'], axis = 1, inplace=True);
                kline_rolling_mean1.insert(0,'id',tseries_price_resample['id'])
                kline_rolling_mean1.insert(1,'time',tseries_price_resample['time'])          
                
                kline_rolling_mean2 = tseries_price_resample.rolling(window= LongTimePeriod,center=False).mean();
                kline_rolling_mean2.drop(['id','time'], axis = 1, inplace=True);
                kline_rolling_mean2.insert(0,'id',tseries_price_resample['id'])
                kline_rolling_mean2.insert(1,'time',tseries_price_resample['time'])
                
                
                #ax1.plot(kline_rolling_mean1.time, kline_rolling_mean1.close, linestyle='-',color='yellow', linewidth = 2)
                #ax1.plot(kline_rolling_mean2.time, kline_rolling_mean2.close, linestyle='-',color='magenta', linewidth = 2)

                ax1.plot(kline_rolling_mean1.time, kline_rolling_mean1.close, linestyle='--',color='black', linewidth = 2)
                ax1.plot(kline_rolling_mean2.time, kline_rolling_mean2.close, linestyle=':',color='black', linewidth = 2)
                
                
                
                for time_special_i in time_special:   
                    ax1.plot([time_special_i,time_special_i],[id_special_minprice,id_special_minprice],marker='o',color='hotpink')
                
                
                ax1.set_xticklabels('')
                ax1.set_ylabel('Price')
                ax1.grid(True) 
                
                
                
                ax2.bar(idx_pxy,tseries_quan_resample_up['quantity_up'], color="lightslategray",width= 0.5)
                ax2.bar(idx_pxy,tseries_quan_resample_down['quantity_down'], color="black",width= 0.5)
                for id_in_i in id_in:
                    ax2.plot([id_in_i,id_in_i],[id_in_minquan,id_in_maxquan],linestyle='-',color='blue', linewidth = 1) 

                for id_out_i in id_out:    
                    ax2.plot([id_out_i,id_out_i],[id_out_minquan,id_out_maxquan],linestyle='--',color='red', linewidth = 1)
                for id_special_i in id_special:    
                    ax2.plot([id_special_i,id_special_i],[id_out_minquan,id_out_minquan],marker='o',color='hotpink')        
                    
                ax2.xaxis.set_major_formatter(mtk.FuncFormatter(x_fmt_func))
                
            #    plt.tick_params(labelsize=15)
                ax2.set_ylabel('Quantity')
                ax2.grid(True)     
                
                xlabels = ax2.get_xticklabels()
                for xl in xlabels:
                    xl.set_rotation(30)
                
                ax3= ax2.twinx()
                ax3.plot(idx_pxy,tseries_position_resample['position'], color="black", linewidth=1, linestyle="-")    
                ax3.xaxis.set_major_formatter(mtk.FuncFormatter(x_fmt_func))
            #    plt.tick_params(labelsize=15)
                ax3.set_ylabel('Position')
                
            #    printtime = start_time[:10]  + '_to_' + end_time[:10] 
                
                pltsavename = printtime + '-' + resample_timescale + '.png'
                plt.savefig(output_dir + '/' + pltsavename) 
    #            plt.savefig(save_root_dir + pltsavename) 
                plt.close()
            #    plt.show()

    # ------------------------------- end of public functions -----------------------------#
