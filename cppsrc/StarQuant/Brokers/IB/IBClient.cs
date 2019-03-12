/****************************** Project Header ******************************\
Project:	      QuantTrading
Author:			  Letian_zj @ Codeplex
URL:			  https://quanttrading.codeplex.com/
Copyright 2014 Letian_zj

This file is part of QuantTrading Project.

QuantTrading is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, 
either version 3 of the License, or (at your option) any later version.

QuantTrading is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with QuantTrading. 
If not, see http://www.gnu.org/licenses/.

\***************************************************************************/
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

using System.Threading;
using System.Globalization;
using System.Diagnostics;
using IBApi;

namespace TradingBase
{
    public class IBClient : EWrapper, IClient
    {
        public IBClient() : this("127.0.0.1", 7496, 0) { }

        public IBClient(string host, int port, int clientId = 0)
        {
            Host = host;
            Port = port;
            ClientId = clientId;

            _marketDataRequests = new List<Tick>();
            _marketDepthRequests = new List<string>();
            _historicalBarRequests = new List<BarRequest>();
            _symbolToPosition = new Dictionary<string, Position>();
            _iborderIdToOrderInfo = new Dictionary<int, OrderInfo>();
            _duplicateIBIdToDeferredTrade = new List<KeyValuePair<int, Trade>>();

            _nextValidIBID = 1;
            _ibSocket = new EClientSocket(this);
        }

        // Properties
        private EClientSocket _ibSocket;
        public  long ServerTime { get; private set; }
        public  string Account { get; private set; }

        public long NextValidOrderId { get { return _nextValidIBID; } }

        public string Host { get; set; }
        public int Port { get; set; }
        public int ClientId { get; set; }
        public bool RequestPositionsOnStartup { get; set; }
        public int ServerVersion { get; private set; }            // IB Server Version
        public bool isServerConnected
        {
            get { return _ibSocket.IsConnected(); }
        }


        // Methods
        // It requests accounts, and poisitions associated to that account
        public void Connect()       // replace Mode()
        {
            _ibSocket.eConnect(Host, Port, ClientId);
            _ibSocket.setServerLogLevel(5);         // detail

            if (ClientId == 0)
            {
                // associate TWS with the client
                _ibSocket.reqAutoOpenOrders(true);
            }

            ServerVersion = _ibSocket.ServerVersion;
            OnGotServerInitialized("ServerVersion:" + ServerVersion);
            //trigger updatePortfolio()
            _ibSocket.reqAccountUpdates(true, null);
        }

        public void Disconnect()            // replace Disconnect(), stop()
        {
            try
            {
                // cancel market data
                CancelMarketData();

                //_ibSocket.eDisconnect();
                _ibSocket.Close();
            }
            catch (Exception e)
            {
                // Relegate
                OnDebug(e.Message);
            }
        }

        public void Start() { }               // replace start and reset

        //********************************* Member Variables *************************************//
        // PositionRequest
        // AccountRequest
        #region member variables
        public event Action<Tick> GotTickDelegate;
        public event Action<Trade> GotFillDelegate;
        public event Action<Order> GotOrderDelegate;
        public event Action<long> GotOrderCancelDelegate;
        public event Action<Position> GotPositionDelegate;
        public event Action<Bar> GotHistoricalBarDelegate;
        public event Action<string> GotServerInitializedDelegate;
        public event Action<string> SendDebugEventDelegate;

        //public event Action<string> GotServerUpDelegate;
        //public event Action<string> GotServerDownDelegate;
        //public event Action<string> GotAccountsDelegate;

        // private memberdata
        // for market data and market depth request
        private List<Tick> _marketDataRequests;     // List<T> holds copy of value type struct.
        private List<string> _marketDepthRequests;      // Symbol full name in _marketDataRequests
        // for historical bar request
        private List<BarRequest> _historicalBarRequests;
        // for position
        private Dictionary<string, Position> _symbolToPosition;
        // map from IB ID to order ID and OrderInfo
        private int _nextValidIBID;
        private Dictionary<int, OrderInfo> _iborderIdToOrderInfo;
        // for order fill; it may contains more than one partially filled ordered.
        private List<KeyValuePair<int, Trade>> _duplicateIBIdToDeferredTrade;
        #endregion

