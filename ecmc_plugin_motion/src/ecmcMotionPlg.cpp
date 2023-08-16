/*************************************************************************\
* Copyright (c) 2023 Paul Scherrer Institute
* ecmc is distributed subject to a Software License Agreement found
* in file LICENSE that is included with this distribution. 
*
*  ecmcMotionPlg.cpp
*
*  Created on: July 10, 2023
*      Author: anderssandstrom
*      Credits to  https://github.com/sgreg/dynamic-loading 
*
\*************************************************************************/

// Needed to get headers in ecmc right...
#define ECMC_IS_PLUGIN

#define ECMC_PLUGIN_ASYN_ENABLE           "enable"
#define ECMC_PLUGIN_ASYN_MOTION_COMMAND   "cmd"
#define ECMC_PLUGIN_ASYN_MOTION_STAT      "status"
#define ECMC_PLUGIN_ASYN_MOTION_TRIGG     "trigg"
#define ECMC_PLUGIN_ASYN_MOTION_MODE      "mode"
#define ECMC_PLUGIN_ASYN_AXIS_ID          "axis_id"
#define ECMC_PLUGIN_ASYN_RATE             "samplerate"
#define ECMC_PLUGIN_ASYN_X_DATA           "x_arr"
#define ECMC_PLUGIN_ASYN_Y_ACTPOS_DATA    "actpos_arr"
#define ECMC_PLUGIN_ASYN_Y_SETPOS_DATA    "setpos_arr"
#define ECMC_PLUGIN_ASYN_Y_DIFFPOS_DATA   "diffpos_arr"
#define ECMC_PLUGIN_ASYN_ENABLE_DATA      "enable_arr"
#define ECMC_PLUGIN_ASYN_ENABLED_DATA     "enabled_arr"
#define ECMC_PLUGIN_ASYN_BUSY_DATA        "busy_arr"
#define ECMC_PLUGIN_ASYN_EXECUTE_DATA     "execute_arr"
#define ECMC_PLUGIN_ASYN_TRAJSOURCE_DATA  "trajsrc_arr"
#define ECMC_PLUGIN_ASYN_ENCSOURCE_DATA   "encsrc_arr"
#define ECMC_PLUGIN_ASYN_ATTARGET_DATA    "attarget_arr"
#define ECMC_PLUGIN_ASYN_ERROR_DATA       "error_arr"
#define ECMC_PLUGIN_ASYN_BUFF_SIZE        "buff_size"
#define ECMC_PLUGIN_ASYN_ELEMENTS_IN_BUFF "elem_count"

#include <sstream>

#include "ecmcMotionPlg.h"
#include "ecmcPluginClient.h"
#include "ecmcAsynPortDriver.h"
#include "ecmcAsynPortDriverUtils.h"
#include "epicsThread.h"
#include "ecmcMotion.h"

// Breaktable
#include "ellLib.h"
#include "dbStaticLib.h"
#include "dbAccess.h"
#include "epicsVersion.h"
#include "cvtTable.h"
#ifdef BASE_VERSION
#define EPICS_3_13
extern DBBASE *pdbbase;
#endif

// Start worker for asyn write 
void f_worker_write(void *obj) {
  if(!obj) {
    printf("%s/%s:%d: Error: Worker write thread ecmcMotionPlg object NULL..\n",
            __FILE__, __FUNCTION__, __LINE__);
    return;
  }
  ecmcMotionPlg *mtnobj = (ecmcMotionPlg*)obj;
  mtnobj->doWriteWorker();
}

