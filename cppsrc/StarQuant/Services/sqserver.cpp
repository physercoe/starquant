#include <iostream>
#include <iomanip>
#include <ctime>
#include <string>
#include <sstream>

#include <stdio.h>
#include <Common/util.h>
#include <Common/timeutil.h>
#include <Services/tradingengine.h>

#include <boost/array.hpp>
#include <algorithm>

using namespace StarQuant;

int main(int argc, char** argv) {
	std::cout << "StarQuant Trading Engine. Version 0.1\n";

	tradingengine engine;
	std::cout << "Type Ctrl-C to exit\n\n";
	engine.run();
	return 0;
}