        //********************************* Outgoing Messages *************************************//
        #region Outgoing Messages
        /// <summary>
        /// Request market data for a basket of securities according to their FullNames
        /// </summary>
        /// <param name="b"></param>
        public void RequestMarketData(Basket b)
        {
            // Connection is verified in _ibSocket.reqMktData
            for (int i = 0; i < b.Count; i++)
            {
                Contract contract;
                contract = SecurityFullNameToContract(b[i]);

                bool exist = false;
                foreach (var t in _marketDataRequests)
                {
                    if (t.FullSymbol == b[i])
                        exist = true;
                }
                if (exist)
                    continue;
                else
                {
                    Tick tick = new Tick();
                    // tick symbol is security full name
                    tick.FullSymbol = b[i];
                    _marketDataRequests.Add(tick);
                    _ibSocket.reqMktData(_marketDataRequests.Count - 1, contract, null, false);
                }
            }
        }

        // Unsubscribe
        public void CancelMarketData(int tickerId)
        {
            _ibSocket.cancelMktData(tickerId);
        }

        // Unsubscribe all
        public void CancelMarketData()
        {
            for (int i = 0; i < _marketDataRequests.Count; i++)
            {
                _ibSocket.cancelMktData(i);
            }
            for (int i = 0; i < _marketDepthRequests.Count; i++)
            {
                _ibSocket.cancelMktDepth(i);
            }
        }

        /// <summary>
        /// Request market depth for contracts with market data
        /// DOM
        /// </summary>
        public void RequestMarketDepth(int depth)
        {
            // for every market data request
            int i;
            for (i = 0; i < _marketDataRequests.Count; i++)
            {
                bool exist = false;
                foreach (string sym in _marketDepthRequests)
                {
                    if (sym == _marketDataRequests[i].FullSymbol)
                        exist = true;
                }
                if (exist)
                    continue;
                else
                {
                    Contract contract = SecurityFullNameToContract(_marketDataRequests[i].FullSymbol);
                    _marketDepthRequests.Add(_marketDataRequests[i].FullSymbol);
                    // reqId as sequence in _marketDataRequests
                    _ibSocket.reqMarketDepth(i, contract, depth);
                }
            }
        }

        public void CancelMarketDepth(int tickerId)
        {
            _ibSocket.cancelMktDepth(tickerId);
        }

        /// <summary>
        /// request historical bar
        /// </summary>
        /// <param name="barsize"> less than 1 day, in seconds </param>
        public void RequestHistoricalData(BarRequest br, bool useRTH = false)
        //Security sec, DateTime starttime, DateTime endtime, int barsize)
        {
            Contract contract = SecurityFullNameToContract(br.FullSymbol);
            if (contract.SecType == "STK")
                contract.IncludeExpired = false;
            else
                contract.IncludeExpired = true;

            int useReguarTradingHour = useRTH ? 1 : 0;
            string barSize;
            switch (br.Interval)
            {
                case 1:
                    barSize = "1 secs";             // not 1 sec
                    break;
                case 5:
                    barSize = "5 secs";
                    break;
                case 15:
                    barSize = "15 secs";
                    break;
                case 30:
                    barSize = "30 secs";
                    break;
                case 60:
                    barSize = "1 min";
                    break;
                case 120:
                    barSize = "2 mins";
                    break;
                case 180:
                    barSize = "3 mins";
                    break;
                case 300:
                    barSize = "5 mins";
                    break;
                case 900:
                    barSize = "15 mins";
                    break;
                case 1800:
                    barSize = "30 mins";
                    break;
                case 3600:
                    barSize = "1 hour";
                    break;
                case 86400:
                    barSize = "1 day";
                    break;
                default:
                    throw new ArgumentOutOfRangeException("Invalid barsize/interval.");
            }

            DateTime startdatetime = br.StartDateTime;
            DateTime enddatetime = br.EndDateTime;
            //yyyymmdd hh:mm:ss tmz
            String enddatetimestring = enddatetime.ToString("yyyyMMdd HH:mm:ss", CultureInfo.InvariantCulture) + " EST";
            TimeSpan duration = enddatetime - startdatetime;
            string durationstring;
            // Request is less than one day --> request in seconds
            if (startdatetime > enddatetime.AddDays(-1))
            {
                durationstring = duration.TotalSeconds.ToString() + " S";
            }
            // Request is greater than 1 day and less than 7 days -> Request in days
            else if (startdatetime > enddatetime.AddDays(-7))
            {
                durationstring = duration.TotalDays.ToString() + " D";
            }
            // Request is greater than 7 days and less than 1 month -> Request in weeks
            else if (startdatetime > enddatetime.AddMonths(-1))
            {
                int numberOfWeeksToRequest = (int)Math.Ceiling(duration.TotalDays / 7.0);
                durationstring = numberOfWeeksToRequest.ToString() + " W";
            }
            else
            {
                throw new ArgumentOutOfRangeException("Period cannot be bigger than 52 weeks.");
            }

            _historicalBarRequests.Add(br);

            _ibSocket.reqHistoricalData(_historicalBarRequests.Count - 1, contract, enddatetimestring, durationstring,
                barSize, "TRADES", useReguarTradingHour, 1);
        }