/** ecmc Motion Commissioning class
 * This object can throw: 
 *    - bad_alloc
 *    - invalid_argument
 *    - runtime_error
*/
ecmcMotionPlg::ecmcMotionPlg(int   objIndex,       // index of this object (if several is created)
                 char* configStr,
                 char* portName) 
                  : asynPortDriver(portName,
                   1, /* maxAddr */
                   asynInt32Mask | asynFloat64Mask | asynFloat32ArrayMask |
                   asynFloat64ArrayMask | asynEnumMask | asynDrvUserMask |
                   asynOctetMask | asynInt8ArrayMask | asynInt16ArrayMask |
                   asynInt32ArrayMask | asynUInt32DigitalMask, /* Interface mask */
                   asynInt32Mask | asynFloat64Mask | asynFloat32ArrayMask |
                   asynFloat64ArrayMask | asynEnumMask | asynDrvUserMask |
                   asynOctetMask | asynInt8ArrayMask | asynInt16ArrayMask |
                   asynInt32ArrayMask | asynUInt32DigitalMask, /* Interrupt mask */
                   ASYN_CANBLOCK , /*NOT ASYN_MULTI_DEVICE*/
                   1, /* Autoconnect */
                   0, /* Default priority */
                   0) /* Default stack size */
                   {
  
  axis_                = NULL;

  command_             = 0;
  status_              = 0;

  destructs_           = 0;
  callbackHandle_      = -1;
  objectId_            = objIndex;
  triggOnce_           = 0;
  cycleCounter_        = 0;
  ignoreCycles_        = 0;
  dataSourceLinked_    = 0;
  
  bTriggInProgress_    = false;

  asynEnableId_        = -1;    // Enable/disable acq./calcs
  asynYActPosArrayId_  = -1;    
  asynYSetPosArrayId_  = -1;    // FFT amplitude array (double)
  asynYDiffPosArrayId_ = -1;    // FFT mode (cont/trigg)
  asynTriggId_         = -1;    // Trigg new measurement
  asynXAxisArrayId_    = -1;    // FFT X-axis frequencies
  asynSRateId_         = -1;    // Sample rate Hz
  asynElementsInBufferId_ = -1;
  asynCommandId_       = -1;
  asynStatusId_        = -1;
  asynBufferSizeId_    = -1;
  asynModeId_          = -1;

  writeBusy_           = 0;
  writePauseTime_.tv_sec  = 0;
  writePauseTime_.tv_nsec = 0.5e6;  // 0.5ms

  axisMutex_           = epicsMutexCreate();  

  ecmcSampleRateHz_    = getEcmcSampleRate();
  cfgSampleRateHz_     = ecmcSampleRateHz_;
  cfgDataSampleRateHz_ = ecmcSampleRateHz_;
  cfgAxisIndex_        = 1;

  // Config defaults
  cfgDbgMode_          = 0;
  cfgArraySize_        = ECMC_PLUGIN_DEFAULT_ARRAY_SIZE; // samples in fft (must be n^2)
  cfgEnable_           = 0;   // start disabled (enable over asyn)

  parseConfigStr(configStr); // Assigns all configs
  // Check valid nfft
  if(cfgArraySize_ <= 0) {
    throw std::out_of_range("Array size must be > 0 (default 4096).");
  }

  // Check valid sample rate
  if(cfgSampleRateHz_ <= 0) {
    throw std::out_of_range("Invalid sample rate"); 
  }
  if(cfgSampleRateHz_ > ecmcSampleRateHz_) {
    printf("Warning selected sample rate faster than ecmc rate, rate will be set to ecmc rate.\n");
    cfgSampleRateHz_ = ecmcSampleRateHz_;
  }
    
  // Se if any data update cycles should be ignored
  // example ecmc 1000Hz, fft 100Hz then ignore 9 cycles (could be strange if not multiples)
  ignoreCycles_ = ecmcSampleRateHz_ / cfgSampleRateHz_ -1;

  // Allocate buffers
  actPosBuffer_      = new ecmcDataBuffer<double>(objectId_,0,
                                                  cfgArraySize_,
                                                  cfgDbgMode_,
                                                  ECMC_PLUGIN_ASYN_Y_ACTPOS_DATA,
                                                  this);
  setPosBuffer_      = new ecmcDataBuffer<double>(objectId_,1,
                                                  cfgArraySize_,
                                                  cfgDbgMode_,
                                                  ECMC_PLUGIN_ASYN_Y_SETPOS_DATA,
                                                  this);
  diffPosBuffer_     = new ecmcDataBuffer<double>(objectId_,2,
                                                  cfgArraySize_,
                                                  cfgDbgMode_,
                                                  ECMC_PLUGIN_ASYN_Y_DIFFPOS_DATA,
                                                  this);
  xPosBuffer_        = new ecmcDataBuffer<double>(objectId_,3,
                                                  cfgArraySize_,
                                                  cfgDbgMode_,
                                                  ECMC_PLUGIN_ASYN_X_DATA,
                                                  this);
  enableBuffer_      = new ecmcDataBuffer<epicsInt8>(objectId_,4,
                                                     cfgArraySize_,
                                                     cfgDbgMode_,
                                                     ECMC_PLUGIN_ASYN_ENABLE_DATA,
                                                     this);
  enabledBuffer_     = new ecmcDataBuffer<epicsInt8>(objectId_,5,
                                                     cfgArraySize_,
                                                     cfgDbgMode_,
                                                     ECMC_PLUGIN_ASYN_ENABLED_DATA,
                                                     this);
  busyBuffer_        = new ecmcDataBuffer<epicsInt8>(objectId_,6,
                                                     cfgArraySize_,
                                                     cfgDbgMode_,
                                                     ECMC_PLUGIN_ASYN_BUSY_DATA,
                                                     this);
  executeBuffer_     = new ecmcDataBuffer<epicsInt8>(objectId_,7,
                                                     cfgArraySize_,
                                                     cfgDbgMode_,
                                                     ECMC_PLUGIN_ASYN_EXECUTE_DATA,
                                                     this);
  trajSourceBuffer_  = new ecmcDataBuffer<epicsInt8>(objectId_,8,
                                                     cfgArraySize_,
                                                     cfgDbgMode_,
                                                     ECMC_PLUGIN_ASYN_TRAJSOURCE_DATA,
                                                     this);
  encSourceBuffer_   = new ecmcDataBuffer<epicsInt8>(objectId_,9,
                                                     cfgArraySize_,
                                                     cfgDbgMode_,
                                                     ECMC_PLUGIN_ASYN_ENCSOURCE_DATA,
                                                     this);
  atTargetBuffer_    = new ecmcDataBuffer<epicsInt8>(objectId_,10,
                                                     cfgArraySize_,
                                                     cfgDbgMode_,
                                                     ECMC_PLUGIN_ASYN_ATTARGET_DATA,
                                                     this);
  errorIdBuffer_     = new ecmcDataBuffer<epicsInt32>(objectId_,11,
                                                      cfgArraySize_,
                                                      cfgDbgMode_,
                                                      ECMC_PLUGIN_ASYN_ERROR_DATA,
                                                      this);

  axis_ = (ecmcAxisBase*) getAxisPointer(cfgAxisIndex_);
  clearBuffers();
 
  // init x axis (after clear)
  xdt_ = 1 / cfgSampleRateHz_;
  xTime_ = 0;
  for(size_t i=0;i<cfgArraySize_;i++) {
    xPosBuffer_->addData(xTime_);
    xTime_+=xdt_;
  }

  xTime_ = 0;
  initAsyn();

  // Create worker thread for writing socket
  std::string threadname = "ecmc." ECMC_PLUGIN_ASYN_PREFIX ".writer";
  if(epicsThreadCreate(threadname.c_str(), 0, 32768, f_worker_write, this) == NULL) {
    throw std::runtime_error("Error: Failed create worker thread for ecmc." ECMC_PLUGIN_ASYN_PREFIX ".writer");
  }
  doWriteEvent_.signal();
}

