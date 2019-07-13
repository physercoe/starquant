

#ifndef CPPSRC_STARQUANT_TRADE_CALC_H
#define CPPSRC_STARQUANT_TRADE_CALC_H

#include <Common/datastruct.h>

namespace StarQuant {
    namespace Calc {
        // Gets the open PL on a per-share basis, ignoring the size of the position.
        double OpenPT(double LastTrade, double AvgPrice, bool Side);
        double OpenPT(double LastTrade, double AvgPrice, int32_t PosSize);
        // Gets the open PL considering all the shares held in a position.
        double OpenPL(double LastTrade, double AvgPrice, int32_t PosSizeMultiplier);

        // Gets the closed PL on a per-share basis, ignoring how many shares are held.
        double ClosePT(const Position& existing, const Fill& adjust);
        // Gets the closed PL on a position basis, the PL that is registered to the account for the entire shares transacted.
        double ClosePL(const Position& existing, const Fill& adjust, int32_t multiplier = 1);
    }  // namespace Calc
}  // namespace StarQuant

#endif  // CPPSRC_STARQUANT_TRADE_CALC_H
