from datetime import date, time, datetime, timedelta
import sys 
import numpy as np
import talib
from collections import defaultdict
# import datetime
sys.path.append("..") 
from pystarquant.strategy.strategy_base import IndicatorBase


def nan2mean(x):
    x[np.isnan(x)] = np.mean(x[~np.isnan(x)])


# class DemoIndicator(IndicatorBase):
#     """
#     Demo indicator for indicator analysis
#     """
#     buyratio = 1.0
#     closeratio = 0.5

#     parameters = ['buyratio', 'closeratio']


#     def calculate(self):
#         """
#         Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
#         Should return dict of list, each list's length should equal to len(self.datas)
#         each element of the dict will show in one chart
#         note: number of curve should less than 10, other wise color will duplicate
#         for example: 
#             results = defaultdict(list)
#             vols = [bar.volume for bar in self.datas]
#             results['vol'] = vols
#             return results      
#         """
#         results = defaultdict(list)

#         # vols = [bar.volume for bar in self.datas]
#         # results['vol'] = vols
#         myindicator = []
#         myindicator2 = []
#         for bar in self.datas:
#             if bar.bid_totalmoney:
#                 myindicator.append(bar.ask_totalmoney/bar.bid_totalmoney - self.buyratio)
#             else:
#                 myindicator.append(0)   
#             if bar.bid_bigmoney:
#                 myindicator2.append(bar.ask_bigmoney/bar.bid_bigmoney - self.closeratio)
#             else:
#                 myindicator2.append(0) 

#         results['totalmoney'] = myindicator
#         results['bigmoney'] = myindicator2


#         return results    