ecmcMotionPlg::~ecmcMotionPlg() {
  // kill worker
  destructs_ = 1;  // maybe need todo in other way.. 
  delete actPosBuffer_;
   
  // De register callback when unload
  //if(callbackHandle_ >= 0) {
  //  dataItem_->deregDataUpdatedCallback(callbackHandle_);
  //}
}

void ecmcMotionPlg::parseConfigStr(char *configStr) {

  // check config parameters
  if (configStr && configStr[0]) {    
    char *pOptions = strdup(configStr);
    char *pThisOption = pOptions;
    char *pNextOption = pOptions;
    
    while (pNextOption && pNextOption[0]) {
      pNextOption = strchr(pNextOption, ';');
      if (pNextOption) {
        *pNextOption = '\0'; /* Terminate */
        pNextOption++;       /* Jump to (possible) next */
      }
      
      // ECMC_PLUGIN_DBG_PRINT_OPTION_CMD (1/0)
      if (!strncmp(pThisOption, ECMC_PLUGIN_DBG_PRINT_OPTION_CMD, strlen(ECMC_PLUGIN_DBG_PRINT_OPTION_CMD))) {
        pThisOption += strlen(ECMC_PLUGIN_DBG_PRINT_OPTION_CMD);
        cfgDbgMode_ = atoi(pThisOption);
      } 
      
      // ECMC_PLUGIN_AXIS_OPTION_CMD (number)
      else if (!strncmp(pThisOption, ECMC_PLUGIN_AXIS_OPTION_CMD, strlen(ECMC_PLUGIN_AXIS_OPTION_CMD))) {
        pThisOption += strlen(ECMC_PLUGIN_AXIS_OPTION_CMD);
        cfgAxisIndex_ = atoi(pThisOption);
      }

      // ECMC_PLUGIN_ENABLE_OPTION_CMD (1/0)
      else if (!strncmp(pThisOption, ECMC_PLUGIN_ENABLE_OPTION_CMD, strlen(ECMC_PLUGIN_ENABLE_OPTION_CMD))) {
        pThisOption += strlen(ECMC_PLUGIN_ENABLE_OPTION_CMD);
        cfgEnable_ = atoi(pThisOption);
      }

      // ECMC_PLUGIN_BUFFER_SIZE_OPTION_CMD (number)
      else if (!strncmp(pThisOption, ECMC_PLUGIN_BUFFER_SIZE_OPTION_CMD, strlen(ECMC_PLUGIN_BUFFER_SIZE_OPTION_CMD))) {
        pThisOption += strlen(ECMC_PLUGIN_BUFFER_SIZE_OPTION_CMD);
        cfgArraySize_ = atoi(pThisOption);
      }

      // ECMC_PLUGIN_RATE_OPTION_CMD (number)
      else if (!strncmp(pThisOption, ECMC_PLUGIN_RATE_OPTION_CMD, strlen(ECMC_PLUGIN_RATE_OPTION_CMD))) {
        pThisOption += strlen(ECMC_PLUGIN_RATE_OPTION_CMD);
        cfgSampleRateHz_ = atof(pThisOption);
      }
      
      // ECMC_PLUGIN_MODE_OPTION_CMD CONT/TRIGG
      else if (!strncmp(pThisOption, ECMC_PLUGIN_MODE_OPTION_CMD, strlen(ECMC_PLUGIN_MODE_OPTION_CMD))) {
        pThisOption += strlen(ECMC_PLUGIN_MODE_OPTION_CMD);
        if(!strncmp(pThisOption, ECMC_PLUGIN_MODE_CONT_OPTION,strlen(ECMC_PLUGIN_MODE_CONT_OPTION))){
          cfgMode_ = CONT;
        }
        if(!strncmp(pThisOption, ECMC_PLUGIN_MODE_TRIGG_OPTION,strlen(ECMC_PLUGIN_MODE_TRIGG_OPTION))){
          cfgMode_ = TRIGG;
        }
      }

      pThisOption = pNextOption;
    }
    free(pOptions);
  }
}

