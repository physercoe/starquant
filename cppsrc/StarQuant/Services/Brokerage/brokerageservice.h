#ifndef _StarQuant_Services_BrokerageService_H_
#define _StarQuant_Services_BrokerageService_H_

#include <memory>
#include <Common/config.h>
#include <Common/Data/marketdatafeed.h>
#include <Common/Brokerage/brokerage.h>

namespace StarQuant
{
	void BrokerageService(std::shared_ptr<brokerage> poms, int clientid=0);
}

#endif  // _StarQuant_Services_BrokerageService_H_