class Volume(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    buyratio = 1.0
    closeratio = 0.5

    parameters = []

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        vols = [bar.volume for bar in self.datas]
        results['vol'] = vols

        return results, signals_up, signals_down 

class Empty(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """

    parameters = ['primary']
    
    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []


        return results, signals_up, signals_down 

class OrderFlow(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """


    test = 0
    entrydt = datetime(2020,1,2,9,30,0)
    parameters = ['primary','test','entrydt']

    primary =  True
    
    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []


        return results, signals_up, signals_down 


class DeltaVolume(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    fast_window = 10
    slow_window = 5000

    parameters = ['fast_window', 'slow_window']

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        vols = [bar.volume for bar in self.datas]
        deltav = [0]
        for i in range(1,len(vols)):
            dv = vols[i] - vols[i-1]
            if abs(dv) > 5e5:
                dv = 0
            deltav.append(dv)

        deltav = np.array([float(v) for v in deltav])
        


        smaslow = talib.SMA(deltav, self.slow_window)
        nan2mean(smaslow)

        smafast = talib.SMA(deltav, self.fast_window)
        nan2mean(smafast)


        std = talib.STDDEV(deltav, self.slow_window)
        nan2mean(std)

        # results['dv'] = deltav
        results['dvfast'] = smafast
        results['dvslow'] = smaslow

        return results, signals_up, signals_down 

class OpenInterest(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    buyratio = 1.0
    closeratio = 0.5

    parameters = []


    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        vols = [bar.open_interest for bar in self.datas]
        results['openinterest'] = vols

        return results, signals_up, signals_down 




class Boll(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    boll_window = 26
    boll_dev = 2

    parameters = ['boll_window', 'boll_dev']
    primary = True

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []


        size = len(self.datas)
        close = np.array([float(bar.close_price) for bar in self.datas])
        sma = talib.SMA(close, self.boll_window)
        sma[np.isnan(sma)] = np.mean(sma[~np.isnan(sma)])

        smalong = talib.SMA(close, 2*self.boll_window)
        smalong[np.isnan(smalong)] = np.mean(smalong[~np.isnan(smalong)])

        std = talib.STDDEV(close, self.boll_window)
        std[np.isnan(std)] = np.mean(std[~np.isnan(std)])        


        boll_up = []
        boll_down = []
        for i in range(size):
            boll_up.append(sma[i]+self.boll_dev*std[i])
            boll_down.append(sma[i]-self.boll_dev*std[i])
            if smalong[i] > sma[i]+self.boll_dev*std[i]:
                signals_down.append((i,smalong[i]))
            if smalong[i] < sma[i]-self.boll_dev*std[i]:
                signals_up.append((i,smalong[i]))            
        # results['close_price'] = close
        results['sma_short'] = sma
        results['sma_long'] = smalong
        results['boll_up'] = boll_up
        results['boll_down'] = boll_down

        return results, signals_up, signals_down 




class MA(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    ma5 = 5
    ma10 = 10
    ma20 = 20

    parameters = ['ma5', 'ma10','ma20']

    primary =  True

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        close = np.array([float(bar.close_price) for bar in self.datas])

        sma5 = talib.SMA(close, self.ma5)
        sma5[np.isnan(sma5)] = np.mean(sma5[~np.isnan(sma5)])

        sma10 = talib.SMA(close, self.ma10)
        sma10[np.isnan(sma10)] = np.mean(sma10[~np.isnan(sma10)])

        sma20 = talib.SMA(close, self.ma20)
        sma20[np.isnan(sma20)] = np.mean(sma20[~np.isnan(sma20)])        

        # results['close_price'] = close
        results['ma5'] = sma5
        results['ma10'] = sma10
        results['ma20'] = sma20


        return results, signals_up, signals_down






class MACD(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    fast_window = 12
    slow_window = 26
    signal_window = 9

    parameters = ['fast_window', 'slow_window','signal_window']


    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        size = len(self.datas)
        close = np.array([float(bar.close_price) for bar in self.datas])
        macd, signal, hist = talib.MACD(
            close, self.fast_window, self.slow_window, self.signal_window
        )

        macd[np.isnan(macd)] = np.mean(macd[~np.isnan(macd)])
        signal[np.isnan(signal)] = np.mean(signal[~np.isnan(signal)])
        hist[np.isnan(hist)] = np.mean(hist[~np.isnan(hist)])

        # results['close_price'] = close
        results['macd'] = macd
        results['signal'] = signal
        results['hist'] = hist


        return results, signals_up, signals_down

class CCI(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    window = 12

    parameters = ['window']

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        size = len(self.datas)
        close = np.array([float(bar.close_price) for bar in self.datas])
        high = np.array([float(bar.high_price) for bar in self.datas])
        low = np.array([float(bar.low_price) for bar in self.datas])

        cci = talib.CCI(
            high, low, close, self.window
        )

        cci[np.isnan(cci)] = np.mean(cci[~np.isnan(cci)])

        results['cci'] = cci



        return results, signals_up, signals_down

class ATR(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    window = 12

    parameters = ['window']

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        size = len(self.datas)
        close = np.array([float(bar.close_price) for bar in self.datas])
        high = np.array([float(bar.high_price) for bar in self.datas])
        low = np.array([float(bar.low_price) for bar in self.datas])

        atr = talib.ATR(
            high, low, close, self.window
        )

        atr[np.isnan(atr)] = np.mean(atr[~np.isnan(atr)])

        results['atr'] = atr

        return results, signals_up, signals_down

class RSI(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    window = 12

    parameters = ['window']

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        size = len(self.datas)
        close = np.array([float(bar.close_price) for bar in self.datas])

        rsi = talib.RSI(close, self.window)

        rsi[np.isnan(rsi)] = np.mean(rsi[~np.isnan(rsi)])

        results['rsi'] = rsi

        return results, signals_up, signals_down

class ADX(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    window = 12

    parameters = ['window']

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        size = len(self.datas)
        close = np.array([float(bar.close_price) for bar in self.datas])
        high = np.array([float(bar.high_price) for bar in self.datas])
        low = np.array([float(bar.low_price) for bar in self.datas])

        adx = talib.ADX(
            high, low, close, self.window
        )

        adx[np.isnan(adx)] = np.mean(adx[~np.isnan(adx)])

        results['adx'] = adx

        return results, signals_up, signals_down


class OBV(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    parameters = []

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        size = len(self.datas)
        close = np.array([float(bar.close_price) for bar in self.datas])
        volume = np.array([float(bar.volume) for bar in self.datas])
        obv = talib.OBV(close, volume)

        obv[np.isnan(obv)] = np.mean(obv[~np.isnan(obv)])

        results['obv'] = obv

        return results, signals_up, signals_down

class AD(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    parameters = []

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        size = len(self.datas)
        high = np.array([float(bar.high_price) for bar in self.datas])
        low = np.array([float(bar.low_price) for bar in self.datas])
        close = np.array([float(bar.close_price) for bar in self.datas])
        volume = np.array([float(bar.volume) for bar in self.datas])
        
        ad = talib.AD(high, low, close, volume)

        ad[np.isnan(ad)] = np.mean(ad[~np.isnan(ad)])

        results['ad'] = ad

        return results, signals_up, signals_down

class ADOSC(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    fast_window = 3
    slow_window = 10
    parameters = ['fast_window', 'slow_window']

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        size = len(self.datas)
        high = np.array([float(bar.high_price) for bar in self.datas])
        low = np.array([float(bar.low_price) for bar in self.datas])
        close = np.array([float(bar.close_price) for bar in self.datas])
        volume = np.array([float(bar.volume) for bar in self.datas])
        
        adosc = talib.ADOSC(high, low, close, volume, self.fast_window, self.slow_window)

        adosc[np.isnan(adosc)] = np.mean(adosc[~np.isnan(adosc)])

        results['adosc'] = adosc

        return results, signals_up, signals_down

class KELTNER(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    fast_window = 12
    slow_window = 26
    dev = 2

    parameters = ['fast_window', 'slow_window', 'dev']

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        size = len(self.datas)
        close = np.array([float(bar.close_price) for bar in self.datas])
        high = np.array([float(bar.high_price) for bar in self.datas])
        low = np.array([float(bar.low_price) for bar in self.datas])

        atr = talib.ATR(high, low, close, self.fast_window)
        mid = talib.SMA(close,self.fast_window)
        sma_slow = talib.SMA(close,self.slow_window)

        up = mid + self.dev* atr
        down = mid -self.dev* atr

        nan2mean(up)
        nan2mean(down)
        nan2mean(mid)
        nan2mean(sma_slow)

        results['up'] = up
        results['down'] = down
        results['mid'] = mid
        results['sma_slow'] = sma_slow

        return results, signals_up, signals_down


class MACD_TICK_COMBO(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    fast_window = 12
    slow_window = 26
    signal_window = 9

    parameters = ['fast_window', 'slow_window','signal_window']

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []

        size = len(self.datas)
        close = np.array([float(bar.last_price) for bar in self.datas])
        macd, signal, hist = talib.MACD(
            close, self.fast_window, self.slow_window, self.signal_window
        )

        macd[np.isnan(macd)] = np.mean(macd[~np.isnan(macd)])
        signal[np.isnan(signal)] = np.mean(signal[~np.isnan(signal)])
        hist[np.isnan(hist)] = np.mean(hist[~np.isnan(hist)])

        # results['close_price'] = close
        results['macd'] = macd
        results['signal'] = signal
        results['hist'] = hist


        return results, signals_up, signals_down


class TICK_COMBO_Boll(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    boll_window = 26
    boll_dev = 2

    parameters = ['boll_window', 'boll_dev']

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []


        size = len(self.datas)
        close = np.array([float(tick.last_price) for tick in self.datas])
        sma = talib.SMA(close, self.boll_window)
        sma[np.isnan(sma)] = np.mean(sma[~np.isnan(sma)])

        smalong = talib.SMA(close, 2*self.boll_window)
        smalong[np.isnan(smalong)] = np.mean(smalong[~np.isnan(smalong)])

        std = talib.STDDEV(close, self.boll_window)
        std[np.isnan(std)] = np.mean(std[~np.isnan(std)])        


        boll_up = []
        boll_down = []
        for i in range(size):
            boll_up.append(sma[i]+self.boll_dev*std[i])
            boll_down.append(sma[i]-self.boll_dev*std[i])
            if smalong[i] > sma[i]+self.boll_dev*std[i]:
                signals_down.append((i,smalong[i]))
            if smalong[i] < sma[i]-self.boll_dev*std[i]:
                signals_up.append((i,smalong[i]))            
        # results['close_price'] = close
        results['sma_short'] = sma
        results['sma_long'] = smalong
        results['boll_up'] = boll_up
        results['boll_down'] = boll_down

        return results, signals_up, signals_down 

class TICK_COMBO_MEANREVERT(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    fast_window = 20
    middle_window = 500
    slow_window = 5000
    dev = 2

    parameters = ['fast_window', 'middle_window', 'slow_window', 'dev']

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []


        size = len(self.datas)
        close = np.array([float(tick.last_price) for tick in self.datas])
        smafast = talib.SMA(close, self.fast_window)
        nan2mean(smafast)

        smaslow = talib.SMA(close, self.slow_window)
        nan2mean(smaslow)

        smamiddle = talib.SMA(close, self.middle_window)
        nan2mean(smamiddle)

        std = talib.STDDEV(close, self.slow_window)
        nan2mean(std)


        boll_up = []
        boll_down = []
        for i in range(size):
            # boll_up.append(smaslow[i]+self.dev*std[i])
            # boll_down.append(smaslow[i]-self.dev*std[i])
            # if (smafast[i] > boll_up[i] and smafast[i] > smamiddle[i] + 3) or smafast[i] > smamiddle[i] +12:
            #     signals_down.append((i,smafast[i]))
            # if (smafast[i] < boll_down[i] and smafast[i] < smamiddle[i] - 3) or smafast[i] < smamiddle[i] -12:
            #     signals_up.append((i,smafast[i]))     
            boll_up.append(smaslow[i]+self.dev*std[i])
            boll_down.append(smaslow[i]-self.dev*std[i])
            spread = max(8, min(15,self.dev*std[i]))
            if  smafast[i] > smaslow[i] +spread:
                signals_down.append((i,smafast[i]))
            if  smafast[i] < smaslow[i] -spread:
                signals_up.append((i,smafast[i]))           
        # results['close_price'] = close
        results['sma_fast'] = smafast
        results['sma_slow'] = smaslow
        results['up'] = boll_up
        results['down'] = boll_down

        return results, signals_up, signals_down 

class TICK_COMBO_MEANBREAK(IndicatorBase):
    """
    Demo indicator for indicator analysis
    """
    fast_window = 20
    slow_window = 200
    dev = 2

    parameters = ['fast_window', 'slow_window', 'dev']

    def calculate(self):
        """
        Calculate indicator using self.datas, where self.datas is a list of TBTBardata.
        Should return dict of list, each list's length should equal to len(self.datas)
        each element of the dict will show in one chart
        note: number of curve should less than 10, other wise color will duplicate
        for example: 
            results = defaultdict(list)
            vols = [bar.volume for bar in self.datas]
            results['vol'] = vols
            return results      
        """
        results = defaultdict(list)
        signals_up = []
        signals_down = []


        size = len(self.datas)
        close = np.array([float(tick.last_price) for tick in self.datas])
        smafast = talib.SMA(close, self.fast_window)
        nan2mean(smafast)

        smaslow = talib.SMA(close, self.slow_window)
        nan2mean(smaslow)

        std = talib.STDDEV(close, self.fast_window)
        nan2mean(std)


        boll_up = []
        boll_down = []
        for i in range(size):
            boll_up.append(smafast[i]+ max(1,self.dev*std[i]))

            boll_down.append(smafast[i]-max(1,self.dev*std[i]))
            if smaslow[i] > boll_up[i]:
                signals_down.append((i,smafast[i]))
            if smaslow[i] < boll_down[i]:
                signals_up.append((i,smafast[i]))            
        # results['close_price'] = close
        results['sma_fast'] = smafast
        results['sma_slow'] = smaslow
        results['up'] = boll_up
        results['down'] = boll_down

        return results, signals_up, signals_down 