void ecmcMotionPlg::connectToDataSource() {
  ///* Check if already linked (one call to enterRT per loaded FFT lib (FFT object))
  //    But link should only happen once!!*/
  //if( dataSourceLinked_ ) {
  //  return;
  //}
  //
  //// Get dataItem
  //dataItem_        = (ecmcDataItem*) getEcmcDataItem(cfgDataSourceStr_);
  //if(!dataItem_) {
  //  throw std::runtime_error( "Data item NULL." );
  //}
  //
  //dataItemInfo_ = dataItem_->getDataItemInfo();
//
  //// Register data callback
  //callbackHandle_ = dataItem_->regDataUpdatedCallback(f_dataUpdatedCallback, this);
  //if (callbackHandle_ < 0) {
  //  throw std::runtime_error( "Failed to register data source callback.");
  //}
//
  //// Check data source
  //if( !dataTypeSupported(dataItem_->getEcmcDataType()) ) {
  //  throw std::invalid_argument( "Data type not supported." );
  //}
//
  //// Add oversampling
  //cfgDataSampleRateHz_ = cfgSampleRateHz_ * dataItem_->getEcmcDataSize()/dataItem_->getEcmcDataElementSize();
  //setDoubleParam(asynSRateId_, cfgDataSampleRateHz_);
  //callParamCallbacks();
//
 // dataSourceLinked_ = 1;
 // updateStatus(IDLE);
}

void ecmcMotionPlg::dataUpdatedCallback(uint8_t*       data, 
                                        size_t         size,
                                        ecmcEcDataType dt) {
  
  //if(fftWaitingForCalc_) {
  //  return;
  //}
  //// No buffer or full or not enabled
  //if(!rawDataBuffer_ || !cfgEnable_) {
  //  return;
  //}
//
  //// See if data should be ignored
  //if(cycleCounter_ < ignoreCycles_) {
  //  cycleCounter_++;
  //  return; // ignore this callback
  //}
//
  //cycleCounter_ = 0;
//
  //if (cfgMode_ == TRIGG && !triggOnce_ ) {
  //  updateStatus(IDLE);
  //  return; // Wait for trigger from plc or asyn
  //}
//
  //if(cfgDbgMode_) {
  //  printEcDataArray(data, size, dt, objectId_);
//
  //  if(elementsInBuffer_ == cfgArraySize_) {
  //    printf("Buffer full (%zu elements appended).\n",elementsInBuffer_);
  //  }
  //}
  //
  //if(elementsInBuffer_ >= cfgArraySize_) {
  //  //Buffer full
  //  if(!fftWaitingForCalc_){            
  //    // Perform calcs
  //    updateStatus(CALC);
  //    fftWaitingForCalc_ = 1;
  //    doCalcEvent_.signal(); // let worker start
  //  }
  //  return;
  //}
//
  //updateStatus(ACQ);
//
  //size_t dataElementSize = getEcDataTypeByteSize(dt);
//
  //uint8_t *pData = data;
  //for(unsigned int i = 0; i < size / dataElementSize; ++i) {
  //  //printf("dataElementSize=%d, size=%d\n",dataElementSize,size);
  //  switch(dt) {
  //    case ECMC_EC_U8:        
  //      addDataToBuffer((double)getUint8(pData));
  //      break;
  //    case ECMC_EC_S8:
  //      addDataToBuffer((double)getInt8(pData));
  //      break;
  //    case ECMC_EC_U16:
  //      addDataToBuffer((double)getUint16(pData));
  //      break;
  //    case ECMC_EC_S16:
  //      addDataToBuffer((double)getInt16(pData));
  //      break;
  //    case ECMC_EC_U32:
  //      addDataToBuffer((double)getUint32(pData));
  //      break;
  //    case ECMC_EC_S32:
  //      addDataToBuffer((double)getInt32(pData));
  //      break;
  //    case ECMC_EC_U64:
  //      addDataToBuffer((double)getUint64(pData));
  //      break;
  //    case ECMC_EC_S64:
  //      addDataToBuffer((double)getInt64(pData));
  //      break;
  //    case ECMC_EC_F32:
  //      addDataToBuffer((double)getFloat32(pData));
  //      break;
  //    case ECMC_EC_F64:
  //      addDataToBuffer((double)getFloat64(pData));
  //      break;
  //    default:
  //      break;
  //  }
  //  
  //  pData += dataElementSize;
  //}
}//