        /// <summary>
        /// Place order. 
        /// Order must have contract field.
        /// </summary>
        public void PlaceOrder(Order o)
        {
            if ((!o.IsValid) || (string.IsNullOrEmpty(o.FullSymbol)))
            {
                OnDebug("Order is not valid.");
                return;
            }

            IBApi.Order order = new IBApi.Order();

            order.AuxPrice = o.IsTrail ? (double)o.TrailPrice : (double)o.StopPrice;
            order.LmtPrice = (double)o.LimitPrice;

            // Only MKT, LMT, STP, and STP LMT, TRAIL, TRAIL LIMIT are supported
            order.OrderType = o.OrderType;

            order.TotalQuantity = o.UnsignedSize;
            order.Action = o.OrderSide ? "BUY" : "SELL";         // SSHORT not supported here

            // order.Account = Account;
            order.Tif = o.TIF.ToString();
            order.OutsideRth = true;
            //order.OrderId = (int)o.id;
            order.Transmit = true;
            if (string.IsNullOrEmpty(o.Account))
                order.Account = Account;
            else
                order.Account = o.Account;

            // Set up IB order Id
            if (o.Id == 0)
            {
                throw new ArgumentOutOfRangeException("Order id is missing.");
            }
            else // TODO: elimitate situation where strategy Order Id already exists
            {
                //order.OrderId = System.Threading.Interlocked.Increment(ref _nextValidIBID); // it returns the incremented id
                order.OrderId = (int)o.Id;
                _iborderIdToOrderInfo.Add(order.OrderId, new OrderInfo(o.Id, order.Account, false));
            }


            IBApi.Contract contract = SecurityFullNameToContract(o.FullSymbol);

            _ibSocket.placeOrder(order.OrderId, contract, order);
        }

        public void CancelOrder(long strategyOrderId)
        {
            bool cancel = false;
            int ibid = -1;
            foreach (KeyValuePair<int, OrderInfo> item in _iborderIdToOrderInfo)
            {
                if (item.Value.StrategyOrderId == strategyOrderId)      // found the order
                {
                    ibid = item.Key;
                    cancel = true;
                    break;
                }
            }
            if (cancel)         // found
                _ibSocket.cancelOrder(ibid);
            else
                OnDebug("The cancel order is not found. strategy id = " + strategyOrderId);
        }

        // Replace Heartbeat
        public void RequestServerTime()
        {
            _ibSocket.reqCurrentTime();
        }
        #endregion


        //********************************* Incoming Messages *************************************//
        #region Incoming Messages
        public virtual void error(Exception e)
        {
            OnDebug(e.Message);
        }

        public virtual void error(string str)
        {
            OnDebug(str);
        }

        /**
         * @brief Errors sent by the TWS are received here.
         * @param id the request identifier which generated the error.
         * @param errorCode the code identifying the error.
         * http://www.interactivebrokers.com/php/apiguide/interoperability/socket_client_c++/errors.htm
         * @param errorMsg error's description.
         *  
         */
        public virtual void error(int id, int errorCode, string errorMsg)
        {
            // Order cancel can also be captured in OrderStatus()
            if (errorCode == 202)           // Order Cancelled
            {
                try
                {
                    OnGotOrderCancel(_iborderIdToOrderInfo[id].StrategyOrderId);
                }
                catch
                {
                    OnDebug("A non-exist order to be cancelled.");
                }
            }
            else
            {
                string str = "requestId = " + id
                    + "; Error code = " + errorCode
                    + "; Error Message = " + errorMsg;
                OnDebug(str);
            }
        }

