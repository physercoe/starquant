import time
import talib
import numpy as np
import datetime


##############################  日志   ##########################
#前一版本名字：

#本版本模块
#1.开仓前向前30分钟寻找止损点位，找到后才开仓
#2.开仓后止损：两个高点中最低点作为止损点；没到最高点，但经过了高点和最低点1/2高度后设置最低点为止损点
#3.增加持仓量信息(增仓才入场)
#新增模块
#1.止损点相位延后一位（即出现第二个止损点把止损点位放到第一个止损点）
#删除模块

##############################  日志end   ##########################

def init(context):
    
    context.s1 = "RB1710"
    context.s2 = "M888"
    context.s3 = "M1609"
    
    subscribe([context.s1])
    context.ifcangwei = False       #是否复利加仓
#    print('保证金比率',instruments(context.s1).margin_rate)
    context.cangwei = {}
    context.cangwei[context.s1] = 0.7
    context.cangwei[context.s2] = 0.7    
    context.cangwei[context.s3] = 0.7    
    
    context.firedFirst = False
    context.firedSecond = True
    context.firedNightOpen = False
    context.firedDayOpen = False
    context.firedMA = True
    context.fireRecover_and_Move = True

    context.firedAutoObstructionResistance = True  #是否用自动支撑阻力
    context.AutoObstructionResistanceMinuteNumber = 12
    context.IFAOR = False
    context.FactorAOR = 0.25
    context.FactorShort_Long = 1
    context.IFLocalPointExist = False
    context.LocalLow = {}
    context.LocalHigh = {}

    context.fired = {}
    
    context.fired[context.s1] = False
    context.fired[context.s2] = False
    context.fired[context.s3] = False

#是否二重日均线
    context.IfTwoMA = {}
    context.IfTwoMA[context.s1] = False
    context.IfTwoMA[context.s2] = False
    context.IfTwoMA[context.s3] = False   
#是否二重日均线end

#是否三重日均线
    context.IfThreeMA = {}
    context.IfThreeMA[context.s1] = True
    context.IfThreeMA[context.s2] = False
    context.IfThreeMA[context.s3] = False   
#是否三重日均线end

#是否两段高低点
    context.IfTwoHL = {}
    context.IfTwoHL[context.s1] = False
    context.IfTwoHL[context.s2] = False
    context.IfTwoHL[context.s3] = False   
#是否两段高低点end
    
#是否移动止损    
    context.firedOpenMoveStopLoss = {}     #移动止损
    
    context.firedOpenMoveStopLoss[context.s1] = False
    context.firedOpenMoveStopLoss[context.s2] = False
    context.firedOpenMoveStopLoss[context.s3] = False
    context.MoveFactor = 0.65            #移动止损因子（在0.5左右）
    context.MoveFactorForPrice = 0.01    #单笔浮盈损失最大因子（在0.01左右）
#是否移动止损end

#是否恢复成本价
    context.firedOpenRecoverCost = {}      #恢复成本价
    
    context.firedOpenRecoverCost[context.s1] = False
    context.firedOpenRecoverCost[context.s2] = False
    context.firedOpenRecoverCost[context.s3] = False
#是否恢复成本价end

#是否移动平均线止损
    context.firedOpenMoveAverageStopLoss = {}     #移动平均线止损
    
    context.firedOpenMoveAverageStopLoss[context.s1] = False
    context.firedOpenMoveAverageStopLoss[context.s2] = False
    context.firedOpenMoveAverageStopLoss[context.s3] = False
#是否移动平均线止损end

#是否持仓过夜
    context.CloseClose = {}
    
    context.CloseClose[context.s1] = True      #False持仓过夜，True日内平仓
    context.CloseClose[context.s2] = False
    context.CloseClose[context.s3] = False
#是否持仓过夜end

#定义金叉死叉
    context.Goldcross = {}
    context.Goldcross[context.s1] = False
    context.Goldcross[context.s2] = False
    context.Goldcross[context.s3] = False    

    context.Deadcross = {}
    context.Deadcross[context.s1] = False
    context.Deadcross[context.s2] = False
    context.Deadcross[context.s3] = False       
#定义金叉死叉end

    context.Contexts = [context.s1]
    
#定义开收盘时间
    context.OpenHour = {}
    context.CloseHour = {}
    context.CloseMinute = {}
    
    context.OpenHour[context.s1] = 21
    context.OpenHour[context.s2] = 21
    context.OpenHour[context.s3] = 21
    
    context.CloseHour[context.s1] = 22
    context.CloseHour[context.s2] = 23
    context.CloseHour[context.s3] = 23

    context.CloseMinute[context.s1] = 60
    context.CloseMinute[context.s2] = 30
    context.CloseMinute[context.s3] = 30
#定义开收盘时间end

#定义收盘不交易分钟数
    context.opencloseminute = {}
    context.opencloseminute[context.s1] = 2
    context.opencloseminute[context.s2] = 5
    context.opencloseminute[context.s3] = 5
#定义开收盘不交易分钟数end

#定义append数组
    context.ticklastprice = {}
    context.ticklastprice[context.s1] = []
    context.ticklastprice[context.s2] = []
    context.ticklastprice[context.s2] = []
    
    
    context.ticklastpriceTime = {}
    context.ticklastpriceTime[context.s1] = []
    context.ticklastpriceTime[context.s2] = []
    context.ticklastpriceTime[context.s2] = []
    
#定义append数组end

#定义止损点位
    context.zhisundianwei = {}
    context.zhisundianwei[context.s1] = 20
    context.zhisundianwei[context.s2] = 3
    context.zhisundianwei[context.s3] = 3
#定义止损点位end

#时间止损止盈点位
    context.stoplosstimePoint = {}
    context.stoplosstimePoint[context.s1] = 15
    context.stoplosstimePoint[context.s2] = 3
    context.stoplosstimePoint[context.s3] = 3   
#时间止损止盈点位end

#移动止损止盈点位
    context.stoplossMovePoint = {}
    context.stoplossMovePoint[context.s1] = 40
    context.stoplossMovePoint[context.s2] = 3
    context.stoplossMovePoint[context.s3] = 3   
#移动止损止盈点位end





#移动止损因子
    context.stoplosstimeFactor = {}
#移动止损因子end

#允许入场滑点
    context.fudong = {}
    context.fudong[context.s1] = 5
    context.fudong[context.s2] = 3
    context.fudong[context.s3] = 3   
#允许入场滑点end    

