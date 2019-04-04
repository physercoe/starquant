import time
import talib
import datetime
from ..strategy_base import StrategyBase
from ...order.order_event import OrderEvent
from ...order.order_type import OrderType
from ...order.order_flag import OrderFlag
from ...position.margin import marginrate
from datetime import timedelta
from pandas import Timestamp
import pandas as pd
import numpy as np

class TestStrategy(StrategyBase):
    """
    high point sell and low point buy
    """
    def __init__(self, events_engine,order_manager,_portfolio_manager_manager,
                start_time=Timestamp('1970-01-01'),end_time = Timestamp('1970-01-01'),
                histbardayfile="histbar_day.csv",histbarhourfile="histbar_hour.csv"):
        super(TestStrategy, self).__init__(events_engine,order_manager,_portfolio_manager_manager)
        """
        state:action indicator
        **trig:action conditon
        """
        self._histbar_day = pd.read_csv(histbardayfile,header = 0,index_col = 1)
        self._histbar_day.index = pd.to_datetime(self._histbar_day.index,format = '%Y%m%d')
        self._histbar_hour = pd.read_csv(histbarhourfile,header = 0,index_col = 1)
        self._histbar_hour = pd.to_datetime(self._histbar_hour.index,format='%Y-%m-%d %H:%M:%S')

        self.now = start_time
        self.s1 = "SHFE F NI 1811"
        self.s2 = "M888"
        self.s3 = "M1609"
        
        self.ifcangwei = False       #是否复利加仓
        
        self.cangwei = {}
        self.cangwei[self.s1] = 0.7
        self.cangwei[self.s2] = 0.7    
        self.cangwei[self.s3] = 0.7    
        
        
        self.firedFirst = False
        self.firedSecond = True
        self.firedNightOpen = False
        self.firedDayOpen = False
        self.firedMA = True
        self.fireRecover_and_Move = True

        self.firedAutoObstructionResistance = True  #是否用自动支撑阻力
        self.AutoObstructionResistanceMinuteNumber = 12
        self.IFAOR = False
        self.FactorAOR = 0.25
        self.FactorShort_Long = 1
        self.IFLocalPointExist = False
        self.LocalLow = {}
        self.LocalHigh = {}







        self.fired = {}
        
        self.fired[self.s1] = False
        self.fired[self.s2] = False
        self.fired[self.s3] = False

    #是否二重日均线
        self.IfTwoMA = {}
        self.IfTwoMA[self.s1] = False
        self.IfTwoMA[self.s2] = False
        self.IfTwoMA[self.s3] = False   
    #是否二重日均线end
    #是否三重日均线
        self.IfThreeMA = {}
        self.IfThreeMA[self.s1] = False
        self.IfThreeMA[self.s2] = False
        self.IfThreeMA[self.s3] = False   
    #是否三重日均线end

    #是否两段高低点
        self.IfTwoHL = {}
        self.IfTwoHL[self.s1] = False
        self.IfTwoHL[self.s2] = False
        self.IfTwoHL[self.s3] = False   
    #是否两段高低点end
        

    #是否移动止损    
        self.firedOpenMoveStopLoss = {}     #移动止损
        
        self.firedOpenMoveStopLoss[self.s1] = True
        self.firedOpenMoveStopLoss[self.s2] = False
        self.firedOpenMoveStopLoss[self.s3] = False
        self.MoveFactor = 0.65            #移动止损因子（在0.5左右）
        self.MoveFactorForPrice = 0.01    #单笔浮盈损失最大因子（在0.01左右）
    #是否移动止损end


    #是否时间止损    
        self.firedOpenTimeStopLoss = {}     #移动止损
        
        self.firedOpenTimeStopLoss[self.s1] = False
        self.firedOpenTimeStopLoss[self.s2] = False
        self.firedOpenTimeStopLoss[self.s3] = False

    #是否时间止损end

    #开仓时间    
        self.OpenPositionTime = {}     #移动止损
    #开仓时间end

    #时间止损分钟数
        self.stoplosstimeminute = {}
        self.stoplosstimeminute[self.s1] = 10
        self.stoplosstimeminute[self.s2] = 3
        self.stoplosstimeminute[self.s3] = 3    
    #时间止损分钟数end   

    #是否恢复成本价
        self.firedOpenRecoverCost = {}      #恢复成本价
        
        self.firedOpenRecoverCost[self.s1] = True
        self.firedOpenRecoverCost[self.s2] = False
        self.firedOpenRecoverCost[self.s3] = False
    #是否恢复成本价end

    #是否移动平均线止损
        self.firedOpenMoveAverageStopLoss = {}     #移动平均线止损
        
        self.firedOpenMoveAverageStopLoss[self.s1] = False
        self.firedOpenMoveAverageStopLoss[self.s2] = False
        self.firedOpenMoveAverageStopLoss[self.s3] = False
    #是否移动平均线止损end

    #是否持仓过夜
        self.CloseClose = {}
        
        self.CloseClose[self.s1] = False      #False持仓过夜，True日内平仓
        self.CloseClose[self.s2] = False
        self.CloseClose[self.s3] = False
    #是否持仓过夜end

    #定义金叉死叉
        self.Goldcross = {}
        self.Goldcross[self.s1] = False
        self.Goldcross[self.s2] = False
        self.Goldcross[self.s3] = False    

        self.Deadcross = {}
        self.Deadcross[self.s1] = False
        self.Deadcross[self.s2] = False
        self.Deadcross[self.s3] = False       
    #定义金叉死叉end

        self.selfs = [self.s1]
        
    #定义开收盘时间
        self.OpenHour = {}
        self.CloseHour = {}
        self.CloseMinute = {}
        
        self.OpenHour[self.s1] = 21
        self.OpenHour[self.s2] = 21
        self.OpenHour[self.s3] = 21
        
        self.CloseHour[self.s1] = 23
        self.CloseHour[self.s2] = 23
        self.CloseHour[self.s3] = 23

        self.CloseMinute[self.s1] = 30
        self.CloseMinute[self.s2] = 30
        self.CloseMinute[self.s3] = 30
    #定义开收盘时间end

    #定义开收盘不交易分钟数
        self.opencloseminute = {}
        self.opencloseminute[self.s1] = 1
        self.opencloseminute[self.s2] = 5
        self.opencloseminute[self.s3] = 5
    #定义开收盘不交易分钟数end

    #定义append数组
        self.ticklastprice = {}
        self.ticklastprice[self.s1] = []
        self.ticklastprice[self.s2] = []
        self.ticklastprice[self.s2] = []
        
        
        self.ticklastpriceTime = {}
        self.ticklastpriceTime[self.s1] = []
        self.ticklastpriceTime[self.s2] = []
        self.ticklastpriceTime[self.s2] = []
        
    #定义append数组end

    #定义止损点位
        self.zhisundianwei = {}
        self.zhisundianwei[self.s1] = 20 #20
        self.zhisundianwei[self.s2] = 3
        self.zhisundianwei[self.s3] = 3
    #定义止损点位end

    #时间止损止盈点位
        self.stoplosstimePoint = {}
        self.stoplosstimePoint[self.s1] = 15 #15
        self.stoplosstimePoint[self.s2] = 3
        self.stoplosstimePoint[self.s3] = 3   
    #时间止损止盈点位end

    #移动止损止盈点位
        self.stoplossMovePoint = {}
        self.stoplossMovePoint[self.s1] = 40  #40
        self.stoplossMovePoint[self.s2] = 3
        self.stoplossMovePoint[self.s3] = 3   
    #移动止损止盈点位end





    #移动止损因子
        self.stoplosstimeFactor = {}
    #移动止损因子end

    #允许入场滑点
        self.fudong = {}
        self.fudong[self.s1] = 50
        self.fudong[self.s2] = 3
        self.fudong[self.s3] = 3   
    #允许入场滑点end    


    #日均线周期设置
        self.SHORTPERIOD = 2#5
        self.MEANPERIOD = 3#10
        self.LONGPERIOD = 4#20
        self.OBSERVATION = 5#50
    #日均线周期设置end    

    #分钟均线周期设置
        self.SHORTPERIOD2 = 5
        self.MEANPERIOD2 = 10
        self.LONGPERIOD2 = 20
        self.OBSERVATION2 = 100
    #分钟均线周期设置end  

        self.minlastprice = {}
        self.minlastprice[self.s1] = np.full([1,self.OBSERVATION2],np.nan)[0]
    #    self.minlastprice[self.s1] = []
        self.minlastprice[self.s2] = []
        self.minlastprice[self.s3] = []

    #A.D.X指标设置
        self.ADX = 40                          #ADX指标
        self.ADXTimePeriod = 4                 #ADX周期
    #A.D.X指标设置end   

    #变量设置
        self.HighPoint = {}
        self.LowPoint = {}
        self.HighPoint[self.s1] = 104070
        self.LowPoint[self.s1] = 101843
        self.YestodayHighPoint = {}
        self.YestodayLowPoint = {}
        self.YestodayHighPoint[self.s1] = 101520
        self.YestodayLowPoint[self.s1] = 99940
        self.HighLowFactor = {}
        self.HighLowFactor[self.s1] = 10
        self.HighLowFactor[self.s2] = 10
        self.HighLowFactor[self.s3] = 10
        
        self.High = {}
        self.Low = {}
        self.Close = {}
        self.HighMin = {}
        self.LowMin = {}
        self.CloseMin = {}

        self.buy_prices = {}
        self.buy_qty = {}
        self.buyStopLossPoint = {}
        self.buyStopLossPointTmp = {}
        self.pricesObstruction = {}


        self.sell_prices = {}
        self.sell_qty = {}
        self.sellStopLossPoint = {}
        self.sellStopLossPointTmp = {}
        self.pricesResistance = {}

        self.TimeStopLossTime = {}
        self.lastprice = {}
        self.AdxCondition = {}
        self.RealAdx = {}
        self.MA_S = {}
        self.MA_M = {}
        self.MA_L = {}
        self.MA_S2 = {}
        self.MA_M2 = {}
        self.MA_L2 = {}
        self.LongMeanCondition = {}
        self.ShortMeanCondition = {}
        self.LongCloseCondition = {}
        self.ShortCloseCondition = {}
        self.TendencyLong = {}
        self.TendencyShort = {}

        self.H1Pricetmp = {}  #买入后高点存储
        self.H1Pricetmp[self.s1] = []  
        self.H1Pricetmp[self.s2] = [] 
        self.H1Pricetmp[self.s3] = [] 
        self.H1Timetmp = {}
        self.list_betweenH1_High = {}
        self.list_betweenH1_High[self.s1] = []
        self.list_betweenH1_High[self.s2] = []
        self.list_betweenH1_High[self.s3] = []
        self.TillLastHighLimit = {} # 两个高点之间的时间间隔最小值(单位：分钟)
        self.TillLastHighLimit[self.s1] = 2
        self.TillLastHighLimit[self.s2] = 2
        self.TillLastHighLimit[self.s3] = 2
        
        
        self.L1Pricetmp = {}  #买入后低点存储
        self.L1Pricetmp[self.s1] = []  
        self.L1Pricetmp[self.s2] = [] 
        self.L1Pricetmp[self.s3] = [] 
        self.L1Timetmp = {}
        self.list_betweenL1_Low = {}
        self.list_betweenL1_Low[self.s1] = []
        self.list_betweenL1_Low[self.s2] = []
        self.list_betweenL1_Low[self.s3] = []
        self.TillLastLowLimit = {} # 两个高点之间的时间间隔最小值(单位：分钟)   
        self.TillLastLowLimit[self.s1] = self.TillLastHighLimit[self.s1]  
        self.TillLastLowLimit[self.s2] = self.TillLastHighLimit[self.s2]
        self.TillLastLowLimit[self.s2] = self.TillLastHighLimit[self.s2]
        
        
        self.BuyTime = {}   #买入时间
        self.list_AfterBuy = {}
        self.list_AfterBuy[self.s1] = []
        self.list_AfterBuy[self.s2] = []
        self.list_AfterBuy[self.s3] = []
        self.BuyRecoverTimeLimit = {}   # 距离Buy的时间(单位：分钟)  
        self.BuyRecoverTimeLimit[self.s1] = 15  
        self.BuyRecoverTimeLimit[self.s2] = 15  
        self.BuyRecoverTimeLimit[self.s3] = 15  
        self.BuyRecoverPointLimit = {}   # 距离Buy的点数(单位：跳钟)  
        self.BuyRecoverPointLimit[self.s1] = 10  
        self.BuyRecoverPointLimit[self.s2] = 5 
        self.BuyRecoverPointLimit[self.s3] = 5
        
        self.SellTime = {}   #卖出时间
        self.list_AfterSell = {}
        self.list_AfterSell[self.s1] = []
        self.list_AfterSell[self.s2] = []
        self.list_AfterSell[self.s3] = []
        self.SellRecoverTimeLimit = {}   # 距离Sell的时间(单位：分钟)  
        self.SellRecoverTimeLimit[self.s1] = self.BuyRecoverTimeLimit[self.s1]   
        self.SellRecoverTimeLimit[self.s2] = self.BuyRecoverTimeLimit[self.s2]   
        self.SellRecoverTimeLimit[self.s3] = self.BuyRecoverTimeLimit[self.s3]   
        self.SellRecoverPointLimit = {}   # 距离Sell的点数(单位：跳数)  
        self.SellRecoverPointLimit[self.s1] = self.BuyRecoverPointLimit[self.s1]  
        self.SellRecoverPointLimit[self.s2] = self.BuyRecoverPointLimit[self.s2]
        self.SellRecoverPointLimit[self.s3] = self.BuyRecoverPointLimit[self.s3]
        
        
        self.H2Price = {}
        self.BuyRecoverFactor = {}
        self.BuyRecoverFactor[self.s1] = 0.5
        self.BuyRecoverFactor[self.s2] = 0.5
        self.BuyRecoverFactor[self.s3] = 0.5
        
        self.L2Price = {}
        self.SellRecoverFactor = {}
        self.SellRecoverFactor[self.s1] = 0.5
        self.SellRecoverFactor[self.s2] = 0.5
        self.SellRecoverFactor[self.s3] = 0.5    
        
        # 两个高点的tick量小于 Len_list_limit,判断是连续上升
        self.Len_list_betweenH1_High_Limit = {}
        self.Len_list_betweenH1_High_Limit[self.s1] = 120
        self.Len_list_betweenH1_High_Limit[self.s2] = 120
        self.Len_list_betweenH1_High_Limit[self.s3] = 120
        
        self.Len_list_betweenL1_Low_Limit = {}
        self.Len_list_betweenL1_Low_Limit[self.s1] = 120
        self.Len_list_betweenL1_Low_Limit[self.s2] = 120
        self.Len_list_betweenL1_Low_Limit[self.s3] = 120
        
        #
        self.MinAfterH2 = {}
        self.MinAfterH2[self.s1] = []
        self.MinAfterH2[self.s2] = []
        self.MinAfterH2[self.s3] = []
        
        self.MaxAfterL2 = {}
        self.MaxAfterL2[self.s1] = []
        self.MaxAfterL2[self.s2] = []
        self.MaxAfterL2[self.s3] = []
        
        #两个高点的tick量大于Len_list_between_limit2,才判断是否有坑
        self.Len_list_betweenH1_High_Limit2 = {}
        self.Len_list_betweenH1_High_Limit2[self.s1] = 1000
        self.Len_list_betweenH1_High_Limit2[self.s2] = 1000
        self.Len_list_betweenH1_High_Limit2[self.s3] = 1000  
        
        self.Len_list_betweenL1_Low_Limit2 = {}
        self.Len_list_betweenL1_Low_Limit2[self.s1] = 1000
        self.Len_list_betweenL1_Low_Limit2[self.s2] = 1000
        self.Len_list_betweenL1_Low_Limit2[self.s3] = 1000
        
        #收盘前计算收益，小于BenifitBeforeClose个价位即平仓
        self.BenifitBeforeClose = {}
        self.BenifitBeforeClose[self.s1] = 5
        self.BenifitBeforeClose[self.s2] = 5
        self.BenifitBeforeClose[self.s1] = 5
        
        #持仓量移动均线
        self.firedPositionMA = True
        self.firedOpenMovePositionCriteria = {}
        self.firedOpenMovePositionCriteria[self.s1] = False
        self.firedOpenMovePositionCriteria[self.s2] = False
        self.firedOpenMovePositionCriteria[self.s3] = False
        
        self.IfPositionMA_Double = {}
        self.IfPositionMA_Double[self.s1] = False
        self.IfPositionMA_Double[self.s2] = False
        self.IfPositionMA_Double[self.s3] = False
        
        self.IfPositionMA_Tripe = {}
        self.IfPositionMA_Tripe[self.s1] = True
        self.IfPositionMA_Tripe[self.s2] = False
        self.IfPositionMA_Tripe[self.s3] = False
        
        
        self.PositionMove_SHORTPERIOD = 5
        self.PositionMove_MEANPERIOD = 20
        self.PositionMove_LONGPERIOD = 120
        self.PositionMove_OBSERVATION = 130
        
        self.PositionList = {}
        self.PositionList[self.s1] = np.full([1,self.PositionMove_OBSERVATION],np.nan)[0]
        self.PositionList[self.s2] = []
        self.PositionList[self.s3] = []
        
        self.Position_MACondition_Tripe = {}
        self.Position_MACondition_Double = {}
        
        self.PositionMA_S ={}
        self.PositionMA_M ={}
        self.PositionMA_L ={}
        
        #止损相位向后
        self.buyStopLossPoint_old = {}
        self.buyStopLossPoint_old[self.s1] = 0
        self.buyStopLossPoint_old[self.s2] = 0
        self.buyStopLossPoint_old[self.s3] = 0
        
        self.counter_buyStopLossPoint = {}
        self.counter_buyStopLossPoint[self.s1] = 0
        self.counter_buyStopLossPoint[self.s1] = 0
        self.counter_buyStopLossPoint[self.s1] = 0
        
        self.sellStopLossPoint_old = {}
        self.sellStopLossPoint_old[self.s1] = 0
        self.sellStopLossPoint_old[self.s2] = 0
        self.sellStopLossPoint_old[self.s3] = 0
        
        self.counter_sellStopLossPoint = {}
        self.counter_sellStopLossPoint[self.s1] = 0
        self.counter_sellStopLossPoint[self.s1] = 0
        self.counter_sellStopLossPoint[self.s1] = 0    

        #开始启动标志，对于实盘可能是任意时刻入场，之前的收盘期间的重置的变量firedfirst,firedsecond，firednightopen,firednight等无法得到赋值
        self.firststart = True

        #实盘仓位同步标志，策略发出订单后该变量为false，只有交易所返回成交和持仓变化信息时重置为true，在此时间间隔内策略不再交易,
        #该标志主要针对开仓，避免重复开仓
        self.orderfilled = True












    #变量设置end


# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
    def before_trading(self):
        pass

    def on_position(self,pos):
        if pos.source == self.id and pos.type in ['n','a']:
            self.orderfilled = True
    
    def on_fill(self,fill):
        # if fill.source = self.id
        #    self.orderfilled = True
        pass

    def on_tick(self, tick):
        # 开始编写你的主要的算法逻辑
        # tick 可以获取到当前订阅的合约的快照行情
        # self._portfolio_manager 可以获取到当前投资组合信息
        sym = tick.full_symbol
        self.now = tick.timestamp
        # print('line 303')   
        if (sym in self.selfs):              
            self.ticklastprice[sym].append(tick.price) 
            self.ticklastpriceTime[sym].append(self.now)
            self.buy_qty[sym] = self._portfolio_manager.positions[sym].buy_quantity
            self.sell_qty[sym] = self._portfolio_manager.positions[sym].sell_quantity
            self.buy_prices[sym] = self._portfolio_manager.positions[sym].avg_buy_price
            self.sell_prices[sym] = self._portfolio_manager.positions[sym].avg_sell_price      
            allmoney = self._portfolio_manager.get_total_value()         #总权益
#下午15点收盘判断高低点并且释放价格list            
            if self.now.hour == 14 and self.now.minute == 59 and self.now.second == 59 and self.firedSecond:

                self.HighPoint[sym] = max(self.ticklastprice[sym])
                self.LowPoint[sym] = min(self.ticklastprice[sym])
                self.YestodayHighPoint[sym] = self.HighPoint[sym]
                self.YestodayLowPoint[sym] = self.LowPoint[sym]
                print('下午15点收盘时确定最高点最低点',self.HighPoint[sym],self.LowPoint[sym])
                print('下午仓位',self.buy_qty[sym],self.sell_qty[sym])
