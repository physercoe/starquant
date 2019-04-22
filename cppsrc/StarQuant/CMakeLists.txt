include_directories(${StarQuantCpp_SOURCE_DIR}/StarQuant)
set(StarQuantCppSrc
  ./Common/datastruct.cpp
  ./Common/util.cpp
  ./Common/heartbeat.cpp
  ./Common/logger.cpp
  ./Common/config.cpp
  ./Common/msgq.cpp
  ./Data/datamanager.cpp
  ./Trade/calc.cpp
  ./Trade/marginmanager.cpp
  ./Trade/riskmanager.cpp
  ./Trade/ordermanager.cpp
  ./Trade/portfoliomanager.cpp
  ./Engine/IEngine.cpp
  ./Engine/CtpMDEngine.cpp
  ./Engine/CtpTDEngine.cpp
 # ./Engine/TapMDEngine.cpp
 # ./Engine/TapTDEngine.cpp
 # ./Engine/PaperTDEngine.cpp
  ./Services/dataservice.cpp
  ./Services/starquant_.cpp
  ./Services/tradingengine.cpp
   )

add_library(starquant SHARED ${StarQuantCppSrc})
set_target_properties(starquant  PROPERTIES COMPILE_FLAGS "-fPIC")
target_link_libraries(starquant  ${Boost_LIBRARIES} ${PYTHON_LIBRARY} ${MONGOC_LIBRARIES} ${LOG4CPLUS_LIBRARIES} ${YAMLCPP_LIBRARY} LinuxDataCollect thosttraderapi thostmduserapi TapQuoteAPI TapTradeAPI  ${NANOMSG_LIBRARY_SHARED} pthread dl util m)
set(SQSERVER_SRC  ./Services/sqserver.cpp )
add_executable(sqserver ${SQSERVER_SRC})
TARGET_LINK_LIBRARIES(sqserver starquant)