#时间止损分钟数
    context.stoplosstimeminute = {}
    context.stoplosstimeminute[context.s1] = 3
    context.stoplosstimeminute[context.s2] = 3
    context.stoplosstimeminute[context.s3] = 3    
#时间止损分钟数end    

#日均线周期设置
    context.SHORTPERIOD = 5
    context.MEANPERIOD = 10
    context.LONGPERIOD = 20
    context.OBSERVATION = 50
#日均线周期设置end    

#分钟均线周期设置
    context.SHORTPERIOD2 = 5
    context.MEANPERIOD2 = 10
    context.LONGPERIOD2 = 20
    context.OBSERVATION2 = 100
#分钟均线周期设置end  

    context.minlastprice = {}
    context.minlastprice[context.s1] = np.full([1,context.OBSERVATION2],np.nan)[0]
#    context.minlastprice[context.s1] = []
    context.minlastprice[context.s2] = []
    context.minlastprice[context.s3] = []

#A.D.X指标设置
    context.ADX = 40                          #ADX指标
    context.ADXTimePeriod = 4                 #ADX周期
#A.D.X指标设置end   

#变量设置
    context.HighPoint = {}
    context.LowPoint = {}
    context.YestodayHighPoint = {}
    context.YestodayLowPoint = {}
    context.HighLowFactor = {}         #文丰注意，如果超过这个值，认为是震荡上行，不交易
    context.HighLowFactor[context.s1] = 200000          
    context.HighLowFactor[context.s2] = 10
    context.HighLowFactor[context.s3] = 10
    
    context.High = {}
    context.Low = {}
    context.Close = {}
    context.HighMin = {}
    context.LowMin = {}
    context.CloseMin = {}

    context.buy_prices = {}
    context.buy_qty = {}
    context.buyStopLossPoint = {}
    context.buyStopLossPointTmp = {}
    context.pricesObstruction = {}


    context.sell_prices = {}
    context.sell_qty = {}
    context.sellStopLossPoint = {}
    context.sellStopLossPointTmp = {}
    context.pricesResistance = {}

    context.TimeStopLossTime = {}
    context.lastprice = {}
    context.AdxCondition = {}
    context.RealAdx = {}
    context.MA_S = {}
    context.MA_M = {}
    context.MA_L = {}
    context.MA_S2 = {}
    context.MA_M2 = {}
    context.MA_L2 = {}
    context.LongMeanCondition = {}
    context.ShortMeanCondition = {}
    context.LongCloseCondition = {}
    context.ShortCloseCondition = {}
    context.TendencyLong = {}
    context.TendencyShort = {}

    context.H1Pricetmp = {}  #买入后高点存储
    context.H1Pricetmp[context.s1] = []  
    context.H1Pricetmp[context.s2] = [] 
    context.H1Pricetmp[context.s3] = [] 
    context.H1Timetmp = {}
    context.list_betweenH1_High = {}
    context.list_betweenH1_High[context.s1] = []
    context.list_betweenH1_High[context.s2] = []
    context.list_betweenH1_High[context.s3] = []
    context.TillLastHighLimit = {} # 两个高点之间的时间间隔最小值(单位：分钟)
    context.TillLastHighLimit[context.s1] = 2
    context.TillLastHighLimit[context.s2] = 2
    context.TillLastHighLimit[context.s3] = 2
    
    
    context.L1Pricetmp = {}  #买入后低点存储
    context.L1Pricetmp[context.s1] = []  
    context.L1Pricetmp[context.s2] = [] 
    context.L1Pricetmp[context.s3] = [] 
    context.L1Timetmp = {}
    context.list_betweenL1_Low = {}
    context.list_betweenL1_Low[context.s1] = []
    context.list_betweenL1_Low[context.s2] = []
    context.list_betweenL1_Low[context.s3] = []
    context.TillLastLowLimit = {} # 两个高点之间的时间间隔最小值(单位：分钟)   
    context.TillLastLowLimit[context.s1] = context.TillLastHighLimit[context.s1]  
    context.TillLastLowLimit[context.s2] = context.TillLastHighLimit[context.s2]
    context.TillLastLowLimit[context.s2] = context.TillLastHighLimit[context.s2]
    
    
    context.BuyTime = {}   #买入时间
    context.list_AfterBuy = {}
    context.list_AfterBuy[context.s1] = []
    context.list_AfterBuy[context.s2] = []
    context.list_AfterBuy[context.s3] = []
    context.BuyRecoverTimeLimit = {}   # 距离Buy的时间(单位：分钟)  
    context.BuyRecoverTimeLimit[context.s1] = 15  
    context.BuyRecoverTimeLimit[context.s2] = 15  
    context.BuyRecoverTimeLimit[context.s3] = 15  
    context.BuyRecoverPointLimit = {}   # 距离Buy的点数(单位：跳钟)  
    context.BuyRecoverPointLimit[context.s1] = 10  
    context.BuyRecoverPointLimit[context.s2] = 5 
    context.BuyRecoverPointLimit[context.s3] = 5
    
    context.SellTime = {}   #卖出时间
    context.list_AfterSell = {}
    context.list_AfterSell[context.s1] = []
    context.list_AfterSell[context.s2] = []
    context.list_AfterSell[context.s3] = []
    context.SellRecoverTimeLimit = {}   # 距离Sell的时间(单位：分钟)  
    context.SellRecoverTimeLimit[context.s1] = context.BuyRecoverTimeLimit[context.s1]   
    context.SellRecoverTimeLimit[context.s2] = context.BuyRecoverTimeLimit[context.s2]   
    context.SellRecoverTimeLimit[context.s3] = context.BuyRecoverTimeLimit[context.s3]   
    context.SellRecoverPointLimit = {}   # 距离Sell的点数(单位：跳数)  
    context.SellRecoverPointLimit[context.s1] = context.BuyRecoverPointLimit[context.s1]  
    context.SellRecoverPointLimit[context.s2] = context.BuyRecoverPointLimit[context.s2]
    context.SellRecoverPointLimit[context.s3] = context.BuyRecoverPointLimit[context.s3]
    
    
    context.H2Price = {}
    context.BuyRecoverFactor = {}
    context.BuyRecoverFactor[context.s1] = 0.5
    context.BuyRecoverFactor[context.s2] = 0.5
    context.BuyRecoverFactor[context.s3] = 0.5
    
    context.L2Price = {}
    context.SellRecoverFactor = {}
    context.SellRecoverFactor[context.s1] = 0.5
    context.SellRecoverFactor[context.s2] = 0.5
    context.SellRecoverFactor[context.s3] = 0.5    
    
    # 两个高点的tick量小于 Len_list_limit,判断是连续上升
    context.Len_list_betweenH1_High_Limit = {}
    context.Len_list_betweenH1_High_Limit[context.s1] = 120
    context.Len_list_betweenH1_High_Limit[context.s2] = 120
    context.Len_list_betweenH1_High_Limit[context.s3] = 120
    
    context.Len_list_betweenL1_Low_Limit = {}
    context.Len_list_betweenL1_Low_Limit[context.s1] = 120
    context.Len_list_betweenL1_Low_Limit[context.s2] = 120
    context.Len_list_betweenL1_Low_Limit[context.s3] = 120
    
    #
    context.MinAfterH2 = {}
    context.MinAfterH2[context.s1] = []
    context.MinAfterH2[context.s2] = []
    context.MinAfterH2[context.s3] = []
    
    context.MaxAfterL2 = {}
    context.MaxAfterL2[context.s1] = []
    context.MaxAfterL2[context.s2] = []
    context.MaxAfterL2[context.s3] = []
    
    #两个高点的tick量大于Len_list_between_limit2,才判断是否有坑
    context.Len_list_betweenH1_High_Limit2 = {}
    context.Len_list_betweenH1_High_Limit2[context.s1] = 1000
    context.Len_list_betweenH1_High_Limit2[context.s2] = 1000
    context.Len_list_betweenH1_High_Limit2[context.s3] = 1000  
    
    context.Len_list_betweenL1_Low_Limit2 = {}
    context.Len_list_betweenL1_Low_Limit2[context.s1] = 1000
    context.Len_list_betweenL1_Low_Limit2[context.s2] = 1000
    context.Len_list_betweenL1_Low_Limit2[context.s3] = 1000
    
    #收盘前计算收益，小于BenifitBeforeClose个价位即平仓
    context.BenifitBeforeClose = {}
    context.BenifitBeforeClose[context.s1] = 5
    context.BenifitBeforeClose[context.s2] = 5
    context.BenifitBeforeClose[context.s1] = 5
    
    #持仓量移动均线
    context.firedPositionMA = True
    context.firedOpenMovePositionCriteria = {}
    context.firedOpenMovePositionCriteria[context.s1] = False
    context.firedOpenMovePositionCriteria[context.s2] = False
    context.firedOpenMovePositionCriteria[context.s3] = False
    
    context.IfPositionMA_Double = {}
    context.IfPositionMA_Double[context.s1] = False
    context.IfPositionMA_Double[context.s2] = False
    context.IfPositionMA_Double[context.s3] = False
    
    context.IfPositionMA_Tripe = {}
    context.IfPositionMA_Tripe[context.s1] = True
    context.IfPositionMA_Tripe[context.s2] = False
    context.IfPositionMA_Tripe[context.s3] = False
    
    
    context.PositionMove_SHORTPERIOD = 5
    context.PositionMove_MEANPERIOD = 20
    context.PositionMove_LONGPERIOD = 120
    context.PositionMove_OBSERVATION = 130
    
    context.PositionList = {}
    context.PositionList[context.s1] = np.full([1,context.PositionMove_OBSERVATION],np.nan)[0]
    context.PositionList[context.s2] = []
    context.PositionList[context.s3] = []
    
    context.Position_MACondition_Tripe = {}
    context.Position_MACondition_Double = {}
    
    context.PositionMA_S ={}
    context.PositionMA_M ={}
    context.PositionMA_L ={}
    
    #止损相位向后
    context.buyStopLossPoint_old = {}
    context.buyStopLossPoint_old[context.s1] = 0
    context.buyStopLossPoint_old[context.s2] = 0
    context.buyStopLossPoint_old[context.s3] = 0
    
    context.counter_buyStopLossPoint = {}
    context.counter_buyStopLossPoint[context.s1] = 0
    context.counter_buyStopLossPoint[context.s1] = 0
    context.counter_buyStopLossPoint[context.s1] = 0
    
    context.sellStopLossPoint_old = {}
    context.sellStopLossPoint_old[context.s1] = 0
    context.sellStopLossPoint_old[context.s2] = 0
    context.sellStopLossPoint_old[context.s3] = 0
    
    context.counter_sellStopLossPoint = {}
    context.counter_sellStopLossPoint[context.s1] = 0
    context.counter_sellStopLossPoint[context.s1] = 0
    context.counter_sellStopLossPoint[context.s1] = 0    
    
    
    