//void ecmcMotionPlg::addDataToBuffer(double data) {
//  
//  if(rawDataBuffer_ && (elementsInBuffer_ < cfgArraySize_) ) {
//    
//    if( cfgBreakTableStr_ && interruptAccept ) {
//      double breakData = data;
//      // Supply a breaktable (init=0, LINR must be > 1 but only used if init > 0)       
//      if (cvtRawToEngBpt(&breakData, 2, 0, &breakTable_, &lastBreakPoint_)!=0) {        
//        //TODO: What does status here mean.. 
//        //throw std::runtime_error("Breaktable conversion failed.\n");
//      }
//      //printf("Index %d: Before %lf, after %lf\n",objectId_,data,breakData);
//      data = breakData * cfgScale_;
//    } else {
//      data = data * cfgScale_;
//    }
//
//    rawDataBuffer_[elementsInBuffer_] = data;
//    prepProcDataBuffer_[elementsInBuffer_] = data;
//  }
//  elementsInBuffer_ ++;
//}

void ecmcMotionPlg::clearBuffers() {
  actPosBuffer_->clear();
  setPosBuffer_->clear();
  diffPosBuffer_->clear();
  enableBuffer_->clear();
  enabledBuffer_->clear();
  busyBuffer_->clear();
  executeBuffer_->clear();
  trajSourceBuffer_->clear();
  encSourceBuffer_->clear();
  atTargetBuffer_->clear();
  errorIdBuffer_->clear();
  xPosBuffer_->clear();
}

void ecmcMotionPlg::printEcDataArray(uint8_t*  data, 
                               size_t         size,
                               ecmcEcDataType dt,
                               int objId) {
  printf("motion obj id: %d, data: ",objId);

  size_t dataElementSize = getEcDataTypeByteSize(dt);

  uint8_t *pData = data;
  for(unsigned int i = 0; i < size / dataElementSize; ++i) {    
    switch(dt) {
      case ECMC_EC_U8:        
        printf("%hhu\n",getUint8(pData));
        break;
      case ECMC_EC_S8:
        printf("%hhd\n",getInt8(pData));
        break;
      case ECMC_EC_U16:
        printf("%hu\n",getUint16(pData));
        break;
      case ECMC_EC_S16:
        printf("%hd\n",getInt16(pData));
        break;
      case ECMC_EC_U32:
        printf("%u\n",getUint32(pData));
        break;
      case ECMC_EC_S32:
        printf("%d\n",getInt32(pData));
        break;
      case ECMC_EC_U64:
        printf("%" PRIu64 "\n",getInt64(pData));
        break;
      case ECMC_EC_S64:
        printf("%" PRId64 "\n",getInt64(pData));
        break;
      case ECMC_EC_F32:
        printf("%f\n",getFloat32(pData));
        break;
      case ECMC_EC_F64:
        printf("%lf\n",getFloat64(pData));
        break;
      default:
        break;
    }
    
    pData += dataElementSize;
  }
}

int ecmcMotionPlg::dataTypeSupported(ecmcEcDataType dt) {

  switch(dt) {
    case ECMC_EC_NONE:      
      return 0;
      break;
    case ECMC_EC_B1:
      return 0;
      break;
    case ECMC_EC_B2:
      return 0;
      break;
    case ECMC_EC_B3:
      return 0;
      break;
    case ECMC_EC_B4:
      return 0;
      break;
    default:
      return 1;
      break;
  }
  return 1;
}

uint8_t   ecmcMotionPlg::getUint8(uint8_t* data) {
  return *data;
}

int8_t    ecmcMotionPlg::getInt8(uint8_t* data) {
  int8_t* p=(int8_t*)data;
  return *p;
}

uint16_t  ecmcMotionPlg::getUint16(uint8_t* data) {
  uint16_t* p=(uint16_t*)data;
  return *p;
}

int16_t   ecmcMotionPlg::getInt16(uint8_t* data) {
  int16_t* p=(int16_t*)data;
  return *p;
}

uint32_t  ecmcMotionPlg::getUint32(uint8_t* data) {
  uint32_t* p=(uint32_t*)data;
  return *p;
}

int32_t   ecmcMotionPlg::getInt32(uint8_t* data) {
  int32_t* p=(int32_t*)data;
  return *p;
}

uint64_t  ecmcMotionPlg::getUint64(uint8_t* data) {
  uint64_t* p=(uint64_t*)data;
  return *p;
}

int64_t   ecmcMotionPlg::getInt64(uint8_t* data) {
  int64_t* p=(int64_t*)data;
  return *p;
}

float     ecmcMotionPlg::getFloat32(uint8_t* data) {
  float* p=(float*)data;
  return *p;
}

double    ecmcMotionPlg::getFloat64(uint8_t* data) {
  double* p=(double*)data;
  return *p;
}

size_t ecmcMotionPlg::getEcDataTypeByteSize(ecmcEcDataType dt){
  switch(dt) {
  case ECMC_EC_NONE:
    return 0;
    break;

  case ECMC_EC_B1:
    return 1;
    break;

  case ECMC_EC_B2:
    return 1;
    break;

  case ECMC_EC_B3:
    return 1;
    break;

  case ECMC_EC_B4:
    return 1;
    break;

  case ECMC_EC_U8:
    return 1;
    break;

  case ECMC_EC_S8:
    return 1;
    break;

  case ECMC_EC_U16:
    return 2;
    break;

  case ECMC_EC_S16:
    return 2;
    break;

  case ECMC_EC_U32:
    return 4;
    break;

  case ECMC_EC_S32:
    return 4;
    break;

  case ECMC_EC_U64:
    return 8;
    break;

  case ECMC_EC_S64:
    return 8;
    break;

  case ECMC_EC_F32:
    return 4;
    break;

  case ECMC_EC_F64:
    return 8;
    break;

  default:
    return 0;
    break;
  }

  return 0;
}

