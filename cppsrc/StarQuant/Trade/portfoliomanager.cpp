#include <Trade/portfoliomanager.h>
#include <Common/datastruct.h>
namespace StarQuant {
	PortfolioManager* PortfolioManager::pinstance_ = nullptr;
	mutex PortfolioManager::instancelock_;

	PortfolioManager::~PortfolioManager()
	{
		// release all the positions
		/*for (auto&& p : positions_) {
			if (p.second != nullptr) delete p.second;
		}*/
	}

	PortfolioManager& PortfolioManager::instance() {
		if (pinstance_ == nullptr) {
			lock_guard<mutex> g(instancelock_);
			if (pinstance_ == nullptr) {
				pinstance_ = new PortfolioManager();
			}
		}
		return *pinstance_;
	}

	PortfolioManager::PortfolioManager() :_count(0) {
		rebuild();
	}

	void PortfolioManager::reset() {
		/*for (auto&& p : positions_) {
			if (p.second != nullptr) delete p.second;
		}*/

		positions_.clear();
		_count = 0;
	}

	void PortfolioManager::rebuild() {
		reset();
	}

	void PortfolioManager::Add(const Position& pos) {
		auto it = positions_.find(pos.fullSymbol_);
		if (it == positions_.end()) {
			positions_.insert(std::pair<string, Position>(pos.fullSymbol_, pos));
		}
		else {
			positions_[pos.fullSymbol_] = pos;
		}
	}

	double PortfolioManager::Adjust(const Fill& fill) {
		auto it = positions_.find(fill.fullSymbol_);
		if (it == positions_.end()) {
			Position pos;
			pos.fullSymbol_ = fill.fullSymbol_;
			pos.size_ = 0;
			pos.avgPrice_ = 0;
			positions_.insert(std::pair<string, Position>(fill.fullSymbol_, pos));

		}

		// return positions_[fill.fullSymbol_].Adjust(fill);TODO: add adjust
		return 1.0;
	}
}