#                   print('下午15点收盘时确定最高点最低点出现的时间',self.ticklastpriceTime[sym][self.ticklastprice[sym].index(max(self.ticklastprice[sym]))],self.ticklastpriceTime[sym][self.ticklastprice[sym].index(min(self.ticklastprice[sym]))])
                self.ticklastprice[sym] = [] 
                self.ticklastpriceTime[sym] = []

                self.firedFirst = True
                self.firedSecond = False
                self.firedNightOpen = True
                self.firedDayOpen = True
            # print('line28')   
#下午15点收盘判断高低点并且释放价格list end                  

#晚上收盘判断高低点并且释放价格list        
            if self.IfTwoHL[sym] and self.nightclosetime(sym,self.now) and self.firedSecond:
                self.HighPoint[sym] = max(self.ticklastprice[sym])
                self.LowPoint[sym] = min(self.ticklastprice[sym])
                self.YestodayHighPoint[sym] = self.HighPoint[sym]
                self.YestodayLowPoint[sym] = self.LowPoint[sym]
                print('晚上收盘时确定最高点最低点',self.HighPoint[sym],self.LowPoint[sym])
                print('晚上仓位',self.buy_qty[sym],self.sell_qty[sym])
#                   print('晚上收盘时确定最高点最低点出现的时间',self.ticklastpriceTime[sym][self.ticklastprice[sym].index(max(self.ticklastprice[sym]))],self.ticklastpriceTime[sym][self.ticklastprice[sym].index(min(self.ticklastprice[sym]))])
                self.ticklastprice[sym] = [] 
                self.ticklastpriceTime[sym] = []
                self.firedFirst = True
                self.firedSecond = False
                self.firedNightOpen = True
                self.firedDayOpen = True
#晚上收盘判断高低点并且释放价格list end
            # self.firedFirst = True
            self.firedSecond = False
            self.firedNightOpen = True
            self.firedDayOpen = True            
            
                
            # if self.fired[sym]:
            #     plot('short',self.MA_S[sym][-1])
            #     plot('Mean',self.MA_M[sym][-1])
            #     plot('long',self.MA_L[sym][-1])
#夜盘开盘            
            if self.nightopentime(sym,self.now) and self.firedFirst and self.firedNightOpen:            #夜盘开盘完成日线级别指标的赋值
#                 self.High[sym] = self.history_bars(sym,self.OBSERVATION,'1d','high')
#                 self.Low[sym] = self.history_bars(sym,self.OBSERVATION,'1d','low')
#                 self.Close[sym] = self.history_bars(sym,self.OBSERVATION,'1d','close')
                
# #                self.RealAdx[sym] = talib.ADX(self.High[sym], self.Low[sym], self.Close[sym], timeperiod = self.ADXTimePeriod)
# #                self.AdxCondition[sym] = self.RealAdx[sym][-1] > self.ADX       #RealAdxCondition 字典存储
            
#                 self.MA_S[sym] = talib.MA(self.Close[sym], self.SHORTPERIOD, matype=0)   #文丰注意可以改
#                 self.MA_M[sym] = talib.MA(self.Close[sym], self.MEANPERIOD, matype=0) 
#                 self.MA_L[sym] = talib.MA(self.Close[sym], self.LONGPERIOD, matype=0)
                
#                 if self.IfThreeMA[sym]:
#                     self.LongMeanCondition[sym] = self.MA_S[sym][-1] > self.MA_M[sym][-1] and self.MA_M[sym][-1] > self.MA_L[sym][-1] and self.MA_L[sym][-1] > self.MA_L[sym][-2]
#                     self.ShortMeanCondition[sym] = self.MA_S[sym][-1] < self.MA_M[sym][-1] and self.MA_M[sym][-1] < self.MA_L[sym][-1] and self.MA_L[sym][-1] < self.MA_L[sym][-2]
#                 elif self.IfTwoMA[sym]::
#                     self.LongMeanCondition[sym] = self.MA_S[sym][-1] > self.MA_M[sym][-1]
#                     self.ShortMeanCondition[sym] = self.MA_S[sym][-1] < self.MA_M[sym][-1]
                # else:
                #     self.LongMeanCondition[sym] = True
                #     self.ShortMeanCondition[sym] = True                
#                 self.LongCloseCondition[sym] = self.MA_S[sym][-1] < self.MA_M[sym][-1] and (self.buy_qty[sym] > 0 and self.orderfilled )
#                 self.ShortCloseCondition[sym] = self.MA_S[sym][-1] > self.MA_M[sym][-1] and (self.sell_qty[sym] > 0 and self.orderfilled)
                
#                 if self.LongCloseCondition[sym]:
#                     self.sell_close(sym, self.buy_qty[sym])
#                     self.orderfilled = False                     
#                     print('均线大赚止损++++++++++++++++++++++++')
#                 if self.ShortCloseCondition[sym]:
#                     self.buy_close(sym, self.buy_qty[sym])
#                     self.orderfilled = False
#                     print('均线大赚止损++++++++++++++++++++++++')
                    
#                 self.TendencyLong[sym] = self.LongMeanCondition[sym]            #多趋势条件
#                 self.TendencyShort[sym] = self.ShortMeanCondition[sym]          #空趋势条件     
                
                self.lastprice[sym] = tick.price
                
                print('晚上21点开盘时最高点最低点',self.HighPoint[sym],self.LowPoint[sym])
                self.fired[sym] = True
                self.firedSecond = True
                self.firedNightOpen = False     #夜盘开盘判断日线级别指标 只在开盘时打开一次
                pass      
            print('line 393')                                                                                                      #夜盘开盘内完成日线级别指标的赋值end