        // @sa eConnect, EClientSocket::reqIds
        // feed in upon connection
        public void nextValidId(int orderId)
        {
            _nextValidIBID = orderId;
            OnGotServerInitialized("NextValidOrderId:"+_nextValidIBID);
        }

        // triggered by eConnect, reqCurrentTime
        public virtual void currentTime(long time)
        {
            ServerTime = time;
            OnGotServerInitialized("ServerTime:"+ServerTime);
        }

        // triggered by EClientSocket::reqManagedAccts
        // feed in upon connection
        public virtual void managedAccounts(string accountsList)
        {
            Account = accountsList;
            OnGotServerInitialized("Account:"+Account);
        }

        // triggered by reqAccountUpdate(true, null) called in Start()
        public virtual void updatePortfolio(Contract contract, int position, double marketPrice, double marketValue,
           double averageCost, double unrealisedPNL, double realisedPNL, string accountName)
        {
            Position pos = new Position();
            pos.FullSymbol = ContractToSecurityFullName(contract);

            pos.Size = position;
            
            // STK averageCost is its unit price
            // FUT averageCost is its unit price * multiplier
            int multiplier = Security.GetMultiplierFromFullSymbol(pos.FullSymbol);
            //pos.AvgPrice = pos.FullSymbol.Contains("STK") ? (decimal)averageCost : 
            //    ((position == 0) ? (decimal)averageCost : (decimal)(averageCost/position/multiplier));
            pos.AvgPrice = (decimal)(averageCost / multiplier);
            pos.ClosedPL = (decimal)realisedPNL;
            pos.OpenPL = (decimal)unrealisedPNL;
            pos.Account = Account;

            // If exists, don't trigger gotPosition
            if (_symbolToPosition.ContainsKey(pos.FullSymbol))
            {
                _symbolToPosition[pos.FullSymbol] = pos;
            }
            else
            {
                _symbolToPosition.Add(pos.FullSymbol, pos);
                OnGotPosition(pos);
            }
        }

        // Provides the executions which happened in the last 24 hours.
        // This event is fired when the reqExecutions() functions is invoked, or when an order is filled.
        public virtual void execDetails(int reqId, Contract contract, Execution execution)
        {
            Trade trade = new Trade();
            //trade.Currency = contract.Currency;
            trade.Account = Account;
            trade.Id = 0;

            trade.TradePrice = (decimal)execution.Price;
            trade.TradeSize = (execution.Side == "BOT"?1:-1)*execution.Shares;
            
            // FullSymbol includes SecurityType, Exchange and Multiplier
            // trade.Security = (SecurityType)EnumDescConverter.GetEnumValue(typeof(SecurityType), contract.SecType);
            trade.FullSymbol = ContractToSecurityFullName(contract);

            // convert date and time
            DateTime dt = DateTime.ParseExact(execution.Time, "yyyyMMdd  HH:mm:ss", CultureInfo.InvariantCulture);       // Two blanks
            trade.TradeDate = dt.Year * 10000 + dt.Month * 100 + dt.Day;
            trade.TradeTime = dt.Hour * 10000 + dt.Minute * 100 + dt.Second;

            if (contract.SecType != "BAG")
            {
                if (_iborderIdToOrderInfo.ContainsKey(execution.OrderId))
                {
                    trade.Id = _iborderIdToOrderInfo[execution.OrderId].StrategyOrderId;
                    if (_iborderIdToOrderInfo[execution.OrderId].IsAcknowledged)
                    {
                        OnGotFill(trade);
                        return;
                    }
                }
                // order not found or not acknowledged yet - defer fill notification
                _duplicateIBIdToDeferredTrade.Add(new KeyValuePair<int, Trade>(execution.OrderId, trade));
            }
        }

