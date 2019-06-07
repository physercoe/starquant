#include <boost/python.hpp>
#include <Services/tradingengine.h>
using namespace boost::python;
using namespace StarQuant;

// http://www.shocksolution.com/python-basics-tutorials-and-examples/linking-python-and-c-with-boostpython/

#ifdef _WIN32
BOOST_PYTHON_MODULE(StarQuant)
#else
BOOST_PYTHON_MODULE(libstarquant)
#endif
{
    class_<tradingengine, boost::noncopyable>("tradingengine_").
        def("run", &tradingengine::run).
        def("live", &tradingengine::live);
}
