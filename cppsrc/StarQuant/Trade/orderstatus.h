#ifndef _StarQuant_Trade_OrderStatus_H_
#define _StarQuant_Trade_OrderStatus_H_
#include <string>

namespace StarQuant {
	enum OrderStatus {
		OS_UNKNOWN = 0,		// Unknown
		OS_NewBorn = 1,			// NewBorn
		OS_PendingSubmit = 2,   
		OS_Submitted = 3,			// submitted
		OS_Acknowledged = 4,		// acknowledged
		OS_Queued =5,
		OS_PartiallyFilled = 6,		// PartiallyFilled
		OS_Filled = 7,				// Filled
		OS_PendingCancel = 8 ,
		OS_PendingModify =9 ,
		OS_Canceled = 10,			// Canceled
		OS_LeftDelete = 11,
		OS_Suspended = 12,
		OS_ApiPending = 13,
		OS_ApiCancelled = 14,
		OS_Fail =15,                 //指令失败
		OS_Deleted =16,             
		OS_Effect = 17,             //已生效-询价成功
		OS_Apply = 18,              //已申请-行权，弃权等申请成功
		OS_Error = 19,
		OS_Trig =20,
		OS_Exctrig=21
	};

// #define THOST_FTDC_OST_AllTraded '0'
// ///部分成交还在队列中
// #define THOST_FTDC_OST_PartTradedQueueing '1'
// ///部分成交不在队列中
// #define THOST_FTDC_OST_PartTradedNotQueueing '2'
// ///未成交还在队列中
// #define THOST_FTDC_OST_NoTradeQueueing '3'
// ///未成交不在队列中
// #define THOST_FTDC_OST_NoTradeNotQueueing '4'
// ///撤单
// #define THOST_FTDC_OST_Canceled '5'
// ///未知
// #define THOST_FTDC_OST_Unknown 'a'
// ///尚未触发
// #define THOST_FTDC_OST_NotTouched 'b'
// ///已触发
// #define THOST_FTDC_OST_Touched 'c'





	enum OrderFlag {			// for CTP,tap offset flag
		OF_None = -1,
		OF_OpenPosition = 0,
		OF_ClosePosition = 1,
		OF_CloseToday = 2,
		OF_CloseYesterday = 3,
		OF_ForceClose = 4,
		OF_ForceOff = 5,
		OF_LocalForceClose = 6
	};

	const std::string OrderStatusString[] = {
		"Unknown",
		"NewBorn",
		"PendingSubmit",
		"Submitted",
		"Acknowledged",
		"Queued",
		"PartiallyFilled",
		"Filled",
		"PendingCancel",
		"PendingModify",
		"Canceled",
		"LeftDelete",
		"Suspended",
		"ApiPending",
		"ApiCancelled",
		"Fail",
		"Deleted",
		"Effect",
		"Apply",
		"Error",
		"Trigerrring",
		"ExcTriggering",
		"None"
	};

	//OrderStatus getOrderStatus(const std::string& status);
	std::string getOrderStatusString(OrderStatus ost);
}

#endif  // _StarQuant_Common_OrderStatus_H_