void ecmcMotionPlg::initAsyn() {

  // Add enable "plugin.motion%d.enable"
  std::string paramName =ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objectId_) + 
             "." + ECMC_PLUGIN_ASYN_ENABLE;
  int *paramId = &asynEnableId_;
  if( createParam(0, paramName.c_str(), asynParamInt32, paramId) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter enable");
  }
  setIntegerParam(*paramId, cfgEnable_);

// Add xdata "plugin.motion%d.x_arr"
//  paramName =ECMC_PLUGIN_ASYN_PREFIX + to_string(objectId_) + 
//             "." + ECMC_PLUGIN_ASYN_X_DATA;
//  paramId = &asynXAxisArrayId_;
//  if( createParam(0, paramName.c_str(), asynParamFloat64Array, paramId ) != asynSuccess ) {
//    throw std::runtime_error("Failed create asyn parameter rawdata");
//  }
//  doCallbacksFloat64Array(xAxisArray_, cfgArraySize_, *paramId,0);
//
//  // Add actpos "plugin.motion%d.actpos_arr"
//  paramName =ECMC_PLUGIN_ASYN_PREFIX + to_string(objectId_) + 
//             "." + ECMC_PLUGIN_ASYN_Y_ACTPOS_DATA;
//  paramId = &asynYActPosArrayId_;
//  if( createParam(0, paramName.c_str(), asynParamFloat64Array, paramId ) != asynSuccess ) {
//    throw std::runtime_error("Failed create asyn parameter rawdata");
//  }
//  doCallbacksFloat64Array(yActPosArray_, cfgArraySize_, *paramId,0);
//
//  // Add actpos "plugin.motion%d.setpos_arr"
//  paramName =ECMC_PLUGIN_ASYN_PREFIX + to_string(objectId_) + 
//             "." + ECMC_PLUGIN_ASYN_Y_SETPOS_DATA;
//  paramId = &asynYSetPosArrayId_;
//  if( createParam(0, paramName.c_str(), asynParamFloat64Array, paramId ) != asynSuccess ) {
//    throw std::runtime_error("Failed create asyn parameter rawdata");
//  }
//  doCallbacksFloat64Array(ySetPosArray_, cfgArraySize_, *paramId,0);
//
//  // Add diffpos "plugin.motion%d.diffpos_arr"
//  paramName =ECMC_PLUGIN_ASYN_PREFIX + to_string(objectId_) + 
//             "." + ECMC_PLUGIN_ASYN_Y_DIFFPOS_DATA;
//  paramId = &asynYDiffPosArrayId_;
//  if( createParam(0, paramName.c_str(), asynParamFloat64Array, paramId ) != asynSuccess ) {
//    throw std::runtime_error("Failed create asyn parameter rawdata");
//  }
//  doCallbacksFloat64Array(yDiffPosArray_, cfgArraySize_, *paramId,0);
//
  // Add motion "plugin.motion%d.command"
  paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objectId_) + 
             "." + ECMC_PLUGIN_ASYN_MOTION_COMMAND;
  paramId = &asynCommandId_;
  if( createParam(0, paramName.c_str(), asynParamInt32, paramId ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter mode");
  }
  setIntegerParam(*paramId, (epicsInt32)command_);

  // Add motion "plugin.motion%d.status"
  paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objectId_) + 
             "." + ECMC_PLUGIN_ASYN_MOTION_STAT;
  paramId = &asynStatusId_;
  if( createParam(0, paramName.c_str(), asynParamInt32, paramId ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter mode");
  }
  setIntegerParam(*paramId, (epicsInt32)status_);

    // Add motion "plugin.motion%d.trigg"
  paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objectId_) + 
             "." + ECMC_PLUGIN_ASYN_MOTION_TRIGG;
  paramId = &asynTriggId_;

  if( createParam(0, paramName.c_str(), asynParamInt32, paramId ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter trigg");
  }
  setIntegerParam(*paramId, (epicsInt32)triggOnce_);

  // Add motion  plugin.motion%d.buff_size"
  paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objectId_) + 
             "." + ECMC_PLUGIN_ASYN_BUFF_SIZE;
  paramId = &asynBufferSizeId_;
  if( createParam(0, paramName.c_str(), asynParamInt32, paramId ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter nfft");
  }
  setIntegerParam(*paramId, (epicsInt32)cfgArraySize_);

  // Add motion "plugin.motion%d.rate"
  paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objectId_) + 
             "." + ECMC_PLUGIN_ASYN_RATE;
  paramId = &asynSRateId_;

  if( createParam(0, paramName.c_str(), asynParamFloat64, paramId ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter rate");
  }
  setDoubleParam(*paramId, cfgSampleRateHz_);

  // Add motion "plugin.motion%d.elem_count"
  paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objectId_) + 
             "." + ECMC_PLUGIN_ASYN_ELEMENTS_IN_BUFF;
  paramId = &asynElementsInBufferId_;

  if( createParam(0, paramName.c_str(), asynParamInt32, paramId ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter trigg");
  }
  setIntegerParam(*paramId, (epicsInt32)elementsInBuffer_);

  // Add motion "plugin.motion%d.axis"
  paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objectId_) + 
             "." + ECMC_PLUGIN_ASYN_AXIS_ID;
  paramId = &asynAxisId_;

  if( createParam(0, paramName.c_str(), asynParamInt32, paramId ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter axis id");
  }
  setIntegerParam(*paramId, (epicsInt32)cfgAxisIndex_);

  // Add motion "plugin.motion%d.mode"
  paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objectId_) + 
             "." + ECMC_PLUGIN_ASYN_MOTION_MODE;
  paramId = &asynModeId_;

  if( createParam(0, paramName.c_str(), asynParamInt32, paramId ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter mode");
  }
  setIntegerParam(*paramId, (epicsInt32)cfgMode_);

  // Update integers
  callParamCallbacks();
}

