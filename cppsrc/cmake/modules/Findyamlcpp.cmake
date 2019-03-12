#
# Find yaml-cpp
#
# This module defines the following variables:
# - YAMLCPP_INCLUDE_DIRS
# - YAMLCPP_LIBRARIES
# - YAMLCPP_FOUND
#
# The following variables can be set as arguments for the module.
# - YAMLCPP_ROOT_DIR : Root library directory of yaml-cpp
#

# Additional modules
include(FindPackageHandleStandardArgs)

if (WIN32)
	# Find include files
	find_path(
		YAMLCPP_INCLUDE_DIR
		NAMES yaml-cpp/yaml.h
		PATHS
			$ENV{PROGRAMFILES}/include
			${YAMLCPP_ROOT_DIR}/include
		DOC "The directory where yaml-cpp/yaml.h resides")

	# Find library files
	find_library(
		YAMLCPP_LIBRARY_RELEASE
		NAMES libyaml-cppmd
		PATHS
			$ENV{PROGRAMFILES}/lib
			${YAMLCPP_ROOT_DIR}/lib)

	find_library(
		YAMLCPP_LIBRARY_DEBUG
		NAMES libyaml-cppmdd
		PATHS
			$ENV{PROGRAMFILES}/lib
			${YAMLCPP_ROOT_DIR}/lib)
else()
	# Find include files
	find_path(
		YAMLCPP_INCLUDE_DIR
		NAMES yaml-cpp/yaml.h
		PATHS
			/usr/include
			/usr/local/include
			/sw/include
			/opt/local/include
		DOC "The directory where yaml-cpp/yaml.h resides")

	# Find library files
	find_library(
		YAMLCPP_LIBRARY
		NAMES yaml-cpp
		PATHS
			/usr/lib64
			/usr/lib
			/usr/lib/x86_64-linux-gnu
			/usr/local/lib64
			/usr/local/lib
			/sw/lib
			/opt/local/lib
			${YAMLCPP_ROOT_DIR}/lib
		DOC "The yaml-cpp library")
endif()

if (WIN32)
	# Handle REQUIRD argument, define *_FOUND variable
	find_package_handle_standard_args(yamlcpp DEFAULT_MSG YAMLCPP_INCLUDE_DIR YAMLCPP_LIBRARY_RELEASE YAMLCPP_LIBRARY_DEBUG)

	# Define YAMLCPP_LIBRARIES and YAMLCPP_INCLUDE_DIRS
	if (YAMLCPP_FOUND)
		set(YAMLCPP_LIBRARIES_RELEASE ${YAMLCPP_LIBRARY_RELEASE})
		set(YAMLCPP_LIBRARIES_DEBUG ${YAMLCPP_LIBRARY_DEBUG})
		set(YAMLCPP_LIBRARIES debug ${YAMLCPP_LIBRARIES_DEBUG} optimized ${YAMLCPP_LIBRARY_RELEASE})
		set(YAMLCPP_INCLUDE_DIRS ${YAMLCPP_INCLUDE_DIR})
	endif()

	# Hide some variables
	mark_as_advanced(YAMLCPP_INCLUDE_DIR YAMLCPP_LIBRARY_RELEASE YAMLCPP_LIBRARY_DEBUG)
else()
	find_package_handle_standard_args(yamlcpp DEFAULT_MSG YAMLCPP_INCLUDE_DIR YAMLCPP_LIBRARY)
	
	if (YAMLCPP_FOUND)
		set(YAMLCPP_LIBRARIES ${YAMLCPP_LIBRARY})
		set(YAMLCPP_INCLUDE_DIRS ${YAMLCPP_INCLUDE_DIR})
	endif()

	mark_as_advanced(YAMLCPP_INCLUDE_DIR YAMLCPP_LIBRARY)
endif()

