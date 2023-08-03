#
#  Copyright (c) 2023    Paul Scherrer Institute
#
#  The program is free software: you can redistribute
#  it and/or modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation, either version 2 of the
#  License, or any newer version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#  more details.
#
#  You should have received a copy of the GNU General Public License along with
#  this program. If not, see https://www.gnu.org/licenses/gpl-2.0.txt
#
# 
# Author  : anderssandstrom
# email   : anders.sandstroem@psi.ch
# Date    : 2023 July 10
# version : 0.0.0 
#


## The following lines are mandatory, please don't change them.
where_am_I := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
include $(E3_REQUIRE_TOOLS)/driver.makefile
include $(E3_REQUIRE_CONFIG)/DECOUPLE_FLAGS

ifneq ($(strip $(ASYN_DEP_VERSION)),)
asyn_VERSION=$(ASYN_DEP_VERSION)
endif

ifneq ($(strip $(ECMC_DEP_VERSION)),)
ecmc_VERSION=$(ECMC_DEP_VERSION)
endif

ifneq ($(strip $(RUCKIG_DEP_VERSION)),)
ruckig_VERSION=$(RUCKIG_DEP_VERSION)
endif

ifeq ($(T_A),linux-x86_64)
  # Assume that the etherlab user library is done via
  # https://github.com/icshwi/etherlabmaster
  USR_INCLUDES += -I/opt/etherlab/include
  USR_CFLAGS += -fPIC
  USR_LDFLAGS += -L /opt/etherlab/lib
  USR_LDFLAGS += -lethercat
  USR_LDFLAGS += -Wl,-rpath=/opt/etherlab/lib
else 
  ifeq ($(T_A),linux-arm)
    # Assume that the etherlab user library is done via
    # https://github.com/icshwi/etherlabmaster
    USR_INCLUDES += -I/opt/etherlab/include
    USR_CFLAGS += -fPIC
    USR_LDFLAGS += -L /opt/etherlab/lib
    USR_LDFLAGS += -lethercat
    USR_LDFLAGS += -Wl,-rpath=/opt/etherlab/lib
  else
    # Assume that the etherlab user library is done via
    # Yocto ESS Linux bb recipe
    USR_INCLUDES += -I$(SDKTARGETSYSROOT)/usr/include/etherlab
    USR_CFLAGS   += -fPIC
    USR_LDFLAGS  += -L $(SDKTARGETSYSROOT)/usr/lib/etherlab
    USR_LDFLAGS  += -lethercat
    USR_LDFLAGS  += -Wl,-rpath=$(SDKTARGETSYSROOT)/usr/lib/etherlab
    USR_LDFLAGS  += -lstdc++
  endif
endif

APP:="."
#APPDB:=$(APP)/Db
#APPSRC:=$(APP)/src
APPSRC:=src
APPDB:=Db

USR_CFLAGS   += -shared -fPIC -Wall -Wextra
USR_LDFLAGS  += -lstdc++
USR_INCLUDES += -I$(where_am_I)$(APPSRC)

TEMPLATES += $(wildcard $(APPDB)/*.db)
TEMPLATES += $(wildcard $(APPDB)/*.template)
SOURCES += $(APPSRC)/ecmcPluginMotion.c
SOURCES += $(APPSRC)/ecmcMotionPlgWrap.cpp
SOURCES += $(APPSRC)/ecmcMotionPlg.cpp
#SOURCES += $(APPSRC)/ecmcDataBuffer.cpp

SCRIPTS += startup.cmd
SCRIPTS += addMotionObj.cmd

db:

.PHONY: db

vlibs:

.PHONY: vlibs

###
