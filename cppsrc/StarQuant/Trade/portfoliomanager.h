#ifndef _StarQuant_Common_PortfolioManager_H_
#define _StarQuant_Common_PortfolioManager_H_

#include <string>
#include <assert.h>
#include <numeric>
#include <mutex>
#include <regex>
#include <atomic>
#include <map>
#include <Common/config.h>
#include <Trade/accountinfo.h>
#include <Trade/position.h>
#include <Trade/orderstatus.h>
#include <Trade/order.h>
#include <Common/logger.h>

using namespace std;

namespace StarQuant {
	class PortfolioManager {
	public:
		PortfolioManager();
		~PortfolioManager();
		static PortfolioManager* pinstance_;
		static mutex instancelock_;
		static PortfolioManager& instance();
		//atomic<uint64_t> _count = { 0 };
		uint64_t _count = 0;
		AccountInfo _account;
		map<string, AccountInfo> accinfomap_;
		map<string, Position> _positions;			// fullsymbol --> size
		double _cash;

		void reset();
		void rebuild();

		void Add(Position& pos);
		double Adjust(Fill& fill);
	};
}

#endif  // _StarQuant_Common_PortfolioManager_H_