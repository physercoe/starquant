Intro 简介
========
StarQuant是一个简易的量化交易、回测系统，代码地址：https://github.com/physercoe/starquant 
本系统基于已有的开源软件EliteQuant，vnpy等开发，主要是完善了原elitequant下的回测、交易功能，去除了一些用不到的内容，采用的gcc为8.2版本，python为3.7版本。
交易主框架基于c++实现，行情，交易、数据记录为单独线程，策略目前是采用python实现（也可以在交易框架中采用c++实现），进程通信采用网络套接字方式，行情数据通过相关端口以messenge形式转发到策略进程，策略下单操作也通过相关端口将指令转发到交易线程，然后调用相关柜台api，行情api支持CTP，TAP(郑商所的易胜内盘)，IB等，数据记录到本地（csv文件或Mongodb数据库）。
回测框架是python实现，事件驱动，和vnpy基本一样，策略在回测和交易程序中形式一样，无需重写代码。
GUI是基于PyQt5，比较简单，支持手动交易，策略交易，委托持仓账号等信息查看。

开发环境
------------------

Manjaro（arch，Linux内核4.14)
boost 1.69
python 3.7.2
gcc 8.2

运行
--------------

首先需要编译完成cppsrc下的库，需要事先安装boost，nanomsg以及CTP,TAP等柜台api的动态链接库。
编译过程和原项目类似，使用 [CMake](https://cmake.org) 进行编译：

```
$ cd cppsur
$ mkdir build
$ cd build
$ cmake ..
$ make
```
编译完成后将cppsrc/build/StarQuant下的libstarquant.so拷贝到lib/下供python调用。
python依赖psutil，pyyaml,pyqt,qdarkstyle,tushare等包。

运行时执行trade.py即可交易，backtest.py为回测执行文件，config_*.yaml为相应的配置文件，运行前请修改。

后续工作
-----------------
本程序尚在开发过程中，风控模块，多账号功能，GUI等方面有待完善等。

欢迎测试提出意见，开发者非cs专业出身，计算机知识很有限，项目也是业余时间完成的，程序适用于对数据延迟不是很敏感的策略，若对延迟比较敏感，请参考其他框架如kungfu。