#变量设置end

# before_trading此函数会在每天策略交易开始前被调用，当天只会被调用一次
def before_trading(context):
    pass

def handle_tick(context, tick):
    # 开始编写你的主要的算法逻辑
    # tick 可以获取到当前订阅的合约的快照行情
    # context.portfolio 可以获取到当前投资组合信息
    


    for Context in context.Contexts:
        
        if tick.order_book_id == Context:

            context.ticklastprice[Context].append(tick.last) 
            context.ticklastpriceTime[Context].append(context.now)

            context.buy_qty[Context] = context.portfolio.positions[Context].buy_quantity
            context.sell_qty[Context] = context.portfolio.positions[Context].sell_quantity
            context.buy_prices[Context] = context.portfolio.positions[Context].buy_avg_open_price
            context.sell_prices[Context] = context.portfolio.positions[Context].sell_avg_open_price      
            allmoney = context.portfolio.total_value         #总权益
#下午15点收盘判断高低点并且释放价格list            
            if context.now.hour == 14 and context.now.minute == 59 and context.now.second == 59 and context.firedSecond:
                for Context in context.Contexts:                           #与460行重复
                    context.HighPoint[Context] = max(context.ticklastprice[Context])
                    context.LowPoint[Context] = min(context.ticklastprice[Context])
                    context.YestodayHighPoint[Context] = context.HighPoint[Context]
                    context.YestodayLowPoint[Context] = context.LowPoint[Context]
                    print('下午15点收盘时确定最高点最低点',context.HighPoint[Context],context.LowPoint[Context])
                    print('下午仓位',context.buy_qty[Context],context.sell_qty[Context])
#                    print('下午15点收盘时确定最高点最低点出现的时间',context.ticklastpriceTime[Context][context.ticklastprice[Context].index(max(context.ticklastprice[Context]))],context.ticklastpriceTime[Context][context.ticklastprice[Context].index(min(context.ticklastprice[Context]))])
        
                    context.ticklastprice[Context] = [] 
                    context.ticklastpriceTime[Context] = []
                
                context.firedFirst = True
                context.firedSecond = False
                context.firedNightOpen = True
                context.firedDayOpen = True
