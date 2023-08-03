/*************************************************************************\
* Copyright (c) 2023 Paul Scherrer Institute
* ecmc is distributed subject to a Software License Agreement found
* in file LICENSE that is included with this distribution. 
*
*  ecmcMotionPlgDefs.h
*
*  Created on: july 10, 2023
*      Author: anderssandstrom
*      Credits to  https://github.com/sgreg/dynamic-loading
*
\*************************************************************************/

#ifndef ECMC_MOTION_PLG_DEFS_H_
#define ECMC_MOTION_PLG_DEFS_H_

#define ECMC_PLUGIN_ASYN_PREFIX         "plugin.motion"

// Options
#define ECMC_PLUGIN_DBG_PRINT_OPTION_CMD   "DBG_PRINT="
#define ECMC_PLUGIN_AXIS_OPTION_CMD        "AXIS="
#define ECMC_PLUGIN_BUFFER_SIZE_OPTION_CMD "BUFFER_SIZE="
#define ECMC_PLUGIN_RATE_OPTION_CMD        "RATE="
#define ECMC_PLUGIN_ENABLE_OPTION_CMD      "ENABLE="
#define ECMC_PLUGIN_MODE_OPTION_CMD        "MODE="

// CONT, TRIGG
#define ECMC_PLUGIN_MODE_CONT_OPTION       "CONT"
#define ECMC_PLUGIN_MODE_TRIGG_OPTION      "TRIGG"

 
/** Just one error code in "c" part of plugin 
(error handled with exceptions i c++ part) */
#define ECMC_PLUGIN_MOTION_ERROR_CODE 1

// Default size (must be n²)
#define ECMC_PLUGIN_DEFAULT_ARRAY_SIZE 4096

#endif  /* ECMC_MOTION_PLG_DEFS_H_ */
