#ifndef _StarQuant_Common_HeartBeat_H_
#define _StarQuant_Common_HeartBeat_H_

#include <time.h>

namespace StarQuant
{
	class CHeartbeat {
	protected:
		time_t last_time;
	public:
		// derived class overwrites heartbeat to tell if itself is still alive
		bool heartbeat(int);
	};
}
#endif
