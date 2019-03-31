Intro 简介
========
StarQuant(中文名：易数交易系统)是一个轻量的、面向个人用户的开源量化交易、回测系统，代码地址：https://github.com/physercoe/starquant 
易数交易系统具有以下功能：
（1）策略回测
（2）行情订阅和数据存储
（3）实盘程序化交易(支持多个API接口，如ctp,tap(易盛内外盘))
（4）可视化界面，
（5）系统、交易（委托，成交，持仓等）的记录。
系统主框架基于c++实现，行情，交易、数据记录为单独线程，线程通信采用网络套接字方式（nanomsg），行情数据可以通过相关端口以messenge形式转发到策略进程，策略下单操作也通过相关端口将指令转发到交易线程，然后调用相关柜台api，行情api支持CTP，TAP等，数据可以记录到本地（csv文件或Mongodb数据库），策略可以采用python或c++实现。
回测框架是python实现，事件驱动，和vnpy基本一样，策略在回测和交易程序中形式基本一样，只需较少改写代码。
GUI是基于PyQt5，支持手动交易，策略交易，委托持仓账号等信息查看。

开发环境
------------------
本系统在开发过程中参考了已有的开源软件EliteQuant，vnpy,kungfu等。
Manjaro（arch，Linux内核4.14)
boost 1.69
python 3.7.2
gcc 8.2
vscode

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

编写约定
-------------------
参考google 的c++ guide
变量命名：类名采用驼峰式，单词首字母大写，不包含_字符；类成员变量字母一般小写，后加_，如data_,全局变量加g_修饰，函数一般大小写混合形式。



使用说明
-------
品种符号约定：
  采用全名的形式：交易所 类型 商品名 合约，如SHFE F RB 1905
  对于ctp，程序内部api会转换为对应的简写形式，rb1905，
行情、交易、策略之间消息传递的格式：消息头|消息内容
 消息头:目的地|源地址|类型，类型有：
 
 消息内容：对应类型的数据

 
 



当前状态
-----------------
本程序尚在开发过程中，基本功能、GUI等方面有待完善等。
TODO:
1完善订单，持仓统计的记录功能
2增加异常处理和检测
3完善日志系统，使用log4cplus
4增加debug模式，输出重要函数的输入参数，输出参数，中间关键变量，为后续模拟盘测试调试提供帮助。



等正式发布时欢迎测试提出意见～



