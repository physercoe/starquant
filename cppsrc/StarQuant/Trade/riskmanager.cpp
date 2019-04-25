#include <Trade/riskmanager.h>
#include <Common/config.h>
namespace StarQuant {


	RiskManager* RiskManager::pinstance_ = nullptr;
	mutex RiskManager::instancelock_;

	RiskManager::RiskManager() : alive_(false)
	{
		// set up from config
		reset();
	}

	RiskManager::~RiskManager()
	{

	}

	RiskManager& RiskManager::instance() {
		if (pinstance_ == nullptr) {
			lock_guard<mutex> g(instancelock_);
			if (pinstance_ == nullptr) {
				pinstance_ = new RiskManager();
			}
		}
		return *pinstance_;
	}

	void RiskManager::reset() {
        alive_ = CConfig::instance().riskcheck;
        limitSizePerOrder_ = CConfig::instance().sizeperorderlimit;
        limitCashPerOrder_ = CConfig::instance().cashperorderlimit;
        limitOrderCount_ = CConfig::instance().ordercountlimit;
        limitCash_ = CConfig::instance().cashlimit;
        limitOrderSize_ = CConfig::instance().ordersizelimit;
        limitOrderCountPerSec_ = CConfig::instance().ordercountperseclimit;

	}
	void RiskManager::resetflow() {
        orderCountPerSec_ = 0;

	}
	void RiskManager::switchday() {
        totalOrderCount_ = 0;
        totalCash_ = 0.0;
        totalOrderSize_ = 0;

	}        

}