        // orderStatus, openOrderEnd, EClientSocket::placeOrder, EClientSocket::reqAllOpenOrders, EClientSocket::reqAutoOpenOrders
        public virtual void openOrder(int orderId, Contract contract, IBApi.Order order, OrderState orderState)
        {
            // log warning
            if (!String.IsNullOrEmpty(orderState.WarningText))
                OnDebug(orderState.WarningText);
            if (orderState.Status != "Submitted" && orderState.Status != "Filled" && orderState.Status != "PreSubmitted")
            {
                // igore other states
                return;
            }

            Order o = new Order();
            o.OrderStatus = (OrderStatus)EnumDescConverter.GetEnumValue(typeof(OrderStatus), orderState.Status);
            if (_iborderIdToOrderInfo.ContainsKey(orderId))
            {
                if (_iborderIdToOrderInfo[orderId].IsAcknowledged)
                    return;         // already acknowledged

                _iborderIdToOrderInfo[orderId].IsAcknowledged = true;
                // update account as it might not have been set explicitly
                // account is used for cancelling order
                _iborderIdToOrderInfo[orderId].Account = order.Account;
            }
            else    // the order was placed directly in Tws
            {
                long soId = (long)orderId;
                _iborderIdToOrderInfo.Add(orderId, new OrderInfo(soId, order.Account, true));
                OnDebug("Got order not from strategy. Id = " + orderId + ", " + "symbol = " + contract.Symbol);
            }

            o.Id = _iborderIdToOrderInfo[orderId].StrategyOrderId;                 // strategy Order Id
            o.Account = order.Account;

            o.OrderSize = Math.Abs(order.TotalQuantity) * ((order.Action == "BUY") ? 1 : -1);

            // Order full symbol includes localsymbol, exchange, multiplier, sectype
            // o.LocalSymbol = contract.LocalSymbol;
            // o.Exchange = contract.Exchange;
            // o.Security = (SecurityType)EnumDescConverter.GetEnumValue(typeof(SecurityType), contract.SecType);
            o.FullSymbol = ContractToSecurityFullName(contract);

            o.TrailPrice = ((order.OrderType == "TRAIL") || (order.OrderType == "TRAIL LIMIT")) ? (decimal)order.AuxPrice : 0m;
            o.StopPrice = ((order.OrderType == "STP") || (order.OrderType == "STP LMT")) ? (decimal)order.AuxPrice : 0m;
            o.LimitPrice = ((order.OrderType == "LMT") || (order.OrderType == "TRAIL LIMIT") || (order.OrderType == "STP LMT")) ? (decimal)order.LmtPrice : 0m;

            o.Currency = contract.Currency;
            // o.Currency = (CurrencyType)EnumDescConverter.GetEnumValue(typeof(CurrencyType), contract.Currency);

            // o.TIF = order.Tif;           // Todo: add Tif

            o.OrderDate = Util.ToIntDate(DateTime.Now);
            o.OrderTime = Util.ToIntTime(DateTime.Now);

            if (contract.SecType != "BAG")
            {
                OnGotOrder(o);

                // send deferred fills if any
                // iterate backwards for possible removal
                for (int i = _duplicateIBIdToDeferredTrade.Count - 1; i > -1; i--)
                {
                    if (_duplicateIBIdToDeferredTrade[i].Key == orderId)
                    {
                        Trade trade = _duplicateIBIdToDeferredTrade[i].Value;
                        trade.Id = o.Id;                // strategy id
                        _duplicateIBIdToDeferredTrade.RemoveAt(i);
                        OnGotFill(trade);
                    }
                }
            }
        }

        public virtual void tickPrice(int tickerId, int field, double price, int canAutoExecute)
        {
            if (tickerId < 0 || tickerId > _marketDataRequests.Count)
            {
                OnDebug("can't match market data ticker.");
                return;
            }
            Tick k = new Tick();
            DateTime ct = DateTime.Now;
            k.Date = ct.Year * 10000 + ct.Month * 100 + ct.Day;
            k.Time = ct.Hour * 10000 + ct.Minute * 100 + ct.Second;
            k.FullSymbol = _marketDataRequests[tickerId].FullSymbol;

            if (field == (int)TickType.LastPrice)
            {
                _marketDataRequests[tickerId].TradePrice = (decimal)price;
                k.TradePrice = (decimal)price;
                k.TradeSize = _marketDataRequests[tickerId].TradeSize;
            }
            else if (field == (int)TickType.BidPrice)
            {
                _marketDataRequests[tickerId].BidPrice = (decimal)price;
                k.BidPrice = (decimal)price;
                k.BidSize = _marketDataRequests[tickerId].BidSize;
            }
            else if (field == (int)TickType.AskPrice)
            {
                _marketDataRequests[tickerId].AskPrice = (decimal)price;
                k.AskPrice = (decimal)price;
                k.AskSize = _marketDataRequests[tickerId].AskSize;
            }
            else
            {
                return;
            }
            if (k.IsValid)
            {
                OnGotTick(k);
            }
        }

