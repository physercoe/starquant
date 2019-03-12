#include <Common/Order/orderstatus.h>

using namespace std;

namespace StarQuant
{
	std::string getOrderStatusString(OrderStatus ost) {
		return OrderStatusString[(int)ost];
	}
}