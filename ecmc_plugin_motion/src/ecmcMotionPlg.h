/*************************************************************************\
* Copyright (c) 2023 Paul Scherrer Institute
* ecmc is distributed subject to a Software License Agreement found
* in file LICENSE that is included with this distribution. 
*
*  ecmcMotionPlg.h
*
*  Created on: july 10, 2023
*      Author: anderssandstrom
*
\*************************************************************************/
#ifndef ECMC_MOTION_PLG_H_
#define ECMC_MOTION_PLG_H_

#include <stdexcept>
#include "ecmcDataItem.h"
#include "ecmcAsynPortDriver.h"
#include "ecmcMotionPlgDefs.h"
#include "inttypes.h"
#include <string>
#include "dbBase.h"
#include "ecmcAxisBase.h"
#include "ecmcDataBuffer.h"
#include "epicsMutex.h"
#include "epicsEvent.h"

#define ECMC_PLUGIN_MOTION_ERROR_AXIS_OUT_OF_RANGE 1

typedef enum TRIGG_MODE{
  NO_MODE = 0,
  CONT    = 1,
  TRIGG   = 2,
} TRIGG_MODE;

class ecmcMotionPlg : public asynPortDriver {
 public:

  /** ecmc Motion Plg class
   * This object can throw: 
   *    - bad_alloc
   *    - invalid_argument
   *    - runtime_error
   *    - out_of_range
  */
  ecmcMotionPlg(int   objIndex,    // index of this object  
                char* configStr,
                char* portName);
  ~ecmcMotionPlg();  

  // Add data to buffer (called from "external" callback)
  void                  dataUpdatedCallback(uint8_t* data, 
                                            size_t size,
                                            ecmcEcDataType dt);
  // Call just before realtime because then all data sources should be available
  void                  connectToDataSource();
  void                  doWriteWorker();  // low prio worker thread
  void                  setEnable(int enable);
  void                  clearBuffers();
  void                  triggMotionObject();
  void                  executeMotionObject();
  virtual asynStatus    writeInt32(asynUser *pasynUser, epicsInt32 value);
  virtual asynStatus    readInt32(asynUser *pasynUser, epicsInt32 *value);
  virtual asynStatus    readFloat64Array(asynUser *pasynUser, epicsFloat64 *value,
                                         size_t nElements, size_t *nIn);
  virtual asynStatus    readFloat64(asynUser *pasynUser, epicsFloat64 *value);


 private:
  void                  parseConfigStr(char *configStr);
  void                  addDataToBuffer(double data);
  void                  initAsyn();
  static int            dataTypeSupported(ecmcEcDataType dt);
  int                   setAxis(int axisId);
  int                   setMode(TRIGG_MODE mode);
  int                   setTrigg(int trigg);
  void                  writeBuffers();
  void                  switchBuffers();


  epicsMutexId          axisMutex_;

  double*               xAxisArray_;        // FFT x axis with freqs
  size_t                elementsInBuffer_;
  double                ecmcSampleRateHz_;
  int                   dataSourceLinked_;   // To avoid link several times
  int                   command_;
  int                   status_;
  // ecmc callback handle for use when deregister at unload
  int                   callbackHandle_;
  int                   destructs_;
  int                   objectId_;           // Unique object id
  int                   triggOnce_;
  int                   cycleCounter_;
  int                   ignoreCycles_;

  // Config options
  int                   cfgDbgMode_;         // Config: allow dbg printouts
  size_t                cfgArraySize_;       // Config: Data set size
  int                   cfgEnable_;          // Config: Enable data acq./calc.
  double                cfgSampleRateHz_;    // Config: Sample rate (defaults to ecmc rate)
  double                cfgDataSampleRateHz_;// Config: Sample for data
  int                   cfgAxisIndex_;       // Config: Enable data acq./calc.
  TRIGG_MODE            cfgMode_;          // Config: Mode continous or triggered.

  // Asyn
  int                   asynEnableId_;       // Enable/disable acq./calcs
  int                   asynYActPosArrayId_;
  int                   asynYSetPosArrayId_;
  int                   asynYDiffPosArrayId_;
  int                   asynXAxisArrayId_;
  int                   asynTriggId_;        // Trigg new measurement
  int                   asynAxisId_;         //  motion axis id
  int                   asynSRateId_;        // Sample rate
  int                   asynElementsInBufferId_;  // Current buffer index
  int                   asynBufferSizeId_;  // Current buffer index
  int                   asynCommandId_;
  int                   asynStatusId_;
  int                   asynModeId_;
  
  ecmcAxisBase          *axis_;
  // Thread related
  //epicsEvent            doCalcEvent_;


  // Some generic utility functions
  static uint8_t        getUint8(uint8_t* data);
  static int8_t         getInt8(uint8_t* data);
  static uint16_t       getUint16(uint8_t* data);
  static int16_t        getInt16(uint8_t* data);
  static uint32_t       getUint32(uint8_t* data);
  static int32_t        getInt32(uint8_t* data);
  static uint64_t       getUint64(uint8_t* data);
  static int64_t        getInt64(uint8_t* data);
  static float          getFloat32(uint8_t* data);
  static double         getFloat64(uint8_t* data);
  static size_t         getEcDataTypeByteSize(ecmcEcDataType dt);
  static void           printEcDataArray(uint8_t*       data, 
                                         size_t         size,
                                         ecmcEcDataType dt,
                                         int objId);
  static void           printComplexArray(std::complex<double>* fftBuff,
                                          size_t elements,
                                          int objId);
  static std::string    to_string(int value);

  ecmcDataBuffer<epicsFloat64> *actPosBuffer_;
  ecmcDataBuffer<epicsFloat64> *setPosBuffer_;
  ecmcDataBuffer<epicsFloat64> *diffPosBuffer_;
  ecmcDataBuffer<epicsFloat64> *xPosBuffer_;
  ecmcDataBuffer<epicsInt8>    *enableBuffer_;
  ecmcDataBuffer<epicsInt8>    *enabledBuffer_;
  ecmcDataBuffer<epicsInt8>    *busyBuffer_;
  ecmcDataBuffer<epicsInt8>    *executeBuffer_;
  ecmcDataBuffer<epicsInt8>    *trajSourceBuffer_;
  ecmcDataBuffer<epicsInt8>    *encSourceBuffer_;
  ecmcDataBuffer<epicsInt8>    *atTargetBuffer_;
  ecmcDataBuffer<epicsInt32>   *errorIdBuffer_;

  bool                  bTriggInProgress_;
  double                xdt_;
  double                xTime_;
  epicsEvent            doWriteEvent_;
  int                   writeBusy_;  
  timespec              writePauseTime_;
};

#endif  /* ECMC_MOTION_PLG_H_ */
