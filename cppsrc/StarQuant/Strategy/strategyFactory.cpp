#include <boost/algorithm/string.hpp>
#include <Strategy/strategyFactory.h>

namespace StarQuant
{
	std::unique_ptr<StrategyBase> strategyFactory(const string& _algo) {
		/*if (boost::iequals(_algo, "simplecross")) {
			//return make_unique<SimpleCross>();
		}*/
		return nullptr;
	}
}