#夜盘开盘end
#日盘开盘
            if self.dayopentime(sym,self.now) and self.firedFirst and self.firedDayOpen:            #白天开盘完成日线级别指标的赋值
            
                # self.High[sym] = self.history_bars(sym,self.OBSERVATION,'1d','high')
                # self.Low[sym] = self.history_bars(sym,self.OBSERVATION,'1d','low')
                # self.Close[sym] = self.history_bars(sym,self.OBSERVATION,'1d','close')
            
                # self.MA_S[sym] = talib.MA(self.Close[sym], self.SHORTPERIOD, matype=0)   #文丰注意可以改
                # self.MA_M[sym] = talib.MA(self.Close[sym], self.MEANPERIOD, matype=0) 
                # self.MA_L[sym] = talib.MA(self.Close[sym], self.LONGPERIOD, matype=0)
                
                # if self.IfThreeMA[sym]:
                #     self.LongMeanCondition[sym] = self.MA_S[sym][-1] > self.MA_M[sym][-1] and self.MA_M[sym][-1] > self.MA_L[sym][-1] and self.MA_L[sym][-1] > self.MA_L[sym][-2]
                #     self.ShortMeanCondition[sym] = self.MA_S[sym][-1] < self.MA_M[sym][-1] and self.MA_M[sym][-1] < self.MA_L[sym][-1] and self.MA_L[sym][-1] < self.MA_L[sym][-2]
                # elif self.IfTwoMA[sym]::
                #     self.LongMeanCondition[sym] = self.MA_S[sym][-1] > self.MA_M[sym][-1]
                #     self.ShortMeanCondition[sym] = self.MA_S[sym][-1] < self.MA_M[sym][-1]
                # else:
                #     self.LongMeanCondition[sym] = True 
                #     self.ShortMeanCondition[sym] = True
                # self.LongCloseCondition[sym] = self.MA_S[sym][-1] < self.MA_M[sym][-1] and (self.buy_qty[sym] > 0 and self.orderfilled )
                # self.ShortCloseCondition[sym] = self.MA_S[sym][-1] > self.MA_M[sym][-1] and (self.sell_qty[sym] > 0 and self.orderfilled )
                
                # if self.LongCloseCondition[sym]:
                #     self.sell_close(sym, self.buy_qty[sym])
                #     self.orderfilled = False
                #     print('均线大赚止损++++++++++++++++++++++++')
                # if self.ShortCloseCondition[sym]:
                #     self.buy_close(sym, self.buy_qty[sym])
                #     self.orderfilled = False
                #     print('均线大赚止损++++++++++++++++++++++++')
                
                # self.TendencyLong[sym] = self.LongMeanCondition[sym]            #多趋势条件
                # self.TendencyShort[sym] = self.ShortMeanCondition[sym]          #空趋势条件     
                
                self.lastprice[sym] = tick.price
                print('白天9点开盘时最高点最低点',self.HighPoint[sym],self.LowPoint[sym])
                self.fired[sym] = True
                self.firedSecond = True
                self.firedDayOpen = False     #白天开盘判断日线级别指标 只在开盘时打开一次
                pass                                                                                                            #白天开盘内完成日线级别指标的赋值end
#日盘开盘结束
            self.buy_qty[sym] = self._portfolio_manager.positions[sym].buy_quantity
            self.sell_qty[sym] = self._portfolio_manager.positions[sym].sell_quantity
            self.buy_prices[sym] = self._portfolio_manager.positions[sym].avg_buy_price
            self.sell_prices[sym] = self._portfolio_manager.positions[sym].avg_sell_price      
            
            # self.lastprice[sym] = tick.price



#任意时刻刚入场时，此时没有前日收盘和当日开盘代码的相关赋值
#需要做的事情：
# 高低点记录
# 计算longmean/closecondition；
# 止损；
# firedfirst,second,nightopen等赋值
            if self.firststart:

                # self.High[sym] = self.history_bars(sym,self.OBSERVATION,'1d','high')
                # self.Low[sym] = self.history_bars(sym,self.OBSERVATION,'1d','low')
                # self.Close[sym] = self.history_bars(sym,self.OBSERVATION,'1d','close')
            
                # self.MA_S[sym] = talib.MA(self.Close[sym], self.SHORTPERIOD, matype=0)   #文丰注意可以改
                # self.MA_M[sym] = talib.MA(self.Close[sym], self.MEANPERIOD, matype=0) 
                # self.MA_L[sym] = talib.MA(self.Close[sym], self.LONGPERIOD, matype=0)
                
                # if self.IfThreeMA[sym]:
                #     self.LongMeanCondition[sym] = self.MA_S[sym][-1] > self.MA_M[sym][-1] and self.MA_M[sym][-1] > self.MA_L[sym][-1] and self.MA_L[sym][-1] > self.MA_L[sym][-2]
                #     self.ShortMeanCondition[sym] = self.MA_S[sym][-1] < self.MA_M[sym][-1] and self.MA_M[sym][-1] < self.MA_L[sym][-1] and self.MA_L[sym][-1] < self.MA_L[sym][-2]
                # elif self.IfTwoMA[sym]::
                #     self.LongMeanCondition[sym] = self.MA_S[sym][-1] > self.MA_M[sym][-1]
                #     self.ShortMeanCondition[sym] = self.MA_S[sym][-1] < self.MA_M[sym][-1]
                # else:
                #     self.LongMeanCondition[sym] = True 
                #     self.ShortMeanCondition[sym] = True
                # self.LongCloseCondition[sym] = self.MA_S[sym][-1] < self.MA_M[sym][-1] and (self.buy_qty[sym] > 0 and self.orderfilled )
                # self.ShortCloseCondition[sym] = self.MA_S[sym][-1] > self.MA_M[sym][-1] and (self.sell_qty[sym] > 0 and self.orderfilled )
                
                # if self.LongCloseCondition[sym]:
                #     self.sell_close(sym, self.buy_qty[sym])
                #     self.orderfilled = False
                #     print('均线大赚止损++++++++++++++++++++++++')
                # if self.ShortCloseCondition[sym]:
                #     self.buy_close(sym, self.buy_qty[sym])
                #     self.orderfilled = False
                #     print('均线大赚止损++++++++++++++++++++++++')
                
                # self.TendencyLong[sym] = self.LongMeanCondition[sym]            #多趋势条件
                # self.TendencyShort[sym] = self.ShortMeanCondition[sym]          #空趋势条件     









                self.lastprice[sym] = tick.price
                
                self.fired[sym] = True
                self.firedFirst = True
                self.firedSecond = True
                self.firststart = False

#给高低点迭代赋值
            if self.fired[sym] and self.firedFirst:
                print('445')
                self.HighPoint[sym] = max(self.HighPoint[sym],self.lastprice[sym])
                self.LowPoint[sym] = min(self.LowPoint[sym],self.lastprice[sym])
                self.lastprice[sym] = tick.price
                print('448')
                
#给高低点迭代赋值end
 
#开仓条件
            openCloseCondition = self.tradetime(sym,self.now) #交易时间条件
            self.TendencyLong[sym] = True
            self.TendencyShort[sym] = True
            self.fired[sym]=True            
            if self.fired[sym]:
                LongPriceCondition = tick.price > self.HighPoint[sym] and tick.price <= self.HighPoint[sym] + self.fudong[sym] and self.buy_qty[sym] == 0 and self.sell_qty[sym] == 0 and self.HighPoint[sym] - self.YestodayHighPoint[sym] < self.HighLowFactor[sym]*self.tick_size(sym)#开多的价仓条件
                ShortPriceCondition = tick.price < self.LowPoint[sym] and tick.price >= self.LowPoint[sym] - self.fudong[sym] and self.sell_qty[sym] == 0 and self.buy_qty[sym] == 0 and self.YestodayLowPoint[sym] - self.LowPoint[sym] < self.HighLowFactor[sym]*self.tick_size(sym)#开空的价仓条件
