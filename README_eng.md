Welcome to StarQuant
==================

<p align="left">
   <img src ="https://img.shields.io/badge/language-c%2B%2B%7Cpython-orange.svg"/>
   <img src ="https://img.shields.io/badge/c%2B%2B-%3E11-blue.svg"/>
    <img src ="https://img.shields.io/badge/python-3.7-blue.svg" />
    <img src ="https://img.shields.io/badge/platform-linux%7Cwindows-brightgreen.svg"/>
    <img src ="https://img.shields.io/badge/build-passing-green.svg" />
    <img src ="https://img.shields.io/badge/license-MIT-blue.svg"/>
</p>

[中文](README.md) 

**StarQuant** is light-weighted, integrated algo-backtest/trade system/platform for individual trader, it is mainly used for future trading at present, stock and other commodity will be included in future.

## Features
* strategy bactested in python, run directly in live；
* marketdata subscribe and record, simulated trading；
* algo-trading in live, support multiple API and accounts, autoconnect/logout/reset, working in 7*24h；
* pyQt5 based GUI interface for monitoring and manual control；
* order , risk manage, log by log4cplus;
* strategy , marketdatafeed, trade run by different processes, communicate by message queue(nanomsg), support cpu affinity;
* realtime message notify through wechat(itchat) ...

## Architecture

C++ 11 based, client-server, event-driven, decoupled module design.




## Development Environment

Manjaro（arch，Linux 4.14)，python 3.7.2，gcc 8.2, anaconda 5.2

**third party softwares:**

* boost 1.69
* nanomsg
* log4cplus
* yamlcpp
* libmongoc-1.0
* ...

**python modules:**

* pandas-datareader
* psutil
* pyyaml
* pyqt
* qdarkstyle
* tushare
* pyfolio
* itchat
* ...


## How to Run


compile files in cppsrc:

```
$ cd cppsur
$ mkdir build
$ cd build
$ cmake ..
$ make
$ cp StarQuant/apiserver.exe ../../
```
start apiserver and gui, strategy, recorder:
```
$ ./apiserver
```
```
$ python gui.py
$ python strategy.py
$ python recorder.py
```


## User Guide

To be continued


## Demo

![ ](demos/live3.png  "trade mode")

![](demos/bt3.png  "backtest mode")

![ ](demos/bt4.png  "backtest results ")


## Current State

Currently StarQuant is under test, v1.0-alpha version has been released.