        public virtual void tickSize(int tickerId, int field, int size)
        {
            if (tickerId < 0 || tickerId > _marketDataRequests.Count)
            {
                OnDebug("can't match market data ticker.");
                return;
            }
            Tick k = new Tick();
            DateTime ct = DateTime.Now;
            k.Date = ct.Year * 10000 + ct.Month * 100 + ct.Day;
            k.Time = ct.Hour * 10000 + ct.Minute * 100 + ct.Second;
            k.FullSymbol = _marketDataRequests[tickerId].FullSymbol;

            // this will be removed
            Security sec = Security.Deserialize(k.FullSymbol);
            bool hundrednorm = (sec.SecurityType == "STK") || (sec.SecurityType == "NIL");

            if (field == (int)TickType.LastSize)
            {
                _marketDataRequests[tickerId].TradeSize = size;     // not adjusted by hundreds
                k.TradeSize = _marketDataRequests[tickerId].TradeSize;
                k.TradePrice = _marketDataRequests[tickerId].TradePrice;
            }
            else if (field == (int)TickType.BidSize)
            {
                _marketDataRequests[tickerId].BidSize = size;
                k.BidPrice = _marketDataRequests[tickerId].BidPrice;
                k.BidSize = _marketDataRequests[tickerId].BidSize;
            }
            else if (field == (int)TickType.AskSize)
            {
                _marketDataRequests[tickerId].AskSize = size;
                k.AskSize = _marketDataRequests[tickerId].AskSize;
                k.AskPrice = _marketDataRequests[tickerId].AskPrice;
            }
            else
            {
                return;
            }
            if (k.IsValid)
            {
                OnGotTick(k);
            }
        }

        // Returns the order book
        public virtual void updateMktDepth(int tickerId, int position, int operation, int side, double price, int size)
        {
            if (tickerId < 0 || tickerId > _marketDataRequests.Count)
            {
                OnDebug("can't match market data ticker.");
                return;
            }
            Tick k = new Tick();
            DateTime ct = DateTime.Now;
            k.Date = ct.Year * 10000 + ct.Month * 100 + ct.Day;
            k.Time = ct.Hour * 10000 + ct.Minute * 100 + ct.Second;
            k.FullSymbol = _marketDataRequests[tickerId].FullSymbol;

            if (side == 1)          // side 0 for ask, 1 for bid
            {
                // why L1 bid price is updated with L2?
                //_marketDataRequests[tickerId].bid = (decimal)price;
                k.BidPrice = (decimal)price;
                k.BidSize = size;
            }
            if (side == 0)          // side 0 for ask, 1 for bid
            {
                //_marketDataRequests[tickerId].ask = (decimal)price;
                k.AskPrice = (decimal)price;
                k.AskSize = size;
            }
            else
            {
                return;
            }
            k.Depth = position;

            if (k.IsValid)
            {
                OnGotTick(k);
            }

        }

        public virtual void updateMktDepthL2(int tickerId, int position, string marketMaker, int operation, int side, double price, int size)
        {
            if (tickerId < 0 || tickerId > _marketDataRequests.Count)
            {
                OnDebug("can't match market data ticker.");
                return;
            }
            Tick k = new Tick();
            DateTime ct = DateTime.Now;
            k.Date = ct.Year * 10000 + ct.Month * 100 + ct.Day;
            k.Time = ct.Hour * 10000 + ct.Minute * 100 + ct.Second;
            k.FullSymbol = _marketDataRequests[tickerId].FullSymbol;

            if (side == 1)                // side 0 for ask, 1 for bid
            {
                // why L1 bid price is updated with L2?
                //_marketDataRequests[tickerId].bid = (decimal)price;
                k.BidPrice = (decimal)price;
                k.BidSize = size;
            }
            if (side == 0)               // side 0 for ask, 1 for bid
            {
                //_marketDataRequests[tickerId].ask = (decimal)price;
                k.AskPrice = (decimal)price;
                k.AskSize = size;
            }
            else
            {
                return;
            }
            k.Depth= position;

            if (k.IsValid)
            {
                OnGotTick(k);
            }
        }