// Avoid issues with std:to_string()
std::string ecmcMotionPlg::to_string(int value) {
  std::ostringstream os;
  os << value;
  return os.str();
}

void ecmcMotionPlg::setEnable(int enable) {
  cfgEnable_ = enable;
  setIntegerParam(asynEnableId_, enable);
  actPosBuffer_->setEnable(enable);
  setPosBuffer_->setEnable(enable);
  diffPosBuffer_->setEnable(enable);
  xPosBuffer_->setEnable(enable);
}
  
void ecmcMotionPlg::triggMotionObject() {
  clearBuffers();
  triggOnce_ = 1;
  setIntegerParam(asynTriggId_,0);
}


// Executed by ecmc rt thread.
void ecmcMotionPlg::executeMotionObject() {
  
  if(!axis_) {
    return;
  }
  
  if(cfgMode_==TRIGG && !bTriggInProgress_) {
    return;
  }

  // protect axis_ if axis object id is changed over asyn
  epicsMutexLock(axisMutex_);
  ecmcAxisStatusType *tempAxisStat = axis_->getDebugInfoDataPointer();
  
  // Fill the buffers
  actPosBuffer_->addData(tempAxisStat->onChangeData.positionActual);
  setPosBuffer_->addData(tempAxisStat->onChangeData.positionSetpoint);
  diffPosBuffer_->addData(tempAxisStat->onChangeData.positionError);
  enableBuffer_->addData(tempAxisStat->onChangeData.statusWd.enable);
  enabledBuffer_->addData(tempAxisStat->onChangeData.statusWd.enabled);
  busyBuffer_->addData(tempAxisStat->onChangeData.statusWd.busy);
  executeBuffer_->addData(tempAxisStat->onChangeData.statusWd.execute);
  trajSourceBuffer_->addData(tempAxisStat->onChangeData.statusWd.trajsource);
  encSourceBuffer_->addData(tempAxisStat->onChangeData.statusWd.encsource);
  atTargetBuffer_->addData(tempAxisStat->onChangeData.statusWd.attarget);
  errorIdBuffer_->addData(tempAxisStat->onChangeData.error);

  xTime_+=xdt_;
  xPosBuffer_->addData(xTime_);  // Always relative within one buffer

  // If buffers full the (all buffers syncronous so all should be full if one is full)
  if(actPosBuffer_->getBufferFull()) {
    bTriggInProgress_ = false;
    xTime_ = 0;  //reset x axis
    switchBuffers();  // unfortenately needed here
    doWriteEvent_.signal();
  }
  epicsMutexUnlock(axisMutex_);
}

//void ecmcMotionPlg::setModeFFT(FFT_MODE mode) {
//  cfgMode_ = mode;
//  setIntegerParam(asynFFTModeId_,(epicsInt32)mode);
//}
//
//FFT_STATUS ecmcMotionPlg::getStatusFFT() {
//  return status_;
//}

//void ecmcMotionPlg::updateStatus(FFT_STATUS status) {
//  status_ = status;
//  setIntegerParam(asynFFTStatId_,(epicsInt32) status);
//  
//  setIntegerParam(asynElementsInBuffer_, (epicsInt32)elementsInBuffer_);
//
//  callParamCallbacks();
//}

asynStatus ecmcMotionPlg::writeInt32(asynUser *pasynUser, epicsInt32 value) {
  int function = pasynUser->reason;
  if( function == asynEnableId_ ) {
    cfgEnable_ = value;
    return asynSuccess;
  } else if( function == asynTriggId_){
    triggOnce_ = value > 0;
    return asynSuccess;
  } else if( function == asynCommandId_){
    command_ = value > 0;
    //also exe something?
    return asynSuccess;
  } else if( function == asynEnableId_){
    setEnable(value > 0);
    return asynSuccess;
  } else if( function == asynAxisId_){
    return setAxis(value) > 0 ? asynSuccess : asynError;
  } else if( function == asynModeId_){
    return setMode((TRIGG_MODE)value) > 0 ? asynSuccess : asynError;    
  } else if( function == asynModeId_){
    return setTrigg(value) ? asynSuccess :asynError;    
  }

  return asynError;
}

