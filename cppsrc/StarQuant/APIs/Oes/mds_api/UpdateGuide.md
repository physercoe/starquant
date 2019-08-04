# OES-API Update Guide    {#update_guide}

MDS_0.15.5.4 / 2018-02-22
-----------------------------------

### 1. API更新概要

  1. 服务端兼容0.15.5.1版本API，客户可以选择不升级
  2. fix: 解决在Windows下的兼容性问题
  3. 调整接口 MdsApi_InitAll, 增加一个函数参数 (pUdpTickOrderAddrKey)，以支持分别订阅逐笔成交和逐笔委托的行情组播
  4. 增加接口 MdsApi_GetLastRecvTime、MdsApi_GetLastSendTime，用于获取通道最近接受/发送消息的时间
  5. 登录失败时, 可以通过 errno/SPK_GET_ERRNO() 获取到具体失败原因

### 2. 服务端更新概要

  1. fix: 优化行情推送，改善推送服务的公平性
  2. fix: 修复在计算深圳逐笔成交的成交金额时没有转换为int64，导致溢出的BUG
  3. fix: 修复上海L1指数快照的 securityType 不正确，取值都是 1 的BUG
  4. fix: 修复查询L1快照时，未按照查询条件 securityType 进行匹配的问题
  5. fix: 修复 mds_tester 查询功能无法使用的问题
  6. 支持指定行情组播发送端的端口号
  7. 优化深证行情采集，改善早盘高峰时期行情延迟过大的问题
  8. 优化行情组播的发送延迟
