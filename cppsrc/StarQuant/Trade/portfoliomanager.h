#ifndef _StarQuant_Common_PortfolioManager_H_
#define _StarQuant_Common_PortfolioManager_H_

#include <string>
#include <assert.h>
#include <numeric>
#include <mutex>
#include <regex>
#include <atomic>
#include <map>
#include <Common/datastruct.h>


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
		AccountInfo account_;
		map<string, AccountInfo> accinfomap_;
		map<string, Position> positions_;			// fullsymbol --> size
		double cash_;

		void reset();
		void rebuild();

		void Add(const Position& pos);
		double Adjust(const Fill& fill);
	};
}

#endif  // _StarQuant_Common_PortfolioManager_H_