        public virtual void historicalData(int reqId, string date, double open, double high, double low, double close, int volume, int count, double WAP, bool hasGaps)
        {
            if (reqId < 0 || reqId > _historicalBarRequests.Count)
            {
                OnDebug("historical data request doesn't match");
                return;
            }
            // yyyyMMdd{space}{space}HH:mm:ss
            DateTime dt;
            if (!DateTime.TryParseExact(date, "yyyyMMdd  HH:mm:ss", CultureInfo.InvariantCulture, DateTimeStyles.None, out dt))
            {
                // only 1s and 1d are supported at this time. so it must be 1d
                dt = DateTime.ParseExact(date, "yyyyMMdd", CultureInfo.InvariantCulture);
            }

            int ndate = dt.Year * 10000 + dt.Month * 100 + dt.Day;
            int ntime = dt.Hour * 10000 + dt.Minute * 100 + dt.Second;

            Bar bar = new Bar((decimal)open, (decimal)high, (decimal)low, (decimal)close,
                    volume, ndate, ntime,
                    _historicalBarRequests[reqId].FullSymbol, _historicalBarRequests[reqId].Interval);
            bar.TradesInBar = count;
            // bar.WAP = (decimal)average;

            if (bar.IsValid)
            {
                OnGotHistoricalBar(bar);
            }
        }

        public virtual void tickString(int tickerId, int field, string value) { }
        public virtual void tickGeneric(int tickerId, int field, double value) { }
        public virtual void tickEFP(int tickerId, int tickType, double basisPoints, string formattedBasisPoints, double impliedFuture, int holdDays, string futureExpiry, double dividendImpact, double dividendsToExpiry) { }
        public virtual void deltaNeutralValidation(int reqId, UnderComp underComp) { }
        public virtual void tickOptionComputation(int tickerId, int field, double impliedVolatility, double delta, double optPrice, double pvDividend, double gamma, double vega, double theta, double undPrice) { }
        public virtual void tickSnapshotEnd(int tickerId) { }
        public virtual void connectionClosed() { }
        public virtual void accountSummary(int reqId, string account, string tag, string value, string currency) { }
        public virtual void accountSummaryEnd(int reqId) { }
        public virtual void updateAccountValue(string key, string value, string currency, string accountName) { }
        public virtual void updateAccountTime(string timestamp) { }
        public virtual void accountDownloadEnd(string account) { }
        // https://www.interactivebrokers.com/en/software/tws/usersguidebook/realtimeactivitymonitoring/order_status_colors.htm
        public virtual void orderStatus(int orderId, string status, int filled, int remaining, double avgFillPrice,
            int permId, int parentId, double lastFillPrice, int clientId, string whyHeld) { }
        public virtual void openOrderEnd() { }
        public virtual void contractDetails(int reqId, ContractDetails contractDetails) { }
        public virtual void contractDetailsEnd(int reqId) { }
        public virtual void execDetailsEnd(int reqId) { }
        public virtual void commissionReport(CommissionReport commissionReport) { }
        public virtual void fundamentalData(int reqId, string data) { }
        public virtual void historicalDataEnd(int reqId, string start, string end) { }
        public virtual void marketDataType(int reqId, int marketDataType) { }
        public virtual void updateNewsBulletin(int msgId, int msgType, String message, String origExchange) { }
        public virtual void position(string account, Contract contract, int pos, double avgCost) { }
        public virtual void positionEnd() { }
        public virtual void realtimeBar(int reqId, long time, double open, double high, double low, double close, long volume, double WAP, int count) { }
        public virtual void scannerParameters(string xml) { }
        public virtual void scannerData(int reqId, int rank, ContractDetails contractDetails, string distance, string benchmark, string projection, string legsStr) { }
        public virtual void scannerDataEnd(int reqId) { }
        public virtual void receiveFA(int faDataType, string faXmlData) { }

        public virtual void bondContractDetails(int reqId, ContractDetails contract) { }
        #endregion

        //********************************* Auxiliary Functions *************************************//
        #region Auxiliary Functions
        /// <summary>
        /// Deserialize SecurityImpl to Contract
        /// </summary>
        /// <param name="symbol">
        /// STK: LocalSymbol SMART
        /// OPT/FOP: Symbol Expiry C/P Strike Exchange Type
        /// Other; LocalSymbol Exchange Type
        /// </param>
        /// <returns></returns>
        private Contract SecurityFullNameToContract(string symbol)
        {
            Security sec = (Security)Security.Deserialize(symbol);
            Contract contract = new Contract();

            if (sec.IsCall || sec.IsPut)
            {
                contract.Expiry = sec.Expiry.ToString();
                contract.Strike = (double)sec.Strike;
                contract.Right = sec.IsCall ? "C" : "P";
                contract.Symbol = sec.Symbol;
            }
            else
            {
                contract.LocalSymbol = sec.Symbol;
            }

            if (sec.HasDest)
            {
                contract.Exchange = sec.Exchange;
                //contract.PrimaryExch = sec.DestEx;
            }
            else
                contract.Exchange = "SMART";
            if (sec.HasSecType)
                contract.SecType = sec.SecurityType;
            else
                contract.SecType = "STK";

            contract.Currency = "USD";

            return contract;
        }