#开仓条件end
#开仓       #
            #openCloseCondition = True
            print('line 461')
            print('condition',tick.price,self.HighPoint[sym],self.LowPoint[sym],LongPriceCondition,ShortPriceCondition)
            if self.fired[sym] and LongPriceCondition and self.TendencyLong[sym] and self.firedOpenMovePositionCriteria[sym] and self.orderfilled: # and openCloseCondition: 
                if self.firedAutoObstructionResistance:
                    LocalHighlowA = history_bars(sym,self.AutoObstructionResistanceMinuteNumber,'3m','low')
                    LocalHighlowA1 = list(LocalHighlowA)
                    LocalHighlowB = LocalHighlowA1[1:]
                    LocalHighlowB.append(tick.price)
                    LocalHighlowC = (np.array(LocalHighlowB) - LocalHighlowA).tolist()
                    LocalHighlowD = LocalHighlowC[:]
                    LocalHighlowD.pop(0)
                    LocalHighlowD.append(LocalHighlowD[-1])
                    LocalHighlowE = (np.array(LocalHighlowD) * np.array(LocalHighlowC)).tolist()
                    LocalLowPointIndex = []
                    LocalHighPointIndex = []
                    LocalBalancePointIndex = []
                    LocalLowPointIndex1 = []
                    LocalHighPointIndex1 = []
                    LocalBalancePointIndex1 = []
                    for i in range(len(LocalHighlowE)-1, 0, -1) :
                        if (LocalHighlowE[i] < 0) and (LocalHighlowC[i + 1] >0) :
                            LocalLowPointIndex.append(i+1)
                            LocalBalancePointIndex.append(i+1)
                        elif (LocalHighlowE[i] == 0) and (i < len(LocalHighlowE)-1) & (i >= 0)  :
                            #j = i
                            #while LocalHighlowE[j] == 0 and (j > 0) :
                            #    j = j - 1
                            j = i
                            k = i
                            while LocalHighlowC[j] == 0 and (j > 0) :
                                j = j -1
                            while LocalHighlowC[k] == 0 and (k <= len(LocalHighlowE) - 2) :
                                k = k + 1
                            if (LocalHighlowC[j] * LocalHighlowC[k]) <0 :
                                if LocalHighlowC[k] > 0 :
                                    LocalLowPointIndex.append(k)
                                    LocalBalancePointIndex.append(k)
                                elif LocalHighlowC[k] <0  :
                                    LocalHighPointIndex.append(k)
                                    LocalBalancePointIndex.append(k)
                            del j 
                            del k
                        elif (LocalHighlowE[i] < 0) and (LocalHighlowC[i + 1] <0) :
                            LocalHighPointIndex.append(i+1)
                            LocalBalancePointIndex.append(i+1)
                    del i
                    
                    LocalLowPointIndex1 = list(set(LocalLowPointIndex))
                    LocalLowPointIndex1.sort(key = LocalLowPointIndex.index)
                    LocalLowPointIndex = LocalLowPointIndex1 
                    LocalHighPointIndex1 = list(set(LocalHighPointIndex))
                    LocalHighPointIndex1.sort(key = LocalHighPointIndex.index)
                    LocalHighPointIndex = LocalHighPointIndex1    
                    
                    LocalBalancePointIndex1 = list(set(LocalBalancePointIndex)) 
                    LocalBalancePointIndex1.sort(key = LocalBalancePointIndex.index)
                    LocalBalancePointIndex = LocalBalancePointIndex1
                    
                            
                    if len(LocalLowPointIndex) != 0 :
                        for i in range(0, len(LocalLowPointIndex)):
                            self.LocalLow[i] =[LocalLowPointIndex[i], LocalHighlowA[LocalLowPointIndex[i]]]
                        del i
                        self.IFLocalPointExist = True
                    else :
                        self.IFLocalPointExist = False
                        print('开多仓前没有坑')

                    self.IFAOR = True
                    
                    if self.IFLocalPointExist and self.IFAOR :
                        for i in range(0, len(self.LocalLow)):
                            print('多仓有坑，tick.price - self.LocalLow[i][1]',tick.price,self.LocalLow[i][1],tick.price - self.LocalLow[i][1])
#                            if (tick.price - self.LocalLow[i][1]) > self.FactorAOR * self.zhisundianwei[sym] * self.tick_size(sym) and (tick.price - self.LocalLow[i][1]) < self.zhisundianwei[sym] * self.tick_size(sym) and self.IFAOR:

                            if (tick.price - self.LocalLow[i][1]) > self.FactorAOR * self.zhisundianwei[sym] * self.tick_size(sym)  and self.IFAOR:
                                # 大于20个点立刻退出
                                if (tick.price - self.LocalLow[i][1]) > self.zhisundianwei[sym] * self.tick_size(sym):
                                    self.IFAOR = False
                                    break
                                    
                                
                                self.buyStopLossPoint[sym] = self.LocalLow[i][1]

                                print('多，前期支持位为止损点:',self.buyStopLossPoint[sym])

                                if self.sell_qty[sym] > 0:
                                    self.buy_close(sym, self.buy_qty[sym],type='lmt',price=tick.price)
                                    self.orderfilled = False
                                if self.ifcangwei :
                                    shoushu = int(self.cangwei[sym]*(allmoney/tick.price))
                                else :
                                    shoushu = 1

                                self.buy_open(symbol=sym,size=shoushu,type='lmt',price=tick.price)   #开仓
                                self.orderfilled = False
                                self.stoplosstimeFactor[sym] = 0
                                self.firedOpenRecoverCost[sym] = True
                                print('id',sym,'多开:',tick.price,tick.bid_price_L1,tick.ask_price_L1,',','大于高点：',self.HighPoint[sym],',','做多手数：',shoushu)
                                shoushu = 0 
                                self.IFLocalPointExist = False
                                self.IFAOR = False
                                
                                self.H1Pricetmp[sym] = tick.price 
                                self.H1Timetmp[sym] = self.now
                                self.BuyTime[sym] = self.now
                                self.H2Price[sym] = tick.price
                                self.MinAfterH2[sym] = tick.price
                # print('477')
                # if self.sell_qty[sym] > 0:
                #     self.buy_close(sym, self.buy_qty[sym])
                # print('480')
                # if self.ifcangwei :
                #     shoushu = int(self.cangwei[sym]*(allmoney/tick.price))
                #     print('483')
                # else :
                #     shoushu = 1
                # print('id',sym,'多开:',tick.price,tick.bid_price_L1,tick.ask_price_L1,',','大于高点：',self.HighPoint[sym],',','做多手数：',shoushu)
                # self.buy_open(symbol=sym,size=shoushu,type='lmt',price=tick.price)   #, price = tick.ask_price_L1
                # self.OpenPositionTime[sym] = self.now
                # self.stoplosstimeFactor[sym] = 0
                # self.firedOpenRecoverCost[sym] = True
                # self.pricesObstruction[sym] = self.HighPoint[sym]
                
                # print('做多瞬间的仓位',self.buy_qty[sym],self.sell_qty[sym])
                # shoushu = 0   #手数回归到0
        
            
            if self.fired[sym] and ShortPriceCondition and openCloseCondition and self.TendencyShort[sym] and self.firedOpenMovePositionCriteria[sym] and self.orderfilled:
                if self.firedAutoObstructionResistance:
#                        LocalHighlowA = np.array([1,2,3,4,9,8,7,4,5,6,6,6,6,7,8,5,5,5,5,9,10]);
                    LocalHighlowA = history_bars(sym,self.AutoObstructionResistanceMinuteNumber,'3m','high')
                    LocalHighlowA1 = list(LocalHighlowA)
                    LocalHighlowB = LocalHighlowA1[1:]
                    LocalHighlowB.append(tick.price)
                    LocalHighlowC = (np.array(LocalHighlowB) - LocalHighlowA).tolist()
                    LocalHighlowD = LocalHighlowC[:]
                    LocalHighlowD.pop(0)
                    LocalHighlowD.append(LocalHighlowD[-1])
                    LocalHighlowE = (np.array(LocalHighlowD) * np.array(LocalHighlowC)).tolist()
                    
                    LocalLowPointIndex = []
                    LocalHighPointIndex = []
                    LocalBalancePointIndex = []
                    LocalLowPointIndex1 = []
                    LocalHighPointIndex1 = []
                    LocalBalancePointIndex1 = []
                    for i in range(len(LocalHighlowE)-1, 0, -1) :
                        if (LocalHighlowE[i] < 0) and (LocalHighlowC[i + 1] >0) :
                            LocalLowPointIndex.append(i+1)
                            LocalBalancePointIndex.append(i+1)
                        elif (LocalHighlowE[i] == 0) and (i < len(LocalHighlowE)-1) & (i >= 0)  :
                            #j = i
                            #while LocalHighlowE[j] == 0 and (j > 0) :
                            #    j = j - 1
                            j = i
                            k = i
                            while LocalHighlowC[j] == 0 and (j > 0) :
                                j = j -1
                            while LocalHighlowC[k] == 0 and (k <= len(LocalHighlowE) - 2) :
                                k = k + 1
                            
                            if (LocalHighlowC[j] * LocalHighlowC[k]) <0 :
                                if LocalHighlowC[k] > 0 :
                                    LocalLowPointIndex.append(k)
                                    LocalBalancePointIndex.append(k)
                                elif LocalHighlowC[k] <0  :
                                    LocalHighPointIndex.append(k)
                                    LocalBalancePointIndex.append(k)
                            del j
                            del k
                        elif (LocalHighlowE[i] < 0) and (LocalHighlowC[i + 1] <0) :
                            LocalHighPointIndex.append(i+1)
                            LocalBalancePointIndex.append(i+1)
                    del i
                    
                    LocalLowPointIndex1 = list(set(LocalLowPointIndex))
                    LocalLowPointIndex1.sort(key = LocalLowPointIndex.index)
                    LocalLowPointIndex = LocalLowPointIndex1 
                    LocalHighPointIndex1 = list(set(LocalHighPointIndex))
                    LocalHighPointIndex1.sort(key = LocalHighPointIndex.index)
                    LocalHighPointIndex = LocalHighPointIndex1                     
                    LocalBalancePointIndex1 = list(set(LocalBalancePointIndex)) 
                    LocalBalancePointIndex1.sort(key = LocalBalancePointIndex.index)
                    LocalBalancePointIndex = LocalBalancePointIndex1                                   
                    
                    if len(LocalHighPointIndex) != 0 :
                        for i in range(0, len(LocalHighPointIndex)):
                            self.LocalHigh[i] =[LocalHighPointIndex[i], LocalHighlowA[LocalHighPointIndex[i]]]
                        del i             
                        self.IFLocalPointExist = True
                    else :
                        self.IFLocalPointExist = False 
                        print('开空仓前没有包')
                    self.IFAOR = True
                    if self.IFLocalPointExist and self.IFAOR:
                        for i in range(0, len(self.LocalHigh)):
                            print('空仓有包，context.LocalHigh[i][1] - tick.price',self.LocalHigh[i][1] , tick.price,self.LocalHigh[i][1] - tick.price)
