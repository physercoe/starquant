"""
General utility functions.
"""

import json
from pathlib import Path
from typing import Callable
from decimal import Decimal

import numpy as np
import pandas as pd
import warnings
from numba import jit,float64,int64

from pystarquant.common.constant import Exchange,Product,PRODUCT_SQ2VT

# str related

def extract_full_symbol(full_symbol: str):
    """
    :return: (symbol, exchange)
    """
    tmp = full_symbol.split(' ')
    if len(tmp) < 3:
        return 'unknown', Exchange.SHFE    
    exchange_str = tmp[0]
    try:
        ex = Exchange(exchange_str)
        symbol = ''
        
        #TODO:add spread support, for product class is 'S'

        for i in range(2,len(tmp)):
            symbol += tmp[i]

        if ex in [Exchange.SHFE, Exchange.DCE, Exchange.INE]:
            symbol = symbol.lower()
    except:
        symbol = 'unknown'
        ex = Exchange.SHFE
    return symbol, ex

def extract_symbol_class(full_symbol:str):
    tmp = full_symbol.split(' ')
    if len(tmp) < 3:
        return 'SHFE F UNKNOWN'
    return tmp[0] + ' ' + tmp[1] + ' ' + tmp[2]

def extract_product(full_symbol:str):
    tmp = full_symbol.split(' ')
    if len(tmp) < 3:
        return  Product.EQUITY
    return PRODUCT_SQ2VT[tmp[1]]   

# from ctp symbol to full symbol
def generate_full_symbol(exchange: Exchange, symbol: str, type: str = 'F'):
    product = ''
    contractno = ''
    fullsym = symbol
    if symbol:
        if type == 'F' or type == 'O':
            for count, word in enumerate(symbol):
                if word.isdigit():
                    break
            product = symbol[:count]
            contractno = symbol[count:]
            fullsym = exchange.value + ' ' + type + ' '\
                + product.upper() + ' ' + contractno
        elif type == 'S':
            combo = symbol.split(' ', 1)[1]
            symbol1 = combo.split('&')[0]
            symbol2 = combo.split('&')[1]
            for count, word in enumerate(symbol1):
                if word.isdigit():
                    break
            product = symbol1[:count]
            contractno = symbol1[count:]
            for count, word in enumerate(symbol2):
                if word.isdigit():
                    break
            product += ('&' + symbol2[:count])
            contractno += ('&' + symbol2[count:])
            fullsym = exchange.value + ' ' + type + ' '\
                + product.upper() + ' ' + contractno
        else:
            fullsym = exchange.value + ' ' + type + ' ' + symbol
    return fullsym


def extract_vt_symbol(vt_symbol: str):
    """
    :return: (symbol, exchange)
    """
    symbol, exchange_str = vt_symbol.split('.')
    return symbol, Exchange(exchange_str)


def generate_vt_symbol(symbol: str, exchange: Exchange):
    return f'{symbol}.{exchange.value}'


def _get_trader_dir(temp_name: str):
    """
    Get path where trader is running in.
    """
    cwd = Path.cwd()
    temp_path = cwd.joinpath(temp_name)

    # If .StarQuant folder exists in current working directory,
    # then use it as trader running path.
    if temp_path.exists():
        return cwd, temp_path

    # Otherwise use home path of system.
    home_path = Path.home()
    temp_path = home_path.joinpath(temp_name)

    # Create .StarQuant folder under home path if not exist.
    if not temp_path.exists():
        temp_path.mkdir()

    return home_path, temp_path


TRADER_DIR, TEMP_DIR = _get_trader_dir(".StarQuant")

# path ,file, related
def get_file_path(filename: str):
    """
    Get path for temp file with filename.
    """
    return TEMP_DIR.joinpath(filename)


def get_folder_path(folder_name: str):
    """
    Get path for temp folder with folder name.
    """
    folder_path = TEMP_DIR.joinpath(folder_name)
    if not folder_path.exists():
        folder_path.mkdir()
    return folder_path


def get_icon_path(filepath: str, ico_name: str):
    """
    Get path for icon file with ico name.
    """
    ui_path = Path(filepath).parent
    icon_path = ui_path.joinpath("ico", ico_name)
    return str(icon_path)


def load_json(filename: str):
    """
    Load data from json file in temp path.
    """
    filepath = get_file_path(filename)

    if filepath.exists():
        with open(filepath, mode='r') as f:
            data = json.load(f)
        return data
    else:
        save_json(filename, {})
        return {}