        /// <summary>
        /// Serialize Contract to SecurityImpl
        /// </summary>
        /// <returns>
        /// STK: LocalSymbol SMART
        /// OPT/FOP: Symbol Expiry C/P Strike Exchange Type
        /// Other; LocalSymbol Exchange Type
        /// </returns>
        /// ToDo: Support Options
        private string ContractToSecurityFullName(Contract contract)
        {
            StringBuilder symbol = new StringBuilder();
            if (contract.SecType == "STK")
            {
                symbol.Append(contract.LocalSymbol).Append(" STK ");
                symbol.Append("SMART");
            }
            else if (contract.SecType == "OPT" || contract.SecType == "FOP")
            {
                symbol.Append(contract.Symbol).Append(" ");
                symbol.Append(contract.Expiry).Append(" ");             // YYYYMM
                if (contract.Right == "C")
                    symbol.Append("CALL").Append(" ");                // Call
                else
                    symbol.Append("PUT").Append(" ");                 // Put
                symbol.Append(contract.Strike.ToString()).Append(" ");
                if (string.IsNullOrEmpty(contract.Exchange))
                    symbol.Append(contract.PrimaryExch).Append(" ");
                else
                    symbol.Append(contract.Exchange).Append(" ");

                symbol.Append(contract.SecType);
            }
            else
            {
                symbol.Append(contract.LocalSymbol).Append(" ");
                symbol.Append(contract.SecType).Append(" ");

                if (string.IsNullOrEmpty(contract.Exchange))
                    symbol.Append(contract.PrimaryExch);
                else
                    symbol.Append(contract.Exchange);
            }

            // add multiplier
            int m = 1;      // stock multiplier = null
            bool success = int.TryParse(contract.Multiplier, out m);
            if (!success)
                m = GetMultiplier(contract.Symbol);
            if (m != 1)
            {
                symbol.Append(" ").Append(m.ToString());
            }

            return symbol.ToString();
        }

        /// <summary>
        /// IB OpenOrder may return null multiplier for ES futures, it needs to be filled with correct multiplier
        /// </summary>
        /// <param name="symbol">local symbol</param>
        /// <returns></returns>
        int GetMultiplier(string symbol)
        {
            int multiplier = 1;
            if (symbol == "ES") multiplier = 50;

            return multiplier;
        }

        private class OrderInfo
        {
            public long StrategyOrderId { get; set; }
            public string Account { get; set; }
            public bool IsAcknowledged { get; set; }

            public OrderInfo() { StrategyOrderId = 0; IsAcknowledged = false; Account = null; }
            public OrderInfo(long id, string acct, bool acked)
            {
                StrategyOrderId = id;
                Account = acct;
                IsAcknowledged = acked;
            }
        }
        #endregion

        #region Messages
        void OnGotTick(Tick k)
        {
            if (GotTickDelegate != null)
                GotTickDelegate(k);
        }

        void OnGotFill(Trade t)
        {
            if (GotFillDelegate != null)
                GotFillDelegate(t);
        }

        void OnGotOrder(Order o)
        {
            if (GotOrderDelegate != null)
                GotOrderDelegate(o);
        }

        void OnGotOrderCancel(long id)
        {
            if (GotOrderCancelDelegate != null)
                GotOrderCancelDelegate(id);
        }
        
        void OnGotPosition(Position p)
        {
            if (GotPositionDelegate != null)
                GotPositionDelegate(p);
        }

        void OnGotHistoricalBar(Bar b)
        {
            if (GotHistoricalBarDelegate != null)
                GotHistoricalBarDelegate(b);
        }

        void OnGotServerInitialized(string msg)
        {
            if (GotServerInitializedDelegate != null)
                GotServerInitializedDelegate(msg);
        }
        
        void OnDebug(string msg)
        {
            if (SendDebugEventDelegate != null)
                SendDebugEventDelegate(msg);
        }
        #endregion
    }
}
