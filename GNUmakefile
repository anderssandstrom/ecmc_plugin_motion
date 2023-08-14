include /ioc/tools/driver.makefile

MODULE = ecmc_plugin_motion

BUILDCLASSES = Linux
ARCH_FILTER = deb10%

# Run 7.0.6 for now
EXCLUDE_VERSIONS+=3 7.0.5 7.0.7

IGNORE_MODULES += asynMotor
IGNORE_MODULES += motorBase

USR_CXXFLAGS += -std=c++17
OPT_CXXFLAGS_YES = -O3

# dependencies
ECmasterECMC_VERSION = v1.1.0
motorECMC_VERSION = 7.0.7-ESS
ecmc_VERSION = v9.0.1_RC1

################################################################################
# THIS RELATES TO THE EtherCAT MASTER LIBRARY
# IT IS OF PARAMOUNT IMPORTANCE TO LOAD THE PROPER KERNEL MODULE
# ################################################################################
USR_LDFLAGS += -lethercat

EC_MASTER_LIB = ${EPICS_MODULES}/ECmasterECMC/${ECmasterECMC_VERSION}/R${EPICSVERSION}/lib/${T_A}
USR_LDFLAGS += -Wl,-rpath=${EC_MASTER_LIB}
USR_LDFLAGS +=         -L ${EC_MASTER_LIB}

BASE_DIR = ecmc_plugin_motion
SRC_DIR = $(BASE_DIR)/src
DB_DIR =  $(BASE_DIR)/db

SOURCES += $(SRC_DIR)/ecmcPluginMotion.c
SOURCES += $(SRC_DIR)/ecmcMotionPlgWrap.cpp
SOURCES += $(SRC_DIR)/ecmcMotionPlg.cpp

#SOURCES += $(foreach d,${SRC_DIR}, $(wildcard $d/*.c) $(wildcard $d/*.cpp))
HEADERS += $(foreach d,${SRC_DIR}, $(wildcard $d/*.h))
DBDS += $(foreach d,${SRC_DIR}, $(wildcard $d/*.dbd))
SCRIPTS += $(BASE_DIR)/startup.cmd
SCRIPTS += $(BASE_DIR)/addMotionObj.cmd
TEMPLATES += $(wildcard $(DB_DIR)/*.template)

