#include <cmath>
#include <Common/config.h>
#include <Trade/calc.h>

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
			if (existing._size == 0) return 0; // nothing to close
			if ((existing._size > 0) == (adjust.tradeSize > 0)) return 0; // if we're adding, nothing to close
			return (existing._size > 0) ? adjust.tradePrice - existing._avgprice : existing._avgprice - adjust.tradePrice;   // if long, sell high = profit; if short, sell low = profit
		}

		double ClosePL(Position& existing, Fill& adjust, int multiplier)
		{
			int closedsize = std::abs(adjust.tradeSize) > std::abs(existing._size) ? std::abs(existing._size) : std::abs(adjust.tradeSize);   // choose the smaller one
			return ClosePT(existing, adjust) * closedsize * multiplier;
		}
	}
}