#下午15点收盘判断高低点并且释放价格list end                  
   
#晚上收盘判断高低点并且释放价格list        
            if context.IfTwoHL[Context] and context.now.hour == context.CloseHour[Context] and context.now.minute == context.CloseMinute[Context] -1  and context.now.second == 59 and context.firedSecond:
                for Context in context.Contexts:           #与460行重复
                    context.HighPoint[Context] = max(context.ticklastprice[Context])
                    context.LowPoint[Context] = min(context.ticklastprice[Context])
                    context.YestodayHighPoint[Context] = context.HighPoint[Context]
                    context.YestodayLowPoint[Context] = context.LowPoint[Context]
                    print('晚上收盘时确定最高点最低点',context.HighPoint[Context],context.LowPoint[Context])
                    print('晚上仓位',context.buy_qty[Context],context.sell_qty[Context])

#                    print('晚上收盘时确定最高点最低点出现的时间',context.ticklastpriceTime[Context][context.ticklastprice[Context].index(max(context.ticklastprice[Context]))],context.ticklastpriceTime[Context][context.ticklastprice[Context].index(min(context.ticklastprice[Context]))])
        
                    context.ticklastprice[Context] = [] 
                    context.ticklastpriceTime[Context] = []
                context.firedFirst = True
                context.firedSecond = False
                context.firedNightOpen = True
                context.firedDayOpen = True
#晚上收盘判断高低点并且释放价格list end
            
            
                
            if context.fired[Context]:
                plot('short',context.MA_S[Context][-1])
                plot('Mean',context.MA_M[Context][-1])
                plot('long',context.MA_L[Context][-1])

#夜盘开盘            
            if context.now.hour == context.OpenHour[Context] and context.now.minute == 0 and context.now.second < 2 and context.firedFirst and context.firedNightOpen:            #夜盘开盘完成日线级别指标的赋值
            
                context.High[Context] = history_bars(Context,context.OBSERVATION,'1d','high')
                context.Low[Context] = history_bars(Context,context.OBSERVATION,'1d','low')
                context.Close[Context] = history_bars(Context,context.OBSERVATION,'1d','close')
                
#                context.RealAdx[Context] = talib.ADX(context.High[Context], context.Low[Context], context.Close[Context], timeperiod = context.ADXTimePeriod)
#                context.AdxCondition[Context] = context.RealAdx[Context][-1] > context.ADX       #RealAdxCondition 字典存储
            
                context.MA_S[Context] = talib.MA(context.Close[Context], context.SHORTPERIOD, matype=0)   #文丰注意可以改
                context.MA_M[Context] = talib.MA(context.Close[Context], context.MEANPERIOD, matype=0) 
                context.MA_L[Context] = talib.MA(context.Close[Context], context.LONGPERIOD, matype=0)
                
                if context.IfThreeMA[Context]:
                    context.LongMeanCondition[Context] = context.MA_S[Context][-1] > context.MA_M[Context][-1] and context.MA_M[Context][-1] > context.MA_L[Context][-1] and context.MA_L[Context][-1] > context.MA_L[Context][-2]
                    context.ShortMeanCondition[Context] = context.MA_S[Context][-1] < context.MA_M[Context][-1] and context.MA_M[Context][-1] < context.MA_L[Context][-1] and context.MA_L[Context][-1] < context.MA_L[Context][-2]
                elif context.IfTwoMA[Context]:
                    context.LongMeanCondition[Context] = context.MA_S[Context][-1] > context.MA_M[Context][-1]
                    context.ShortMeanCondition[Context] = context.MA_S[Context][-1] < context.MA_M[Context][-1]
                else:
                    context.LongMeanCondition[Context] = True
                    context.ShortMeanCondition[Context] = True
                    
                    
                context.LongCloseCondition[Context] = context.MA_S[Context][-1] < context.MA_M[Context][-1] and context.buy_qty[Context] > 0
                context.ShortCloseCondition[Context] = context.MA_S[Context][-1] > context.MA_M[Context][-1] and context.sell_qty[Context] > 0
                
                if context.LongCloseCondition[Context]:
                    sell_close(Context, context.buy_qty[Context])
                    print('均线大赚止损++++++++++++++++++++++++')
                if context.ShortCloseCondition[Context]:
                    buy_close(Context, context.buy_qty[Context])
                    print('均线大赚止损++++++++++++++++++++++++')
                    
                context.TendencyLong[Context] = context.LongMeanCondition[Context]            #多趋势条件
                context.TendencyShort[Context] = context.ShortMeanCondition[Context]          #空趋势条件     
                
                context.lastprice[Context] = tick.last
                
                print('晚上21点开盘时最高点最低点',context.HighPoint[Context],context.LowPoint[Context])
                context.fired[Context] = True
                context.firedSecond = True
                context.firedNightOpen = False     #夜盘开盘判断日线级别指标 只在开盘时打开一次

                pass                                                                                                            #夜盘开盘内完成日线级别指标的赋值end
#夜盘开盘end


