# the minimum version of CMake required
cmake_minimum_required(VERSION 2.8)
PROJECT(StarQuantCpp C CXX)
# required for unit testing using CMake's ctest command
LIST(APPEND CMAKE_MODULE_PATH  ${StarQuantCpp_SOURCE_DIR}/cmake/modules)

include(CTest)
include(CheckIncludeFile)
include(CheckIncludeFileCXX)
include(CheckIncludeFiles)
include(ExternalProject)

#Find Packages
find_package(ZLIB REQUIRED)
find_package(PkgConfig)
find_package(Boost REQUIRED COMPONENTS system filesystem regex thread python3 locale date_time)
find_package(rapidjson REQUIRED)
FIND_PACKAGE(PythonInterp)
FIND_PACKAGE(PythonLibs)
find_package(yamlcpp REQUIRED)
find_package(nanomsg REQUIRED)
find_package(cereal REQUIRED)


INCLUDE_DIRECTORIES(${ZLIB_INCLUDE_DIR})
INCLUDE_DIRECTORIES(${RAPIDJSON_INCLUDE_DIRS})
INCLUDE_DIRECTORIES(${PYTHON_INCLUDE_DIR})
INCLUDE_DIRECTORIES(${Boost_INCLUDE_DIR})
INCLUDE_DIRECTORIES(${YAMLCPP_INCLUDE_DIR})
include_directories(${NANOMSG_INCLUDE_DIR})
include_directories(${CEREAL_INCLUDE_DIR})




ADD_DEFINITIONS("-std=gnu++17 -DIB_USE_STD_STRING ")
subdirs(StarQuant)

get_property(dirs DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR} PROPERTY INCLUDE_DIRECTORIES)
foreach(dir ${dirs})
  message(STATUS "dir='${dir}'")
endforeach()


