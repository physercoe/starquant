#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import defaultdict
import importlib
import traceback
from pathlib import Path
import os
import yaml
from PyQt5 import QtGui
class dotdict(dict):

    """
    dot.notation access to dictionary attributes
    """

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


context = dotdict()


history_bar = defaultdict(list)
history_tick = defaultdict(list)
history_tbtbar = defaultdict(list)

wxcmd = ''



# config info

config_server = None
try:
    path = os.path.abspath(os.path.dirname(__file__))
    config_file = os.path.join(path, '../../etc/config_server.yaml')
    with open(os.path.expanduser(config_file), encoding='utf8') as fd:
        config_server = yaml.load(fd, Loader=yaml.SafeLoader)
except IOError:
    print("config_server.yaml is missing")


lang_dict = None
try:
    path = os.path.abspath(os.path.dirname(__file__))
    config_file = os.path.join(path, '../gui/language/en/live_text.yaml')
    font = QtGui.QFont('Microsoft Sans Serif', 12)
    if config_server['language'] == 'cn':
        config_file = os.path.join(path, '../gui/language/cn/live_text.yaml')
        font = QtGui.QFont(u'微软雅黑', 12)
    with open(os.path.expanduser(config_file), encoding='utf8') as fd:
        lang_dict = yaml.load(fd, Loader=yaml.SafeLoader)
    lang_dict['font'] = font
except IOError:
    print("live_text.yaml is missing")

if config_server['using_remote']:
    try:
        import ray
        ray.init(address=config_server['ray_addr'])
    except Exception as e:
        print(e)




# class module 
class ClassLoader:
    
    def __init__(self,metaclass,dirpath):
        self.metaclass = metaclass
        self.dirpath = dirpath
        self.classes = {}
        self.settings = {}
        self.load_class()

    def load_class(self, reload: bool = False):
        self.classes.clear()
        self.settings.clear()

        path = Path.cwd().joinpath(self.dirpath)
        mpath = self.dirpath + '.'
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                if filename.endswith(".py"):
                    _module_name = mpath.join(
                        ["", filename.replace(".py", "")])
                elif filename.endswith(".pyd"):
                    _module_name = mpath.join(
                        ["", filename.replace(".pyd", "")])
                elif filename.endswith(".so"):                    
                    _module_name = mpath.join(
                        ["", filename.replace(".so", "")])
                else:
                    continue
                self.load_class_from_module(
                        _module_name, reload)


        for class_name, model_class in self.classes.items():
            setting = model_class.get_class_parameters()
            self.settings[class_name] = setting


    def load_class_from_module(self, module_name: str, reload: bool = False):
        """
        Load class from module file.
        """
        try:
            module = importlib.import_module(module_name)
        # if reload delete old attribute
            if reload:
                if module.__file__.endswith('.so') or module.__file__.endswith('.pyd'):
                    pass
                else:
                    for attr in dir(module):
                        if attr not in ('__name__', '__file__'):
                            delattr(module, attr)
                importlib.reload(module)
            for name in dir(module):
                value = getattr(module, name)
                if (isinstance(value, type) and issubclass(value, self.metaclass) and value is not self.metaclass):
                    self.classes[value.__name__] = value
        except:  # noqa
            msg = f"模块文件{module_name}加载失败，触发异常：\n{traceback.format_exc()}"
            self.write_log(msg)

    def write_log(self,msg):
        print(msg)

from pystarquant.strategy.strategy_base import StrategyBase,IndicatorBase,FactorBase,ModelBase

strategyloader = ClassLoader(StrategyBase,'teststrategy')
livestrategyloader = ClassLoader(StrategyBase,'mystrategy')
indicatorloader = ClassLoader(IndicatorBase,'indicator')
factorloader = ClassLoader(FactorBase,'indicator')
modelloader = ClassLoader(ModelBase,'indicator')


# contracts  
from .datastruct import ContractData
DefaultContracts = defaultdict(ContractData)

