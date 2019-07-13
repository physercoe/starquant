/*****************************************************************************
 * Copyright [2019] 
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *  http://www.apache.org/licenses/LICENSE-2.0
 *
 *  Unless required by applicable law or agreed to in writing, software
 *  distributed under the License is distributed on an "AS IS" BASIS,
 *  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 *  See the License for the specific language governing permissions and
 *  limitations under the License.
 *****************************************************************************/

#include <Trade/calc.h>
#include <Common/datastruct.h>
#include <cmath>


using namespace std;

namespace StarQuant {
    namespace Calc {

        double OpenPT(double LastTrade, double AvgPrice, bool Side) {
            return Side ? LastTrade - AvgPrice : AvgPrice - LastTrade;
        }

        double OpenPT(double LastTrade, double AvgPrice, int32_t PosSize) {
            return (PosSize == 0) ? 0 : OpenPT(LastTrade, AvgPrice, PosSize > 0);
        }

        double OpenPL(double LastTrade, double AvgPrice, int32_t PosSizeMultiplier) {
            return PosSizeMultiplier * (LastTrade - AvgPrice);
        }

        double ClosePT(Position& existing, Fill& adjust) {
            if (existing.size_ == 0) return 0; // nothing to close
            if ((existing.size_ > 0) == (adjust.tradeSize_ > 0)) return 0; // if we're adding, nothing to close
            return (existing.size_ > 0) ? adjust.tradePrice_ - existing.avgPrice_ : existing.avgPrice_ - adjust.tradePrice_;   // if long, sell high = profit; if short, sell low = profit
        }

        double ClosePL(Position& existing, Fill& adjust, int32_t multiplier) {
            int32_t closedsize = std::abs(adjust.tradeSize_) > std::abs(existing.size_) ? std::abs(existing.size_) : std::abs(adjust.tradeSize_);   // choose the smaller one
            return ClosePT(existing, adjust) * closedsize * multiplier;
        }
    }  // namespace Calc
}  // namespace StarQuant