#日盘开盘
            if context.now.hour == 9 and context.now.minute == 0 and context.now.second < 2 and context.firedFirst and context.firedDayOpen:            #白天开盘完成日线级别指标的赋值
            
                context.High[Context] = history_bars(Context,context.OBSERVATION,'1d','high')
                context.Low[Context] = history_bars(Context,context.OBSERVATION,'1d','low')
                context.Close[Context] = history_bars(Context,context.OBSERVATION,'1d','close')

            
                context.MA_S[Context] = talib.MA(context.Close[Context], context.SHORTPERIOD, matype=0)   #文丰注意可以改
                context.MA_M[Context] = talib.MA(context.Close[Context], context.MEANPERIOD, matype=0) 
                context.MA_L[Context] = talib.MA(context.Close[Context], context.LONGPERIOD, matype=0)
                
                if context.IfThreeMA[Context]:
                    context.LongMeanCondition[Context] = context.MA_S[Context][-1] > context.MA_M[Context][-1] and context.MA_M[Context][-1] > context.MA_L[Context][-1] and context.MA_L[Context][-1] > context.MA_L[Context][-2]
                    context.ShortMeanCondition[Context] = context.MA_S[Context][-1] < context.MA_M[Context][-1] and context.MA_M[Context][-1] < context.MA_L[Context][-1] and context.MA_L[Context][-1] < context.MA_L[Context][-2]
                elif context.IfTwoMA[Context]:
                    context.LongMeanCondition[Context] = context.MA_S[Context][-1] > context.MA_M[Context][-1]
                    context.ShortMeanCondition[Context] = context.MA_S[Context][-1] < context.MA_M[Context][-1]
                else:
                    context.LongMeanCondition[Context] = True
                    context.ShortMeanCondition[Context] = True

                context.LongCloseCondition[Context] = context.MA_S[Context][-1] < context.MA_M[Context][-1] and context.buy_qty[Context] > 0
                context.ShortCloseCondition[Context] = context.MA_S[Context][-1] > context.MA_M[Context][-1] and context.sell_qty[Context] > 0
                
                if context.LongCloseCondition[Context]:
                    sell_close(Context, context.buy_qty[Context])
                    print('均线大赚止损++++++++++++++++++++++++')
                if context.ShortCloseCondition[Context]:
                    buy_close(Context, context.buy_qty[Context])
                    print('均线大赚止损++++++++++++++++++++++++')
                
                context.TendencyLong[Context] = context.LongMeanCondition[Context]            #多趋势条件
                context.TendencyShort[Context] = context.ShortMeanCondition[Context]          #空趋势条件     
                
                context.lastprice[Context] = tick.last

                print('白天9点开盘时最高点最低点',context.HighPoint[Context],context.LowPoint[Context])
                context.fired[Context] = True
                context.firedSecond = True
                context.firedDayOpen = False     #白天开盘判断日线级别指标 只在开盘时打开一次
                pass                                                                                                            #白天开盘内完成日线级别指标的赋值end
#日盘开盘结束


            context.buy_qty[Context] = context.portfolio.positions[Context].buy_quantity
            context.sell_qty[Context] = context.portfolio.positions[Context].sell_quantity
            context.buy_prices[Context] = context.portfolio.positions[Context].buy_avg_open_price
            context.sell_prices[Context] = context.portfolio.positions[Context].sell_avg_open_price
            
#给高低点迭代赋值
            if context.fired[Context] and context.firedFirst:
                context.HighPoint[Context] = max(context.HighPoint[Context],context.lastprice[Context])
                context.LowPoint[Context] = min(context.LowPoint[Context],context.lastprice[Context])
                context.lastprice[Context] = tick.last
                pass
#给高低点迭代赋值end

#交易时间段
#            dayopenCondition = (context.now.hour > 9) or (context.now.hour == 9 and context.now.minute > context.opencloseminute[Context])
            dayopenCondition = (context.now.hour >= 9) 
            daycloseCondition = (context.now.hour < 14) or (context.now.hour == 14 and context.now.minute < 60 - context.opencloseminute[Context])
#            nightopenCondition = (context.now.hour > context.OpenHour[Context]) or (context.now.hour == context.OpenHour[Context] and context.now.minute > context.opencloseminute[Context] )
            nightopenCondition = (context.now.hour >= context.OpenHour[Context]) 
            nightcloseCondition = (context.now.hour < context.CloseHour[Context] ) or ( context.now.hour == context.CloseHour[Context] and context.now.minute < context.CloseMinute[Context] - context.opencloseminute[Context])
#交易时间段end    

#开仓条件
            openCloseCondition = (dayopenCondition and daycloseCondition) or (nightopenCondition and nightcloseCondition)  #交易时间条件
            
            if context.fired[Context]:
                LongPriceCondition = tick.last > context.HighPoint[Context] and tick.last <= context.HighPoint[Context] + context.fudong[Context] and context.buy_qty[Context] == 0 and context.sell_qty[Context] == 0 and context.HighPoint[Context] - context.YestodayHighPoint[Context] < context.HighLowFactor[Context]*instruments(Context).tick_size()#开多的价仓条件
                ShortPriceCondition = tick.last < context.LowPoint[Context] and tick.last >= context.LowPoint[Context] - context.fudong[Context] and context.sell_qty[Context] == 0 and context.buy_qty[Context] == 0 and context.YestodayLowPoint[Context] - context.LowPoint[Context] < context.HighLowFactor[Context]*instruments(Context).tick_size()#开空的价仓条件
            
                
                
                
#开仓条件end

#开仓
            if context.fired[Context] and LongPriceCondition and context.TendencyLong[Context] and context.firedOpenMovePositionCriteria[Context] and openCloseCondition: 
          
                if context.firedAutoObstructionResistance:
                    LocalHighlowA = history_bars(Context,context.AutoObstructionResistanceMinuteNumber,'3m','low')
                    LocalHighlowA1 = list(LocalHighlowA)
                    LocalHighlowB = LocalHighlowA1[1:]
                    LocalHighlowB.append(tick.last)
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
                            context.LocalLow[i] =[LocalLowPointIndex[i], LocalHighlowA[LocalLowPointIndex[i]]]
                        del i
                        context.IFLocalPointExist = True
                    else :
                        context.IFLocalPointExist = False
                        print('开多仓前没有坑')

                    context.IFAOR = True
                    
                    if context.IFLocalPointExist and context.IFAOR :
                        for i in range(0, len(context.LocalLow)):
                            print('多仓有坑，tick.last - context.LocalLow[i][1]',tick.last,context.LocalLow[i][1],tick.last - context.LocalLow[i][1])
#                            if (tick.last - context.LocalLow[i][1]) > context.FactorAOR * context.zhisundianwei[Context] * instruments(Context).tick_size() and (tick.last - context.LocalLow[i][1]) < context.zhisundianwei[Context] * instruments(Context).tick_size() and context.IFAOR:

                            if (tick.last - context.LocalLow[i][1]) > context.FactorAOR * context.zhisundianwei[Context] * instruments(Context).tick_size()  and context.IFAOR:
                                # 大于20个点立刻退出
                                if (tick.last - context.LocalLow[i][1]) > context.zhisundianwei[Context] * instruments(Context).tick_size():
                                    context.IFAOR = False
                                    break
                                    
                                
                                context.buyStopLossPoint[Context] = context.LocalLow[i][1]

                                print('多，前期支持位为止损点:',context.buyStopLossPoint[Context])

                                if context.sell_qty[Context] > 0:
                                    buy_close(Context, context.buy_qty[Context])
                                if context.ifcangwei :
                                    shoushu = int(context.cangwei[Context]*(allmoney/tick.last))
                                else :
                                    shoushu = 1

                                buy_open(Context,float(shoushu))   #开仓
                                context.stoplosstimeFactor[Context] = 0
                                context.firedOpenRecoverCost[Context] = True
                                print('id',Context,'多开:',tick.last,tick.bid[0],tick.ask[0],',','大于高点：',context.HighPoint[Context],',','做多手数：',shoushu)
                                shoushu = 0 
                                context.IFLocalPointExist = False
                                context.IFAOR = False
                                
                                context.H1Pricetmp[Context] = tick.last 
                                context.H1Timetmp[Context] = context.now
                                context.BuyTime[Context] = context.now
                                context.H2Price[Context] = tick.last
                                context.MinAfterH2[Context] = tick.last
      
            if context.fired[Context] and ShortPriceCondition and openCloseCondition and context.TendencyShort[Context] and context.firedOpenMovePositionCriteria[Context]:
                if context.firedAutoObstructionResistance:
#                        LocalHighlowA = np.array([1,2,3,4,9,8,7,4,5,6,6,6,6,7,8,5,5,5,5,9,10]);
                    LocalHighlowA = history_bars(Context,context.AutoObstructionResistanceMinuteNumber,'3m','high')
                    LocalHighlowA1 = list(LocalHighlowA)
                    LocalHighlowB = LocalHighlowA1[1:]
                    LocalHighlowB.append(tick.last)
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
                            context.LocalHigh[i] =[LocalHighPointIndex[i], LocalHighlowA[LocalHighPointIndex[i]]]
                        del i             
                        context.IFLocalPointExist = True
                    else :
                        context.IFLocalPointExist = False 
                        print('开空仓前没有包')
                    context.IFAOR = True
                    if context.IFLocalPointExist and context.IFAOR:
                        for i in range(0, len(context.LocalHigh)):
                            print('空仓有包，context.LocalHigh[i][1] - tick.last',context.LocalHigh[i][1] , tick.last,context.LocalHigh[i][1] - tick.last)
#                            if (context.LocalHigh[i][1] - tick.last) > context.FactorShort_Long * context.FactorAOR * context.zhisundianwei[Context] * instruments(Context).tick_size() and (context.LocalHigh[i][1] - tick.last) < context.FactorShort_Long * context.zhisundianwei[Context] * instruments(Context).tick_size() and context.IFAOR:

                            if (context.LocalHigh[i][1] - tick.last) > context.FactorAOR * context.zhisundianwei[Context] * instruments(Context).tick_size()  and context.IFAOR:
                                
                                if (context.LocalHigh[i][1] - tick.last) > context.zhisundianwei[Context] * instruments(Context).tick_size():
                                    context.IFAOR = False
                                    break

                                context.sellStopLossPoint[Context] = context.LocalHigh[i][1]

                                if context.buy_qty[Context] > 0:
                                    sell_close(Context, context.buy_qty[Context])
                
                                if context.ifcangwei :
                                    shoushu = int(context.cangwei[Context]*(allmoney/tick.last))
                                    pass
                                else :
                                    shoushu = 1
                                
                                sell_open(Context,float(shoushu))                                 
                                print('空，前期阻力位为止损点',context.sellStopLossPoint[Context])
                                
                                context.stoplosstimeFactor[Context] = 0
                                context.firedOpenRecoverCost[Context] = True
                                print('id',Context,'空开:',tick.last,tick.bid[0],tick.ask[0],',','小于低点：',context.LowPoint[Context],',','做空手数：',shoushu)
                                shoushu = 0                                 

                                context.IFLocalPointExist = False
                                context.IFAOR = False
                                
                                context.L1Pricetmp[Context] = tick.last 
                                context.L1Timetmp[Context] = context.now
                                context.SellTime[Context] = context.now
                                context.L2Price[Context] = tick.last
                                context.MaxAfterL2[Context] = tick.last
                                


#开仓end


#智能止损
            if context.fireRecover_and_Move:
                if context.buy_qty[Context] > 0:
                    # 双高点
                    if tick.last <= context.H1Pricetmp[Context] :
                        context.list_betweenH1_High[Context].append(tick.last)
                    elif tick.last > context.H1Pricetmp[Context] :
#                        if context.now - context.H1Timetmp[Context] < datetime.timedelta(minutes = context.TillLastHighLimit[Context]) :
                        if len(context.list_betweenH1_High[Context]) < context.Len_list_betweenH1_High_Limit[Context] :
                            context.list_betweenH1_High[Context] = []
                            context.H1Pricetmp[Context] = tick.last
                        elif len(context.list_betweenH1_High[Context]) > context.Len_list_betweenH1_High_Limit2[Context] :
                            
                            if len(context.list_betweenH1_High[Context]) != 0  :
                                    
                                if context.buyStopLossPoint_old[Context] != min(context.list_betweenH1_High[Context]) :
                                    context.counter_buyStopLossPoint[Context] =  context.counter_buyStopLossPoint[Context] + 1 
                                    
                                    if context.counter_buyStopLossPoint[Context] > 1:
                                        context.buyStopLossPoint[Context] = context.buyStopLossPoint_old[Context]
                                        context.buyStopLossPoint_old[Context]= min(context.list_betweenH1_High[Context])
                                        #print('恢复成本价到坑1',context.buyStopLossPoint[Context])
                                    elif context.counter_buyStopLossPoint[Context] == 1:
                                        context.buyStopLossPoint_old[Context]= min(context.list_betweenH1_High[Context])
                                    
                                context.H1Pricetmp[Context] = tick.last
                                context.list_betweenH1_High[Context] = []
                                
                                    
                    # 1/2离场
                    if tick.last >= context.H2Price[Context] :
                        #context.list_AfterBuy[Context] = []
                        context.H2Price[Context] = tick.last
                        context.MinAfterH2[Context] = context.H2Price[Context]
                    else : 
                        if context.MinAfterH2[Context] > tick.last:
                            context.MinAfterH2[Context] = tick.last
                        
                        #context.list_AfterBuy[Context].append(tick.last)          
                        if  context.H2Price[Context] - context.MinAfterH2[Context] > context.BuyRecoverPointLimit[Context]*instruments(Context).tick_size() :
                            if tick.last - context.MinAfterH2[Context] > context.BuyRecoverFactor[Context] * (context.H2Price[Context] - context.MinAfterH2[Context]) :
                                if context.buyStopLossPoint_old[Context] != context.MinAfterH2[Context] :
                                    context.counter_buyStopLossPoint[Context] =  context.counter_buyStopLossPoint[Context] + 1
                                    
                                    if context.counter_buyStopLossPoint[Context] > 1:
                                        context.buyStopLossPoint[Context] = context.buyStopLossPoint_old[Context]
                                        context.buyStopLossPoint_old[Context] = context.MinAfterH2[Context]
                                        #print('恢复成本价到坑2',context.buyStopLossPoint[Context])
                                    elif context.counter_buyStopLossPoint[Context] == 1:
                                        context.buyStopLossPoint_old[Context] = context.MinAfterH2[Context]
                                    
                                
                                
                                
                if context.sell_qty[Context] > 0:
                    # 双低点
                    if tick.last >= context.L1Pricetmp[Context] :
                            context.list_betweenL1_Low[Context].append(tick.last)
                    elif tick.last < context.L1Pricetmp[Context] :
