#include <cmath>
#include <Trade/calc.h>
#include <Common/datastruct.h>

using namespace std;

namespace StarQuant {
	namespace Calc {

		double OpenPT(double LastTrade, double AvgPrice, bool Side)
		{
			return Side ? LastTrade - AvgPrice : AvgPrice - LastTrade;
		}

		double OpenPT(double LastTrade, double AvgPrice, int PosSize)
		{
			return (PosSize == 0) ? 0 : OpenPT(LastTrade, AvgPrice, PosSize > 0);
		}

		double OpenPL(double LastTrade, double AvgPrice, int PosSizeMultiplier)
		{
			return PosSizeMultiplier * (LastTrade - AvgPrice);
		}

		double ClosePT(Position& existing, Fill& adjust)
		{
			if (existing.size_ == 0) return 0; // nothing to close
			if ((existing.size_ > 0) == (adjust.tradeSize_ > 0)) return 0; // if we're adding, nothing to close
			return (existing.size_ > 0) ? adjust.tradePrice_ - existing.avgPrice_ : existing.avgPrice_ - adjust.tradePrice_;   // if long, sell high = profit; if short, sell low = profit
		}

		double ClosePL(Position& existing, Fill& adjust, int multiplier)
		{
			int closedsize = std::abs(adjust.tradeSize_) > std::abs(existing.size_) ? std::abs(existing.size_) : std::abs(adjust.tradeSize_);   // choose the smaller one
			return ClosePT(existing, adjust) * closedsize * multiplier;
		}
	}
}