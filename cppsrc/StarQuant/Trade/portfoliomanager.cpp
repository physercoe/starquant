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

void PortfolioManager::Add(std::shared_ptr<Position> pos) {
    if (pos)
        positions_[pos->key_] = pos;
}

double PortfolioManager::Adjust(const Fill& fill) {
    // auto it = positions_.find(fill.fullSymbol_);
    // if (it == positions_.end()) {
    // 	Position pos;
    // 	pos.fullSymbol_ = fill.fullSymbol_;
    // 	pos.size_ = 0;
    // 	pos.avgPrice_ = 0;
    // 	positions_.insert(std::pair<string, Position>(fill.fullSymbol_, pos));

    // }

    // return positions_[fill.fullSymbol_].Adjust(fill);TODO: add adjust
    return 1.0;
}

std::shared_ptr<Position> PortfolioManager::retrievePosition(const string& key) {
    auto it = positions_.find(key);
    if (it != positions_.end()) {
        return it->second;
    }
    return nullptr;
}


}  // namespace StarQuant