#                        if context.now - context.L1Timetmp[Context] <  datetime.timedelta(minutes = context.TillLastLowLimit[Context]):
                        if len(context.list_betweenL1_Low[Context]) < context.Len_list_betweenL1_Low_Limit[Context] :
                            context.list_betweenL1_Low[Context] = []
                            context.L1Pricetmp[Context] = tick.last
                        elif len(context.list_betweenL1_Low[Context]) > context.Len_list_betweenL1_Low_Limit2[Context] :
                            if len(context.list_betweenL1_Low[Context]) != 0 :
                                
                                if context.sellStopLossPoint_old[Context] != max(context.list_betweenL1_Low[Context]) :
                                    context.counter_sellStopLossPoint[Context] =  context.counter_sellStopLossPoint[Context] + 1 
                                    
                                    if context.counter_sellStopLossPoint[Context] > 1:
                                        context.sellStopLossPoint[Context] = context.sellStopLossPoint_old[Context]
                                        context.sellStopLossPoint_old[Context] = max(context.list_betweenL1_Low[Context])
                                        #print('恢复成本价到包1',context.sellStopLossPoint[Context])
                                    elif context.counter_sellStopLossPoint[Context] == 1:
                                        context.sellStopLossPoint_old[Context] = max(context.list_betweenL1_Low[Context])
                                    
                                context.L1Pricetmp[Context] = tick.last
                                context.list_betweenL1_Low[Context] = []
                                
                    # 1/2离场         
                    if tick.last <= context.L2Price[Context] :
                        #context.list_AfterSell[Context] = []
                        context.L2Price[Context] = tick.last
                        context.MaxAfterL2[Context] = context.L2Price[Context]
                    else : 
                        if context.MaxAfterL2[Context] < tick.last :
                            context.MaxAfterL2[Context] = tick.last
                        #context.list_AfterSell[Context].append(tick.last)          
                        if  context.MaxAfterL2[Context] - context.L2Price[Context] > context.SellRecoverPointLimit[Context]*instruments(Context).tick_size() :
                            if context.MaxAfterL2[Context] - tick.last  > context.SellRecoverFactor[Context] * (context.MaxAfterL2[Context] - context.L2Price[Context]) :
                                if context.sellStopLossPoint_old[Context] != context.MaxAfterL2[Context] :
                                    context.counter_sellStopLossPoint[Context] =  context.counter_sellStopLossPoint[Context] + 1 
                                    
                                    if context.counter_sellStopLossPoint[Context] > 1:
                                        context.sellStopLossPoint[Context] = context.sellStopLossPoint_old[Context]
                                        context.sellStopLossPoint_old[Context] = context.MaxAfterL2[Context]
                                        #print('恢复成本价到包2',context.sellStopLossPoint[Context])    
                                    elif context.counter_sellStopLossPoint[Context] == 1:
                                        context.sellStopLossPoint_old[Context] = context.MaxAfterL2[Context]
            
            
                                
#智能止损end

# 仓位移动平均线
            if context.now.second == 2 :
                context.firedPositionMA = True
                
            if context.now.second == 1 and context.firedPositionMA :
                context.PositionList[Context] = np.delete(context.PositionList[Context],0)
                context.PositionList[Context] = context.PositionList[Context].tolist()
                context.PositionList[Context].append(tick.open_interest)
                context.PositionList[Context] = np.array(context.PositionList[Context])
                context.firedPositionMA = False
                
                context.PositionMA_S[Context] = talib.MA(context.PositionList[Context], context.PositionMove_SHORTPERIOD, matype=0)   
                context.PositionMA_M[Context] = talib.MA(context.PositionList[Context], context.PositionMove_MEANPERIOD, matype=0) 
                context.PositionMA_L[Context] = talib.MA(context.PositionList[Context], context.PositionMove_LONGPERIOD, matype=0)
            
                context.Position_MACondition_Tripe[Context] =  (context.PositionMA_S[Context][-1] - context.PositionMA_M[Context][-1] > 0) and (context.PositionMA_M[Context][-1] - context.PositionMA_L[Context][-1] > 0) 
                
                context.Position_MACondition_Double[Context] =  (context.PositionMA_S[Context][-1] - context.PositionMA_M[Context][-1] > 0) 
                    
                    
                if context.IfPositionMA_Double[Context] :
                    context.firedOpenMovePositionCriteria[Context] = context.Position_MACondition_Double[Context]
                if context.IfPositionMA_Tripe[Context] :
                    context.firedOpenMovePositionCriteria[Context] = context.Position_MACondition_Tripe[Context]
# 仓位移动平均线end                         
                

                              


#止损出场
            if context.buy_qty[Context] > 0 and tick.last <= context.buyStopLossPoint[Context]:
                sell_close(Context, context.buy_qty[Context])
                print('卖平止损：',tick.last-context.buy_prices[Context])
                context.list_AfterBuy[Context] = []
                context.list_betweenH1_High[Context] = []
                context.counter_buyStopLossPoint[Context] = 0
                context.buyStopLossPoint_old[Context] = 0
                
                

            
            if context.sell_qty[Context] > 0 and tick.last >= context.sellStopLossPoint[Context]:
                buy_close(Context, context.sell_qty[Context])
                print('买平止损：',context.sell_prices[Context]-tick.last)
                context.list_AfterSell[Context] = []
                context.list_betweenL1_Low[Context] = []
                context.counter_sellStopLossPoint[Context] = 0
                context.sellStopLossPoint_old[Context] = 0
#止损出场end