#                            if (self.LocalHigh[i][1] - tick.price) > self.FactorShort_Long * self.FactorAOR * self.zhisundianwei[sym] * self.tick_size(sym) and (self.LocalHigh[i][1] - tick.price) < self.FactorShort_Long * self.zhisundianwei[sym] * self.tick_size(sym) and self.IFAOR:

                            if (self.LocalHigh[i][1] - tick.price) > self.FactorAOR * self.zhisundianwei[sym] * self.tick_size(sym)  and self.IFAOR:
                                
                                if (self.LocalHigh[i][1] - tick.price) > self.zhisundianwei[sym] * self.tick_size(sym):
                                    self.IFAOR = False
                                    break

                                self.sellStopLossPoint[sym] = self.LocalHigh[i][1]

                                if self.buy_qty[sym] > 0:
                                    self.sell_close(sym, self.buy_qty[sym],type='lmt',price = tick.price)
                                    self.orderfilled = False
                                if self.ifcangwei :
                                    shoushu = int(self.cangwei[sym]*(allmoney/tick.price))
                                    pass
                                else :
                                    shoushu = 1
                                
                                self.sell_open(sym,shoushu,type='lmt',price=tick.price)   
                                self.orderfilled = False                              
                                print('空，前期阻力位为止损点',self.sellStopLossPoint[sym])
                                
                                self.stoplosstimeFactor[sym] = 0
                                self.firedOpenRecoverCost[sym] = True
                                print('id',sym,'空开:',tick.price,tick.bid_price_L1,tick.ask_price_L1,',','小于低点：',self.LowPoint[sym],',','做空手数：',shoushu)
                                shoushu = 0                                 

                                self.IFLocalPointExist = False
                                self.IFAOR = False
                                
                                self.L1Pricetmp[sym] = tick.price 
                                self.L1Timetmp[sym] = self.now
                                self.SellTime[sym] = self.now
                                self.L2Price[sym] = tick.price
                                self.MaxAfterL2[sym] = tick.price
                # if self.buy_qty[sym] > 0:
                #     self.sell_close(sym, self.buy_qty[sym],type='lmt',price = tick.price)
                # if self.ifcangwei :
                #     shoushu = int(self.cangwei[sym]*(allmoney/tick.price))
                #     pass
                # else :
                #     shoushu = 1
                # print('id',sym,'空开:',tick.price,tick.bid_price_L1,tick.ask_price_L1,',','小于低点：',self.LowPoint[sym],',','做空手数：',shoushu)
                # self.sell_open(sym,shoushu,type='lmt',price=tick.price) 
                # self.OpenPositionTime[sym] = self.now
                # self.stoplosstimeFactor[sym] = 0
                # self.firedOpenRecoverCost[sym] = True
                # self.pricesResistance[sym] = self.LowPoint[sym] 
                
                # print('做空瞬间的仓位',self.buy_qty[sym],self.sell_qty[sym])
                # shoushu = 0   
#开仓end    
            self.buy_qty[sym] = self._portfolio_manager.positions[sym].buy_quantity
            self.sell_qty[sym] = self._portfolio_manager.positions[sym].sell_quantity
            self.buy_prices[sym] = self._portfolio_manager.positions[sym].avg_buy_price
            self.sell_prices[sym] = self._portfolio_manager.positions[sym].avg_sell_price   
            
#智能止损
            if self.fireRecover_and_Move:
                if self.buy_qty[sym] > 0:
                    # 双高点
                    if tick.price <= self.H1Pricetmp[sym] :
                        self.list_betweenH1_High[sym].append(tick.price)
                    elif tick.price > self.H1Pricetmp[sym] :
#                        if self.now - self.H1Timetmp[sym] < datetime.timedelta(minutes = self.TillLastHighLimit[sym]) :
                        if len(self.list_betweenH1_High[sym]) < self.Len_list_betweenH1_High_Limit[sym] :
                            self.list_betweenH1_High[sym] = []
                            self.H1Pricetmp[sym] = tick.price
                        elif len(self.list_betweenH1_High[sym]) > self.Len_list_betweenH1_High_Limit2[sym] :
                            
                            if len(self.list_betweenH1_High[sym]) != 0  :
                                    
                                if self.buyStopLossPoint_old[sym] != min(self.list_betweenH1_High[sym]) :
                                    self.counter_buyStopLossPoint[sym] =  self.counter_buyStopLossPoint[sym] + 1 
                                    
                                    if self.counter_buyStopLossPoint[sym] > 1:
                                        self.buyStopLossPoint[sym] = self.buyStopLossPoint_old[sym]
                                        self.buyStopLossPoint_old[sym]= min(self.list_betweenH1_High[sym])
                                        #print('恢复成本价到坑1',self.buyStopLossPoint[sym])
                                    elif self.counter_buyStopLossPoint[sym] == 1:
                                        self.buyStopLossPoint_old[sym]= min(self.list_betweenH1_High[sym])
                                    
                                self.H1Pricetmp[sym] = tick.price
                                self.list_betweenH1_High[sym] = []
                                
                                    
                    # 1/2离场
                    if tick.price >= self.H2Price[sym] :
                        #self.list_AfterBuy[sym] = []
                        self.H2Price[sym] = tick.price
                        self.MinAfterH2[sym] = self.H2Price[sym]
                    else : 
                        if self.MinAfterH2[sym] > tick.price:
                            self.MinAfterH2[sym] = tick.price
                        
                        #self.list_AfterBuy[sym].append(tick.price)          
                        if  self.H2Price[sym] - self.MinAfterH2[sym] > self.BuyRecoverPointLimit[sym]*self.tick_size(sym) :
                            if tick.price - self.MinAfterH2[sym] > self.BuyRecoverFactor[sym] * (self.H2Price[sym] - self.MinAfterH2[sym]) :
                                if self.buyStopLossPoint_old[sym] != self.MinAfterH2[sym] :
                                    self.counter_buyStopLossPoint[sym] =  self.counter_buyStopLossPoint[sym] + 1
                                    
                                    if self.counter_buyStopLossPoint[sym] > 1:
                                        self.buyStopLossPoint[sym] = self.buyStopLossPoint_old[sym]
                                        self.buyStopLossPoint_old[sym] = self.MinAfterH2[sym]
                                        #print('恢复成本价到坑2',self.buyStopLossPoint[sym])
                                    elif self.counter_buyStopLossPoint[sym] == 1:
                                        self.buyStopLossPoint_old[sym] = self.MinAfterH2[sym]
                                    
                                
                                
                                
                if self.sell_qty[sym] > 0:
                    # 双低点
                    if tick.price >= self.L1Pricetmp[sym] :
                            self.list_betweenL1_Low[sym].append(tick.price)
                    elif tick.price < self.L1Pricetmp[sym] :
