/*************************************************************************\
* Copyright (c) 2023 Paul Scherrer Institute
* ecmc is distributed subject to a Software License Agreement found
* in file LICENSE that is included with this distribution. 
*
*  ecmcPluginExample.cpp
*
*  Created on: july 10, 2023
*      Author: anderssandstrom
*
\*************************************************************************/

// Needed to get headers in ecmc right...
#define ECMC_IS_PLUGIN
#define ECMC_EXAMPLE_PLUGIN_VERSION 2

#ifdef __cplusplus
extern "C" {
#endif  // ifdef __cplusplus

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "ecmcPluginDefs.h"
#include "ecmcMotionPlgDefs.h"
#include "ecmcMotionPlgWrap.h"

static int    lastEcmcError   = 0;
static char*  lastConfStr         = NULL;

/** Optional. 
 *  Will be called once after successfull load into ecmc.
 *  Return value other than 0 will be considered error.
 *  configStr can be used for configuration parameters.
 **/
int motionConstruct(char *configStr)
{
  //This module is allowed to load several times so no need to check if loaded

  // create FFT object and register data callback
  lastConfStr = strdup(configStr);
  return createMotionObj(configStr);
}

/** Optional function.
 *  Will be called once at unload.
 **/
void motionDestruct(void)
{
  deleteAllMotionObjs();
  if(lastConfStr){
    free(lastConfStr);
  }
}

/** Optional function.
 *  Will be called each realtime cycle if definded
 *  ecmcError: Error code of ecmc. Makes it posible for 
 *  this plugin to react on ecmc errors
 *  Return value other than 0 will be considered to be an error code in ecmc.
 **/
int motionRealtime(int ecmcError)
{ 
  executeMotionObjs();
  lastEcmcError = ecmcError;
  return 0;
}

/** Link to data source here since all sources should be availabe at this stage
 *  (for example ecmc PLC variables are defined only at enter of realtime)
 **/
int motionEnterRT(){
  return linkDataTomotionObjs();
}

/** Optional function.
 *  Will be called once just before leaving realtime mode
 *  Return value other than 0 will be considered error.
 **/
int motionExitRT(void){
  return 0;
}

//// Plc function for clear of buffers
//double fft_clear(double index) {
//  return (double)clearFFT((int)index);
//}
//
//// Plc function for enable
//double fft_enable(double index, double enable) {
//  return (double)enableFFT((int)index, (int)enable);
//}
//
//// Plc function for trigg new measurement (will clear buffers)
//double fft_trigg(double index) {
//  return (double)triggFFT((int)index);
//}
//
//// Plc function for enable
//double fft_mode(double index, double mode) {
//  return (double)modeFFT((int)index, (FFT_MODE)((int)mode));
//}
//
//// Plc function for enable
//double fft_stat(double index) {
//  return (double)statFFT((int)index);
//}

// Register data for plugin so ecmc know what to use
struct ecmcPluginData pluginDataDef = {
  // Allways use ECMC_PLUG_VERSION_MAGIC
  .ifVersion = ECMC_PLUG_VERSION_MAGIC, 
  // Name 
  .name = "ecmcPlugin_Motion",
  // Description
  .desc = "Motion plugin for commissioning of ecmc motion axes.",
  // Option description
  .optionDesc = "\n    "ECMC_PLUGIN_DBG_PRINT_OPTION_CMD"<1/0>     : Enables/disables printouts from plugin, default = disabled.\n"
                "    "ECMC_PLUGIN_AXIS_OPTION_CMD"<axis id>      : Sets default source axis id.\n"
                "    "ECMC_PLUGIN_BUFFER_SIZE_OPTION_CMD"<size>  : Data points to collect, default = 4096.\n" 
                "    "ECMC_PLUGIN_RATE_OPTION_CMD"<rate hz>      : Sampling rate in Hz" 
                "    "ECMC_PLUGIN_MODE_OPTION_CMD"<TRIGG/CONT>   : Sampling rate in Hz" 
                , 
  // Plugin version
  .version = ECMC_EXAMPLE_PLUGIN_VERSION,
  // Optional construct func, called once at load. NULL if not definded.
  .constructFnc = motionConstruct,
  // Optional destruct func, called once at unload. NULL if not definded.
  .destructFnc = motionDestruct,
  // Optional func that will be called each rt cycle. NULL if not definded.
  .realtimeFnc = motionRealtime,
  // Optional func that will be called once just before enter realtime mode
  .realtimeEnterFnc = motionEnterRT,
  // Optional func that will be called once just before exit realtime mode
  .realtimeExitFnc = motionExitRT,
  // PLC funcs
//  .funcs[0] =
//      { /*----fft_clear----*/
//        // Function name (this is the name you use in ecmc plc-code)
//        .funcName = "fft_clear",
//        // Function description
//        .funcDesc = "double fft_clear(index) : Clear/reset fft[index].",
//        /**
//        * 7 different prototypes allowed (only doubles since reg in plc).
//        * Only funcArg${argCount} func shall be assigned the rest set to NULL.
//        **/
//        .funcArg0 = NULL,
//        .funcArg1 = fft_clear,
//        .funcArg2 = NULL,
//        .funcArg3 = NULL,
//        .funcArg4 = NULL,
//        .funcArg5 = NULL,
//        .funcArg6 = NULL,
//        .funcArg7 = NULL,
//        .funcArg8 = NULL,
//        .funcArg9 = NULL,
//        .funcArg10 = NULL,
//        .funcGenericObj = NULL,
//      },
//  .funcs[1] =
//      { /*----fft_enable----*/
//        // Function name (this is the name you use in ecmc plc-code)
//        .funcName = "fft_enable",
//        // Function description
//        .funcDesc = "double fft_enable(index, enable) : Set enable for fft[index].",
//        /**
//        * 7 different prototypes allowed (only doubles since reg in plc).
//        * Only funcArg${argCount} func shall be assigned the rest set to NULL.
//        **/
//        .funcArg0 = NULL,
//        .funcArg1 = NULL,
//        .funcArg2 = fft_enable,
//        .funcArg3 = NULL,
//        .funcArg4 = NULL,
//        .funcArg5 = NULL,
//        .funcArg6 = NULL,
//        .funcArg7 = NULL,
//        .funcArg8 = NULL,
//        .funcArg9 = NULL,
//        .funcArg10 = NULL,
//        .funcGenericObj = NULL,
//      },
//    .funcs[2] =
//      { /*----fft_trigg----*/
//        // Function name (this is the name you use in ecmc plc-code)
//        .funcName = "fft_trigg",
//        // Function description
//        .funcDesc = "double fft_trigg(index) : Trigg new measurement for fft[index]. Will clear buffers.",
//        /**
//        * 7 different prototypes allowed (only doubles since reg in plc).
//        * Only funcArg${argCount} func shall be assigned the rest set to NULL.
//        **/
//        .funcArg0 = NULL,
//        .funcArg1 = fft_trigg,
//        .funcArg2 = NULL,
//        .funcArg3 = NULL,
//        .funcArg4 = NULL,
//        .funcArg5 = NULL,
//        .funcArg6 = NULL,
//        .funcArg7 = NULL,
//        .funcArg8 = NULL,
//        .funcArg9 = NULL,
//        .funcArg10 = NULL,
//        .funcGenericObj = NULL,
//      },
//    .funcs[3] =
//      { /*----fft_mode----*/
//        // Function name (this is the name you use in ecmc plc-code)
//        .funcName = "fft_mode",
//        // Function description
//        .funcDesc = "double fft_mode(index, mode) : Set mode Cont(1)/Trigg(2) for fft[index].",
//        /**
//        * 7 different prototypes allowed (only doubles since reg in plc).
//        * Only funcArg${argCount} func shall be assigned the rest set to NULL.
//        **/
//        .funcArg0 = NULL,
//        .funcArg1 = NULL,
//        .funcArg2 = fft_mode,
//        .funcArg3 = NULL,
//        .funcArg4 = NULL,
//        .funcArg5 = NULL,
//        .funcArg6 = NULL,
//        .funcArg7 = NULL,
//        .funcArg8 = NULL,
//        .funcArg9 = NULL,
//        .funcArg10 = NULL,
//        .funcGenericObj = NULL,
//      },
//    .funcs[4] =
//      { /*----fft_stat----*/
//        // Function name (this is the name you use in ecmc plc-code)
//        .funcName = "fft_stat",
//        // Function description
//        .funcDesc = "double fft_stat(index) : Get status of fft (NO_STAT, IDLE, ACQ, CALC) for fft[index].",
//        /**
//        * 7 different prototypes allowed (only doubles since reg in plc).
//        * Only funcArg${argCount} func shall be assigned the rest set to NULL.
//        **/
//        .funcArg0 = NULL,
//        .funcArg1 = fft_stat,
//        .funcArg2 = NULL,
//        .funcArg3 = NULL,
//        .funcArg4 = NULL,
//        .funcArg5 = NULL,
//        .funcArg6 = NULL,
//        .funcArg7 = NULL,
//        .funcArg8 = NULL,
//        .funcArg9 = NULL,
//        .funcArg10 = NULL,
//        .funcGenericObj = NULL,
//      },
  .funcs[0] = {0},  // last element set all to zero..
  // PLC consts
  /* CONTINIOUS MODE = 1 */
//  .consts[0] = {
//        .constName = "fft_CONT",
//        .constDesc = "FFT Mode: Continious",
//        .constValue = CONT
//      },
//  /* TRIGGERED MODE = 2 */
//  .consts[1] = {
//        .constName = "fft_TRIGG",
//        .constDesc = "FFT Mode :Triggered",
//        .constValue = TRIGG
//      },
//  /* TRIGGERED MODE = 2 */
//  .consts[2] = {
//        .constName = "fft_NO_STAT",
//        .constDesc = "FFT Status: Invalid state",
//        .constValue = NO_STAT,
//      },
//  /* TRIGGERED MODE = 2 */
//  .consts[3] = {
//        .constName = "fft_IDLE",
//        .constDesc = "FFT Status: Idle state (waiting for trigger)",
//        .constValue = IDLE
//      },
//  /* TRIGGERED MODE = 2 */
//  .consts[4] = {
//        .constName = "fft_ACQ",
//        .constDesc = "FFT Status: Acquiring data",
//        .constValue = ACQ
//      },
//  /* TRIGGERED MODE = 2 */
//  .consts[5] = {
//        .constName = "fft_CALC",
//        .constDesc = "FFT Status: Calculating result",
//        .constValue = CALC
//      },
  .consts[0] = {0}, // last element set all to zero..
};

ecmc_plugin_register(pluginDataDef);

# ifdef __cplusplus
}
# endif  // ifdef __cplusplus
