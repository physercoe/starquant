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
		map<string, AccountInfo> accinfomap_;     //accname->acc
		map<string, std::shared_ptr<Position> > positions_;			// poskey ->pos
		double cash_;

		void reset();
		void rebuild();

		void Add(std::shared_ptr<Position> ppos);
		double Adjust(const Fill& fill);
		std::shared_ptr<Position> retrievePosition(const string& key);
	};
}

#endif  // _StarQuant_Common_PortfolioManager_H_