DefaultContracts['SHFE F RB'] = ContractData(
    full_symbol= "SHFE F RB",
    size=10,
    pricetick= 1,
    rate= 1e-4,
    isratio= True,
    close_rate= 1e-4
)
DefaultContracts['SHFE F HC'] = ContractData(
    full_symbol= "SHFE F HC",
    size=10,
    pricetick= 1,
    rate= 1.05e-4,
    isratio= True,
    close_rate= 1.05e-4
)
DefaultContracts['SHFE F NI'] = ContractData(
    full_symbol= "SHFE F NI",
    size=1,
    pricetick= 10,
    rate= 6.1,
    isratio= False,
    close_rate= 6.1
)
DefaultContracts['SHFE F ZN'] = ContractData(
    full_symbol= "SHFE F ZN",
    size=5,
    pricetick= 5,
    rate= 0.62,
    isratio= False,
    close_rate= 0
)
DefaultContracts['SHFE F CU'] = ContractData(
    full_symbol= "SHFE F CU",
    size=5,
    pricetick= 10,
    rate= 0.55e-4,
    isratio= True,
    close_rate= 0
)
DefaultContracts['SHFE F AG'] = ContractData(
    full_symbol= "SHFE F AG",
    size=15,
    pricetick= 1,
    rate= 0.55e-4,
    isratio= True,
    close_rate= 0.55e-4
)
DefaultContracts['SHFE F BU'] = ContractData(
    full_symbol= "SHFE F BU",
    size=10,
    pricetick= 2,
    rate= 1.05e-4,
    isratio= True,
    close_rate= 1.05e-4
)
DefaultContracts['SHFE F RU'] = ContractData(
    full_symbol= "SHFE F RU",
    size=10,
    pricetick= 5,
    rate= 0.5e-4,
    isratio= True,
    close_rate= 0.5e-4
)
DefaultContracts['DCE F I'] = ContractData(
    full_symbol= "DCE F I",
    size=100,
    pricetick= 0.5,
    rate= 0.65e-4,
    isratio= True,
    close_rate= 0.65e-4
)
DefaultContracts['DCE F J'] = ContractData(
    full_symbol= "DCE F J",
    size=100,
    pricetick= 0.5,
    rate= 0.65e-4,
    isratio= True,
    close_rate= 0.65e-4
)
DefaultContracts['DCE F JM'] = ContractData(
    full_symbol= "DCE F JM",
    size=100,
    pricetick= 0.5,
    rate= 0.65e-4,
    isratio= True,
    close_rate= 0.65e-4
)
DefaultContracts['DCE F JD'] = ContractData(
    full_symbol= "DCE F JD",
    size=10,
    pricetick= 1,
    rate= 1.55e-4,
    isratio= True,
    close_rate= 1.55e-4
)
DefaultContracts['DCE F M'] = ContractData(
    full_symbol= "DCE F M",
    size=10,
    pricetick= 1,
    rate= 0.16,
    isratio= False,
    close_rate= 0.085
)
DefaultContracts['DCE F A'] = ContractData(
    full_symbol= "DCE F A",
    size=10,
    pricetick= 1,
    rate= 0.21,
    isratio= False,
    close_rate= 0.21
)
DefaultContracts['DCE F Y'] = ContractData(
    full_symbol= "DCE F Y",
    size=10,
    pricetick= 2,
    rate= 0.26,
    isratio= False,
    close_rate= 0.135
)
DefaultContracts['DCE F P'] = ContractData(
    full_symbol= "DCE F P",
    size=10,
    pricetick= 2,
    rate= 0.26,
    isratio= False,
    close_rate= 0.135
)

DefaultContracts['CZCE F MA'] = ContractData(
    full_symbol= "CZCE F MA",
    size=10,
    pricetick= 1,
    rate= 0.21,
    isratio= False,
    close_rate= 0.21
)
DefaultContracts['CZCE F TA'] = ContractData(
    full_symbol= "CZCE F TA",
    size=5,
    pricetick= 2,
    rate= 0.62,
    isratio= False,
    close_rate= 0
)

DefaultContracts['CZCE F CF'] = ContractData(
    full_symbol= "CZCE F CF",
    size=5,
    pricetick= 5,
    rate= 0.88,
    isratio= False,
    close_rate= 0
)
DefaultContracts['CZCE F SR'] = ContractData(
    full_symbol= "CZCE F SR",
    size=10,
    pricetick= 1,
    rate= 0.31,
    isratio= False,
    close_rate= 0
)
DefaultContracts['CZCE F FG'] = ContractData(
    full_symbol= "CZCE F FG",
    size=20,
    pricetick= 1,
    rate= 0.155,
    isratio= False,
    close_rate= 0.155
)

DefaultContracts['CZCE F RM'] = ContractData(
    full_symbol= "CZCE F RM",
    size=10,
    pricetick= 1,
    rate= 0.16,
    isratio= False,
    close_rate= 0.16
)
DefaultContracts['CFFEX F IF'] = ContractData(
    full_symbol= "CFFEX F IF",
    size=300,
    pricetick= 0.2,
    rate= 0.25e-4,
    isratio= True,
    close_rate= 0.25e-4
)
DefaultContracts['INE F SC'] = ContractData(
    full_symbol= "INE F SC",
    size=1000,
    pricetick= 0.1,
    rate= 0.21e-2,
    isratio= False,
    close_rate= 0.21e-2
)