#                        if self.now - self.L1Timetmp[sym] <  datetime.timedelta(minutes = self.TillLastLowLimit[sym]):
                        if len(self.list_betweenL1_Low[sym]) < self.Len_list_betweenL1_Low_Limit[sym] :
                            self.list_betweenL1_Low[sym] = []
                            self.L1Pricetmp[sym] = tick.price
                        elif len(self.list_betweenL1_Low[sym]) > self.Len_list_betweenL1_Low_Limit2[sym] :
                            if len(self.list_betweenL1_Low[sym]) != 0 :
                                
                                if self.sellStopLossPoint_old[sym] != max(self.list_betweenL1_Low[sym]) :
                                    self.counter_sellStopLossPoint[sym] =  self.counter_sellStopLossPoint[sym] + 1 
                                    
                                    if self.counter_sellStopLossPoint[sym] > 1:
                                        self.sellStopLossPoint[sym] = self.sellStopLossPoint_old[sym]
                                        self.sellStopLossPoint_old[sym] = max(self.list_betweenL1_Low[sym])
                                        #print('恢复成本价到包1',self.sellStopLossPoint[sym])
                                    elif self.counter_sellStopLossPoint[sym] == 1:
                                        self.sellStopLossPoint_old[sym] = max(self.list_betweenL1_Low[sym])
                                    
                                self.L1Pricetmp[sym] = tick.price
                                self.list_betweenL1_Low[sym] = []
                                
                    # 1/2离场         
                    if tick.price <= self.L2Price[sym] :
                        #self.list_AfterSell[sym] = []
                        self.L2Price[sym] = tick.price
                        self.MaxAfterL2[sym] = self.L2Price[sym]
                    else : 
                        if self.MaxAfterL2[sym] < tick.price :
                            self.MaxAfterL2[sym] = tick.price
                        #self.list_AfterSell[sym].append(tick.price)          
                        if  self.MaxAfterL2[sym] - self.L2Price[sym] > self.SellRecoverPointLimit[sym]*self.tick_size(sym) :
                            if self.MaxAfterL2[sym] - tick.price  > self.SellRecoverFactor[sym] * (self.MaxAfterL2[sym] - self.L2Price[sym]) :
                                if self.sellStopLossPoint_old[sym] != self.MaxAfterL2[sym] :
                                    self.counter_sellStopLossPoint[sym] =  self.counter_sellStopLossPoint[sym] + 1 
                                    
                                    if self.counter_sellStopLossPoint[sym] > 1:
                                        self.sellStopLossPoint[sym] = self.sellStopLossPoint_old[sym]
                                        self.sellStopLossPoint_old[sym] = self.MaxAfterL2[sym]
                                        #print('恢复成本价到包2',self.sellStopLossPoint[sym])    
                                    elif self.counter_sellStopLossPoint[sym] == 1:
                                        self.sellStopLossPoint_old[sym] = self.MaxAfterL2[sym]
            
            
                                
#智能止损end




# 仓位移动平均线
            if self.now.second == 2 :
                self.firedPositionMA = True
                
            if self.now.second == 1 and self.firedPositionMA :
                self.PositionList[sym] = np.delete(self.PositionList[sym],0)
                self.PositionList[sym] = self.PositionList[sym].tolist()
                self.PositionList[sym].append(tick.open_interest)
                self.PositionList[sym] = np.array(self.PositionList[sym])
                self.firedPositionMA = False
                
                self.PositionMA_S[sym] = talib.MA(self.PositionList[sym], self.PositionMove_SHORTPERIOD, matype=0)   
                self.PositionMA_M[sym] = talib.MA(self.PositionList[sym], self.PositionMove_MEANPERIOD, matype=0) 
                self.PositionMA_L[sym] = talib.MA(self.PositionList[sym], self.PositionMove_LONGPERIOD, matype=0)
            
                self.Position_MACondition_Tripe[sym] =  (self.PositionMA_S[sym][-1] - self.PositionMA_M[sym][-1] > 0) and (self.PositionMA_M[sym][-1] - self.PositionMA_L[sym][-1] > 0) 
                
                self.Position_MACondition_Double[sym] =  (self.PositionMA_S[sym][-1] - self.PositionMA_M[sym][-1] > 0) 
                    
                    
                if self.IfPositionMA_Double[sym] :
                    self.firedOpenMovePositionCriteria[sym] = self.Position_MACondition_Double[sym]
                if self.IfPositionMA_Tripe[sym] :
                    self.firedOpenMovePositionCriteria[sym] = self.Position_MACondition_Tripe[sym]
# 仓位移动平均线end                         
                

                              


#止损出场
            if self.orderfilled  and self.buy_qty[sym] > 0 and tick.price <= self.buyStopLossPoint[sym]:
                self.sell_close(sym, self.buy_qty[sym],type='lmt',price=tick.price)
                self.orderfilled = False
                print('卖平止损：',tick.price-self.buy_prices[sym])
                self.list_AfterBuy[sym] = []
                self.list_betweenH1_High[sym] = []
                self.counter_buyStopLossPoint[sym] = 0
                self.buyStopLossPoint_old[sym] = 0
                
                

            
            if self.orderfilled and self.sell_qty[sym] > 0 and tick.price >= self.sellStopLossPoint[sym]:
                self.buy_close(sym, self.sell_qty[sym],type='lmt',price=tick.price)
                self.orderfilled = False
                print('买平止损：',self.sell_prices[sym]-tick.price)
                self.list_AfterSell[sym] = []
                self.list_betweenL1_Low[sym] = []
                self.counter_sellStopLossPoint[sym] = 0
                self.sellStopLossPoint_old[sym] = 0
#止损出场end

# #时间止损出场
#             if self.buy_qty[sym] > 0 and self.firedOpenTimeStopLoss[sym] :
# #                print('timedelta',(self.now - self.OpenPositionTime[sym]))
#                 if (self.now - self.OpenPositionTime[sym]) > datetime.timedelta(minutes = self.stoplosstimeminute[sym]):
#                     if tick.price - self.buy_prices[sym] < self.stoplosstimePoint[sym] * 0.5 :
#                         self.sell_close(sym, self.buy_qty[sym],type='lmt',price=tick.price)
#                         print('时间卖平止损：',tick.price-self.buy_prices[sym])
            
            
#             if self.sell_qty[sym] > 0 and self.firedOpenTimeStopLoss[sym] :
# #                print('timedelta',(self.now - self.OpenPositionTime[sym]))
#                 if (self.now - self.OpenPositionTime[sym]) > datetime.timedelta(minutes = self.stoplosstimeminute[sym]):
#                     if  self.sell_prices[sym] - tick.price < self.stoplosstimePoint[sym] * 0.5 :
#                         self.buy_close(sym, self.sell_qty[sym],type='lmt',price=tick.price)
#                         print('时间卖平止损：',self.sell_prices[sym] - tick.price)
        
# #时间止损出场end
# #恢复成本价
#             if self.firedOpenRecoverCost[sym] :
                
#                 if self.buy_qty[sym] > 0 :
#                     self.buyStopLossPoint[sym] = self.buy_prices[sym] - self.zhisundianwei[sym] * self.tick_size(sym)
                    
#                     if (tick.price - self.buy_prices[sym]) > self.stoplosstimePoint[sym]* self.tick_size(sym):
#                         self.buyStopLossPoint[sym] = self.buy_prices[sym] 
#                         print('恢复成本价到买价',self.buyStopLossPoint[sym])
#                         self.firedOpenRecoverCost[sym] = False
#                 if self.sell_qty[sym] > 0 :
#                     self.sellStopLossPoint[sym] = self.sell_prices[sym] + self.zhisundianwei[sym] * self.tick_size(sym)
                    
#                     if (self.sell_prices[sym] - tick.price) > self.stoplosstimePoint[sym] * self.tick_size(sym)  :
#                         self.sellStopLossPoint[sym] = self.sell_prices[sym]
#                         print('恢复成本价到卖价',self.sellStopLossPoint[sym])
#                         self.firedOpenRecoverCost[sym] = False
# #恢复成本价end
# #止损出场
#             if self.buy_qty[sym] > 0 and tick.price <= self.buyStopLossPoint[sym]:
#                 self.sell_close(sym, self.buy_qty[sym],type='lmt',price=tick.price)
#                 print('卖平止损：',tick.price-self.buy_prices[sym])
            