def save_json(filename: str, data: dict):
    """
    Save data into json file in temp path.
    """
    filepath = get_file_path(filename)
    with open(filepath, mode='w+') as f:
        json.dump(data, f, indent=4)

# math related
def round_to_pricetick(price: float, pricetick: float):
    """
    Round price to price tick value.
    """
    rounded = round(price / pricetick, 0) * pricetick
    return rounded


def round_to(value: float, target: float) -> float:
    """
    Round price to price tick value.
    """
    value = Decimal(str(value))
    target = Decimal(str(target))
    rounded = float(int(round(value / target)) * target)
    return rounded


def nan2mean(x):
    x[np.isnan(x)] = np.mean(x[~np.isnan(x)])



def zero_divide(x, y):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = np.divide(x,y)
    if hasattr(y, "__len__"):
        res[y == 0] = 0
    elif y == 0:
        res = 0        
    return res

def vanish_thre(x, thre):
    x[np.abs(x)>thre] = 0
    return x

@jit
def ewm_fast(x,halflife, adjust=False):
    alpha = 1 - np.exp(np.log(0.5)/halflife)
    ewm_arr = np.zeros_like(x)
    ewm_arr[0] = x[0]
    for t in range(1,x.shape[0]):
        ewm_arr[t] = alpha*x[t] + (1 - alpha)*ewm_arr[t-1]

    return ewm_arr  

@jit(nopython=True,nogil=True)
def _ewm(arr_in, halflife, adjust=False):
    alpha = 1 - np.exp(np.log(0.5)/halflife)
    n = arr_in.shape[0]
    ewma = np.empty(n, dtype=float64)
    w = 1
    ewma_old = arr_in[0]
    ewma[0] = ewma_old
    for i in range(1, n):
        w += (1-alpha)**i
        ewma_old = ewma_old*(1-alpha) + arr_in[i]
        ewma[i] = ewma_old / w
    return ewma


def ewma(x, halflife, init=0, adjust=False):
    init_s = pd.Series(data=init)
    if type(x) == np.ndarray:
        s = init_s.append(pd.Series(x))
    else:
        s = init_s.append(x)
    if adjust:
        xx = range(len(x))
        lamb=1 - 0.5**(1 / halflife)
        aa=1-np.power(1-lamb, xx)*(1-lamb)
        bb=s.ewm(halflife=halflife, adjust=False).mean().iloc[1:].values
        # bb = _ewm(s.values,halflife=halflife,adjust=False)[1:]
        return bb/aa
    else:
        return s.ewm(halflife=halflife, adjust=False).mean().iloc[1:].values
        # return _ewm(s.values,halflife=halflife,adjust=False)[1:]



def ewma_lambda(x, lambda_, init=0, adjust=False):
    init_s = pd.Series(data=init)
    s = init_s.append(x)
    if adjust:
        xx = range(len(x))
        aa=1-np.power(1-lambda_, xx)*(1-lambda_)
        bb=s.ewm(alpha=lambda_, adjust=False).mean().iloc[1:]
        return bb/aa
    else:
        return s.ewm(alpha=lambda_, adjust=False).mean()[1:]

def rsi(ret, period):
    abs_move = np.abs(ret)
    up_move = np.maximum(ret, 0)
    up_total = ewma(up_move, period, adjust=True)
    move_total = ewma(abs_move, period, adjust=True)
    rsi = zero_divide(up_total, move_total) - 0.5
    return rsi

def fcum(x, n, fill=0):
    return pd.Series(data=cum(pd.concat((x, pd.Series(np.repeat(fill, n))), ignore_index=True), n).shift(-n)[:-n].values, index=x.index)

def cum(x, n):
    sum_x = x.cumsum()
    sum_x_shift = sum_x.shift(n)
    sum_x_shift[:n]= 0
    return sum_x - sum_x_shift

def get_range_pos(wpr, min_period, max_period, period):
    return ewma(zero_divide(wpr-min_period, max_period-min_period), period, adjust=True) - 0.5


def fast_roll_var(x, period):
      x_ma = cum(x,period)/period
      x2 = x*x
      x2_ma = cum(x2,period)/period
      var_x = x2_ma-x_ma*x_ma
      return(var_x)















def virtual(func: Callable):
    """
    mark a function as "virtual", which means that this function can be override.
    any base class should use this or @abstractmethod to decorate all functions
    that can be (re)implemented by subclasses.
    """
    return func