asynStatus ecmcMotionPlg::readInt32(asynUser *pasynUser, epicsInt32 *value) {
  int function = pasynUser->reason;
  if( function == asynEnableId_ ) {
    *value = cfgEnable_;
    return asynSuccess;
  } else if( function == asynAxisId_){
    *value = cfgAxisIndex_;
    return asynSuccess;
  } else if( function == asynTriggId_ ){
    *value = triggOnce_;
    return asynSuccess;
  }else if( function == asynStatusId_ ){
    *value = (epicsInt32)status_;
    return asynSuccess;
  }else if( function == asynBufferSizeId_ ){
    *value = (epicsInt32)cfgArraySize_;
    return asynSuccess;
  }else if( function == asynElementsInBufferId_){
    *value = (epicsInt32)elementsInBuffer_;
    return asynSuccess;
  } else if( function == asynEnableId_){
    *value =cfgEnable_;
    return asynSuccess;
  }

  return asynError;
}

// These callbacks are moved to ecmcdataBuffer class
asynStatus ecmcMotionPlg::readFloat64Array(asynUser *pasynUser, epicsFloat64 *value,
                                     size_t nElements, size_t *nIn) {
  *nIn = 0;
  return asynError;
}

asynStatus  ecmcMotionPlg::readFloat64(asynUser *pasynUser, epicsFloat64 *value) {
  int function = pasynUser->reason;
  if( function == asynSRateId_ ) {
    *value = cfgDataSampleRateHz_;
    return asynSuccess;
  }

  return asynError;
}

int ecmcMotionPlg::setAxis(int axisId) {
  ecmcAxisBase *temp= (ecmcAxisBase*) getAxisPointer(axisId);
  if(!temp) {
    printf("Warning selected axis index out of range.\n");
    //set old value again
    setParamAlarmStatus(asynAxisId_,1);
    setParamAlarmSeverity(asynAxisId_,1);
    setIntegerParam(asynAxisId_, (epicsInt32)cfgAxisIndex_);
    callParamCallbacks();
    return ECMC_PLUGIN_MOTION_ERROR_AXIS_OUT_OF_RANGE;    
  }

  epicsMutexLock(axisMutex_);
  clearBuffers();
  axis_ = temp;
  cfgAxisIndex_ = axisId;
  epicsMutexUnlock(axisMutex_);

  setParamAlarmStatus(asynAxisId_,0);
  setParamAlarmSeverity(asynAxisId_,0);
  setIntegerParam(asynAxisId_, (epicsInt32)cfgAxisIndex_);
  callParamCallbacks();
  return 0;  
}

int ecmcMotionPlg::setTrigg(int trigg) {
  if(cfgMode_==TRIGG) {
    epicsMutexLock(axisMutex_);
    clearBuffers();
    bTriggInProgress_ = true;
    epicsMutexUnlock(axisMutex_);
  }
  return 0;
}

int ecmcMotionPlg::setMode(TRIGG_MODE mode) {
  cfgMode_ = mode;
  return 0;
}

// Write socket worker thread (switch between two buffers)
void ecmcMotionPlg::doWriteWorker() {
  while(true) {    
    if(destructs_) {
      return;
    }    

    nanosleep(&writePauseTime_,NULL);    

    if(writeBusy_ || !cfgEnable_ ) {
      continue;
    }

    if(destructs_) {
      return;
    }
 
    doWriteEvent_.wait();
    writeBusy_ = 1;
    writeBuffers();
    writeBusy_ = 0;
  }
}

// triggered by low prio work thread only
void ecmcMotionPlg::writeBuffers() {
  
  //Write all buffers
  actPosBuffer_->writeBuffer();
  setPosBuffer_->writeBuffer();
  diffPosBuffer_->writeBuffer();
  enableBuffer_->writeBuffer();
  enabledBuffer_->writeBuffer();
  busyBuffer_->writeBuffer();
  executeBuffer_->writeBuffer();
  trajSourceBuffer_->writeBuffer();
  encSourceBuffer_->writeBuffer();
  atTargetBuffer_->writeBuffer();
  errorIdBuffer_->writeBuffer();
  // Always write x last if triggering is needed
  xPosBuffer_->writeBuffer();
}

// triggered by ecmc RT thread
void ecmcMotionPlg::switchBuffers() {

// switch in new empty buffer while data is stored in the other.
  actPosBuffer_->switchBuffer();
  setPosBuffer_->switchBuffer();
  diffPosBuffer_->switchBuffer();
  enableBuffer_->switchBuffer();
  enabledBuffer_->switchBuffer();
  busyBuffer_->switchBuffer();
  executeBuffer_->switchBuffer();
  trajSourceBuffer_->switchBuffer();
  encSourceBuffer_->switchBuffer();
  atTargetBuffer_->switchBuffer();
  errorIdBuffer_->switchBuffer();
  xPosBuffer_->switchBuffer();
}