#             if self.sell_qty[sym] > 0 and tick.price >= self.sellStopLossPoint[sym]:
#                 self.buy_close(sym, self.sell_qty[sym],type='lmt',price = tick.price)
#                 print('买平止损：',self.sell_prices[sym]-tick.price)
# #止损出场end
#移动止损
            if self.firedOpenMoveStopLoss[sym]:
                if self.buy_qty[sym] > 0 and int((tick.price - self.buy_prices[sym]) / (self.stoplossMovePoint[sym] * self.tick_size(sym))) > self.stoplosstimeFactor[sym]:
                    self.stoplosstimeFactor[sym] = int((tick.price - self.buy_prices[sym]) / (self.stoplossMovePoint[sym] * self.tick_size(sym)))
                    
                    if (1.0 - self.MoveFactor) * (tick.price - self.buy_prices[sym]) > self.MoveFactorForPrice * tick.price :
                        self.buyStopLossPointTmp[sym] = (1 - self.MoveFactorForPrice) * tick.price
                        
                        if self.buyStopLossPointTmp[sym] >= self.buyStopLossPoint[sym] :
                            self.buyStopLossPoint[sym] = self.buyStopLossPointTmp[sym]
                    else :
                        self.buyStopLossPoint[sym] = self.buy_prices[sym] + (self.MoveFactor*self.stoplosstimeFactor[sym]*self.stoplossMovePoint[sym] * self.tick_size(sym))
                        
                    self.firedOpenRecoverCost[sym] = False
                if self.sell_qty[sym] > 0 and int((self.sell_prices[sym] - tick.price) / (self.stoplossMovePoint[sym] * self.tick_size(sym))) > self.stoplosstimeFactor[sym]:
                    self.stoplosstimeFactor[sym] = int((self.sell_prices[sym] - tick.price) / (self.stoplossMovePoint[sym] * self.tick_size(sym)))
                    
                    if (1.0 - self.MoveFactor) * (self.sell_prices[sym] - tick.price) > self.MoveFactorForPrice * tick.price :
                        self.sellStopLossPointTmp[sym] = (1 + self.MoveFactorForPrice) * tick.price
                        
                        if self.sellStopLossPointTmp[sym] <= self.sellStopLossPoint[sym] :
                            self.sellStopLossPoint[sym] = self.sellStopLossPointTmp[sym]
                    else :
                        self.sellStopLossPoint[sym] = self.sell_prices[sym] - (self.MoveFactor*self.stoplosstimeFactor[sym]*self.stoplossMovePoint[sym] * self.tick_size(sym))
                        
#                    print('移动卖止损到',self.sellStopLossPoint[sym])
                    self.firedOpenRecoverCost[sym] = False
#移动止损end
#移动平均线止损
            if self.now.second == 2 :
                self.firedMA = True
                
            if self.now.second == 1 and self.firedMA :
                self.minlastprice[sym] = np.delete(self.minlastprice[sym],0)
                self.minlastprice[sym] = self.minlastprice[sym].tolist()
                self.minlastprice[sym].append(tick.price)
                self.minlastprice[sym] = np.array(self.minlastprice[sym])
                self.firedMA = False
                
                if (self.buy_qty[sym] > 0 or self.sell_qty[sym] > 0) and self.firedOpenMoveAverageStopLoss[sym] and self.firedFirst :
                    pass
                    
                    # self.MA_S2[sym] = talib.MA(self.minlastprice[sym], self.SHORTPERIOD2, matype=0)   
                    # self.MA_M2[sym] = talib.MA(self.minlastprice[sym], self.MEANPERIOD2, matype=0) 
                    # self.MA_L2[sym] = talib.MA(self.minlastprice[sym], self.LONGPERIOD2, matype=0)
                    
                    # if self.MA_S2[sym][-1] - self.MA_M2[sym][-1] > 0:
                    #     if self.MA_S2[sym][-2] - self.MA_M2[sym][-2] < 0:
                    #         self.Goldcross[sym] = True
                    #     elif self.MA_S2[sym][-2] == self.MA_M2[sym][-2]:
                    #         i = -2
                    #         while self.MA_S2[sym][i] == self.MA_M2[sym][i]:
                    #             i = i - 1
                    #         if self.MA_S2[sym][i] - self.MA_M2[sym][i] < 0:
                    #             self.Goldcross[sym] = True
                    #         else :
                    #             self.Goldcross[sym] = False
                    #     else :
                    #         self.Goldcross[sym] = False                        
                    
                    # if self.MA_S2[sym][-1] - self.MA_M2[sym][-1] < 0:
                    #     if self.MA_S2[sym][-2] - self.MA_M2[sym][-2] > 0:
                    #         self.Deadcross[sym] = True
                    #     elif self.MA_S2[sym][-2] == self.MA_M2[sym][-2]:
                    #         i = -2
                    #         while self.MA_S2[sym][i] == self.MA_M2[sym][i]:
                    #             i = i - 1
                    #         if self.MA_S2[sym][i] - self.MA_M2[sym][i] > 0:
                    #             self.Deadcross[sym] = True
                    #         else :
                    #             self.Deadcross[sym] = False
                    #     else :
                    #         self.Deadcross[sym] = False   
                            
                    # if self.orderfilled and self.buy_qty[sym] > 0 and self.Deadcross[sym] :
                    #     self.sell_close(sym, self.buy_qty[sym])
                    #     self.orderfilled = False
                    #     self.Deadcross[sym] = False
                    #     print('买开通过均线卖平',self.MA_S2[sym][-1],self.MA_M2[sym][-1],self.MA_L2[sym][-1])          
                    # if self.orderfilled and self.sell_qty[sym] > 0 and self.Goldcross[sym] :
                    #     self.buy_close(sym, self.buy_qty[sym])
                    #     self.orderfilled = False
                    #     print('卖开通过均线买平',self.MA_S2[sym][-1],self.MA_M2[sym][-1],self.MA_L2[sym][-1])  
                    #     self.Goldcross[sym] = False
#移动平均线止损end
#下午或者晚上收盘，平仓出场
            if self.CloseClose[sym]:
                if self.now.hour == 14 and self.now.minute == 60 - 1:
                    if self.buy_qty[sym] > 0 and tick.price - self.buy_prices[sym] < self.BenifitBeforeClose[sym] * self.tick_size(sym):
                        self.sell_close(sym, self.buy_qty[sym],type='lmt',price=tick.price)
                        print('日内下午三点之前卖平',sym)
                    if self.sell_qty[sym] > 0 and self.buy_prices[sym] - tick.price  < self.BenifitBeforeClose[sym] * self.tick_size(sym):
                        self.buy_close(sym, self.sell_qty[sym],type='lmt',price=tick.price)
                        print('日内下午三点之前买平',sym)
                if self.now.hour == self.CloseHour[sym] and self.now.minute == self.CloseMinute[sym] - 1:
                    if self.buy_qty[sym] > 0 and tick.price - self.buy_prices[sym] < self.BenifitBeforeClose[sym] * self.tick_size(sym):
                        self.sell_close(sym, self.buy_qty[sym],type='lmt',price=tick.price)
                        print('日内晚收盘前卖平',sym)
                    if self.sell_qty[sym] > 0 and self.buy_prices[sym] - tick.price  < self.BenifitBeforeClose[sym] * self.tick_size(sym):
                        self.buy_close(sym, self.sell_qty[sym],type='lmt',price=tick.price)
                        print('日内晚收盘前买平',sym)
    def after_trading(self):

        pass
    def history_bars(self,sym,numbers,freq,colname):
        ktime = self.now
        if (freq =='1d'):
            indexendday = datetime.datetime(ktime.year,ktime.month,ktime.day)
            indexend = self._histbar_day.index.get_loc(indexendday)
            indexbegin = indexend - numbers
            if indexbegin < 0:
                indexbegin = 0
            # indexbeginday = self._histbar_day.index[indexbegin]
            # df = self._histbar_day[ (self._histbar_day.index< indexendday) & (self._histbar_day.index >= indexbeginday)]
            df = self._histbar_day.ix[indexbegin:indexend]
            return df[colname]

            
    def tick_size(self,sym):
        return 10
        #RB = 2
        #NI = 10





    def dayclosetime(self,sym,time):
        if time.hour == 14 and time.minute == 59 and time.second == 59:
            return True
        return False


    def dayopentime(self,sym,time):
        if time.hour == 9 and time.minute == 0 and time.second == 0:
            return True
        return False
        
    
    def nightclosetime(self,sym,time):
        closehour = 23
        closemin = 29
        if sym == 'NI':
            closehour = 0
            closemin = 59
        if time.hour == closehour and time.minute == closemin  and time.second == 59
            return True
        return False

    def nightopentime(self,sym,time):
        if time.hour == 9 and time.minute == 0 and time.second == 0:
            return True
        return False



    def tradetime(self,sym,time):
        dayopenCondition = (time.hour >= 9) 
        daycloseCondition = (time.hour < 14) or (time.hour == 14 and time.minute < 60 - self.opencloseminute[sym])
        nightopenCondition = (time.hour >= self.OpenHour[sym]) 
        nightcloseCondition = (time.hour < self.CloseHour[sym] ) or ( time.hour == self.CloseHour[sym] and time.minute < self.CloseMinute[sym] - self.opencloseminute[sym])
        trade = (dayopenCondition and daycloseCondition) or (nightopenCondition and nightcloseCondition) 

        return trade





