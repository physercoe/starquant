#ifndef __StarQuant_Strategy_StrategyFactor_H__
#define __StarQuant_Strategy_StrategyFactor_H__

#include <memory>
#include <Common/config.h>
#include <Common/Strategy/strategybase.h>

// A factory function to create strategy
namespace StarQuant
{
	std::unique_ptr<StrategyBase> strategyFactory(const string& _algo);
}

#endif
