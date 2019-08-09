include_directories(${StarQuantCpp_SOURCE_DIR}/StarQuant)
include_directories(${StarQuantCpp_SOURCE_DIR}/StarQuant/APIs/Oes)
set(StarQuantCppSrc
  ./Common/datastruct.cpp
  ./Common/util.cpp
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
  ./Engine/XtpMDEngine.cpp
  ./Engine/OesMDEngine.cpp
 # ./Engine/TapMDEngine.cpp
  ./Engine/PaperTDEngine.cpp
  ./Services/dataservice.cpp
  ./Services/starquant_.cpp
  ./Services/tradingengine.cpp
   )

add_library(starquant-dev SHARED ${StarQuantCppSrc})
set_target_properties(starquant-dev  PROPERTIES COMPILE_FLAGS "-fPIC")
target_link_libraries(starquant-dev  
  ${Boost_LIBRARIES} 
  ${PYTHON_LIBRARY} 
  ${MONGOC_LIBRARIES} 
  ${LOG4CPLUS_LIBRARIES} 
  ${YAMLCPP_LIBRARY} 
  ${FMT_LIBRARIES} 
  ${NANOMSG_LIBRARY_SHARED}
  LinuxDataCollect 
  thosttraderapi 
  thostmduserapi 
  TapQuoteAPI 
  TapTradeAPI
  xtptraderapi
  xtpquoteapi
  oes_api
  pthread 
  dl 
  util
  m)
set(SQSERVER_SRC  ./Services/sqserver.cpp )
add_executable(testapiserver.exe ${SQSERVER_SRC})
TARGET_LINK_LIBRARIES(testapiserver.exe starquant-dev)