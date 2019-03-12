#ifndef __StarQuant_Common_GetRealTime_H__
#define __StarQuant_Common_GetRealTime_H__

/*
* Author:  David Robert Nadeau
* Site:    http://NadeauSoftware.com/
* License: Creative Commons Attribution 3.0 Unported License
*          http://creativecommons.org/licenses/by/3.0/deed.en_US
*/
#include <inttypes.h>

namespace StarQuant
{
#if defined(_WIN32) || defined(_WIN64)
#include <Windows.h>

#elif defined(__unix__) || defined(__unix) || defined(unix) || (defined(__APPLE__) && defined(__MACH__))
#include <unistd.h>	/* POSIX flags */
#include <time.h>	/* clock_gettime(), time() */
#include <sys/time.h>	/* gethrtime(), gettimeofday() */

#if defined(__MACH__) && defined(__APPLE__)
#include <mach/mach.h>
#include <mach/mach_time.h>
#endif

#else
#error "Unable to define getRealTime( ) for an unknown OS."
#endif

#define __MILLI_MULTIPLE__ 1000
#define __MICRO_MULTIPLE__ 1000000
#define __NANOO_MULTIPLE__ 1000000000
	/**
	* Returns the real time, in micro-seconds, or 0 if an error occurred.
	*
	* Time is measured since an arbitrary and OS-dependent start time.
	* The returned real time is only useful for computing an elapsed time
	* between two calls to this function.
	*/
	uint64_t getMicroTime();
}
#endif  // __StarQuant_Common_GetRealTime_H__