#移动止损
            if context.firedOpenMoveStopLoss[Context]:
                if context.buy_qty[Context] > 0 and int((tick.last - context.buy_prices[Context]) / (context.stoplossMovePoint[Context] * instruments(Context).tick_size())) > context.stoplosstimeFactor[Context]:
                    context.stoplosstimeFactor[Context] = int((tick.last - context.buy_prices[Context]) / (context.stoplossMovePoint[Context] * instruments(Context).tick_size()))
                    
                    if (1.0 - context.MoveFactor) * (tick.last - context.buy_prices[Context]) > context.MoveFactorForPrice * tick.last :
                        context.buyStopLossPointTmp[Context] = (1 - context.MoveFactorForPrice) * tick.last
                        
                        if context.buyStopLossPointTmp[Context] >= context.buyStopLossPoint[Context] :
                            context.buyStopLossPoint[Context] = context.buyStopLossPointTmp[Context]
                    else :
                        context.buyStopLossPoint[Context] = context.buy_prices[Context] + (context.MoveFactor*context.stoplosstimeFactor[Context]*context.stoplossMovePoint[Context] * instruments(Context).tick_size())
                        
                    context.firedOpenRecoverCost[Context] = False

                if context.sell_qty[Context] > 0 and int((context.sell_prices[Context] - tick.last) / (context.stoplossMovePoint[Context] * instruments(Context).tick_size())) > context.stoplosstimeFactor[Context]:
                    context.stoplosstimeFactor[Context] = int((context.sell_prices[Context] - tick.last) / (context.stoplossMovePoint[Context] * instruments(Context).tick_size()))
                    
                    if (1.0 - context.MoveFactor) * (context.sell_prices[Context] - tick.last) > context.MoveFactorForPrice * tick.last :
                        context.sellStopLossPointTmp[Context] = (1 + context.MoveFactorForPrice) * tick.last
                        
                        if context.sellStopLossPointTmp[Context] <= context.sellStopLossPoint[Context] :
                            context.sellStopLossPoint[Context] = context.sellStopLossPointTmp[Context]
                    else :
                        context.sellStopLossPoint[Context] = context.sell_prices[Context] - (context.MoveFactor*context.stoplosstimeFactor[Context]*context.stoplossMovePoint[Context] * instruments(Context).tick_size())
                        

#                    print('移动卖止损到',context.sellStopLossPoint[Context])
                    context.firedOpenRecoverCost[Context] = False
#移动止损end


#移动平均线止损
            if context.now.second == 2 :
                context.firedMA = True
                
            if context.now.second == 1 and context.firedMA :
                context.minlastprice[Context] = np.delete(context.minlastprice[Context],0)
                context.minlastprice[Context] = context.minlastprice[Context].tolist()
                context.minlastprice[Context].append(tick.last)
                context.minlastprice[Context] = np.array(context.minlastprice[Context])
                context.firedMA = False
                
                if (context.buy_qty[Context] > 0 or context.sell_qty[Context] > 0) and context.firedOpenMoveAverageStopLoss[Context] and context.firedFirst :
                    
                    context.MA_S2[Context] = talib.MA(context.minlastprice[Context], context.SHORTPERIOD2, matype=0)   
                    context.MA_M2[Context] = talib.MA(context.minlastprice[Context], context.MEANPERIOD2, matype=0) 
                    context.MA_L2[Context] = talib.MA(context.minlastprice[Context], context.LONGPERIOD2, matype=0)
                    
                    if context.MA_S2[Context][-1] - context.MA_M2[Context][-1] > 0:
                        if context.MA_S2[Context][-2] - context.MA_M2[Context][-2] < 0:
                            context.Goldcross[Context] = True
                        elif context.MA_S2[Context][-2] == context.MA_M2[Context][-2]:
                            i = -2
                            while context.MA_S2[Context][i] == context.MA_M2[Context][i]:
                                i = i - 1
                            if context.MA_S2[Context][i] - context.MA_M2[Context][i] < 0:
                                context.Goldcross[Context] = True
                            else :
                                context.Goldcross[Context] = False
                        else :
                            context.Goldcross[Context] = False                        
                    
                    if context.MA_S2[Context][-1] - context.MA_M2[Context][-1] < 0:
                        if context.MA_S2[Context][-2] - context.MA_M2[Context][-2] > 0:
                            context.Deadcross[Context] = True
                        elif context.MA_S2[Context][-2] == context.MA_M2[Context][-2]:
                            i = -2
                            while context.MA_S2[Context][i] == context.MA_M2[Context][i]:
                                i = i - 1
                            if context.MA_S2[Context][i] - context.MA_M2[Context][i] > 0:
                                context.Deadcross[Context] = True
                            else :
                                context.Deadcross[Context] = False
                        else :
                            context.Deadcross[Context] = False   
                            
                    if context.buy_qty[Context] > 0 and context.Deadcross[Context] :
                        sell_close(Context, context.buy_qty[Context])
                        context.Deadcross[Context] = False
                        print('~~~~~~~~~~~~~~~~~~~~~~~~~买开通过均线卖平',context.MA_S2[Context][-1],context.MA_M2[Context][-1],context.MA_L2[Context][-1])          

                    if context.sell_qty[Context] > 0 and context.Goldcross[Context] :
                        buy_close(Context, context.buy_qty[Context])
                        print('~~~~~~~~~~~~~~~~~~~~~~~~~~卖开通过均线买平',context.MA_S2[Context][-1],context.MA_M2[Context][-1],context.MA_L2[Context][-1])  
                        context.Goldcross[Context] = False

#移动平均线止损end

#下午或者晚上收盘，平仓出场

            if context.CloseClose[Context]:
                if context.now.hour == 14 and context.now.minute == 60 - 1:
                    if context.buy_qty[Context] > 0 and tick.last - context.buy_prices[Context] < context.BenifitBeforeClose[Context] * instruments(Context).tick_size() :
                        sell_close(Context, context.buy_qty[Context])
                        print('日内下午三点之前卖平',Context)

                    if context.sell_qty[Context] > 0 and context.buy_prices[Context] - tick.last  < context.BenifitBeforeClose[Context] * instruments(Context).tick_size():
                        buy_close(Context, context.sell_qty[Context])
                        print('日内下午三点之前买平',Context)


                if context.now.hour == context.CloseHour[Context] and context.now.minute == context.CloseMinute[Context] - 1:
                    if context.buy_qty[Context] > 0 and tick.last - context.buy_prices[Context] < context.BenifitBeforeClose[Context] * instruments(Context).tick_size():
                        sell_close(Context, context.buy_qty[Context])
                        print('日内晚收盘前卖平',Context)
                    if context.sell_qty[Context] > 0 and context.buy_prices[Context] - tick.last  < context.BenifitBeforeClose[Context] * instruments(Context).tick_size():
                        buy_close(Context, context.sell_qty[Context])
                        print('日内晚收盘前买平',Context)

  
def after_trading(context):

    pass