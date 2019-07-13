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
#include <Services/tradingengine.h>
#include <boost/python.hpp>

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
