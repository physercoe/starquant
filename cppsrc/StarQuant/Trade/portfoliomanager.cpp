#include <Trade/portfoliomanager.h>

namespace StarQuant {
	PortfolioManager* PortfolioManager::pinstance_ = nullptr;
	mutex PortfolioManager::instancelock_;

	PortfolioManager::~PortfolioManager()
	{
		// release all the positions
		/*for (auto&& p : _positions) {
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
		/*for (auto&& p : _positions) {
			if (p.second != nullptr) delete p.second;
		}*/

		_positions.clear();
		_count = 0;
	}

	void PortfolioManager::rebuild() {
		reset();
	}

	void PortfolioManager::Add(Position& pos) {
		auto it = _positions.find(pos._fullsymbol);
		if (it == _positions.end()) {
			_positions.insert(std::pair<string, Position>(pos._fullsymbol, pos));
		}
		else {
			_positions[pos._fullsymbol] = pos;
		}
	}

	double PortfolioManager::Adjust(Fill& fill) {
		auto it = _positions.find(fill.fullSymbol);
		if (it == _positions.end()) {
			Position pos;
			pos._fullsymbol = fill.fullSymbol;
			pos._size = 0;
			pos._avgprice = 0;
			_positions.insert(std::pair<string, Position>(fill.fullSymbol, pos));

		}

		return _positions[fill.fullSymbol].Adjust(fill);
	}
}