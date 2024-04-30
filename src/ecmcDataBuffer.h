/*************************************************************************\
* Copyright (c) 2019 European Spallation Source ERIC
* ecmc is distributed subject to a Software License Agreement found
* in file LICENSE that is included with this distribution. 
*
*  ecmcDataBuffer.h
*
*  Created on: Mar 22, 2020
*      Author: anderssandstrom
*
\*************************************************************************/
#ifndef ECMC_DATA_BUFFER_WRITE_H_
#define ECMC_DATA_BUFFER_WRITE_H_

#include "ecmcAsynPortDriver.h"

#include <stdexcept>
#include "inttypes.h"
#include <string>

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include "asynPortDriver.h"
#include "epicsMutex.h"
#include "ecmcMotionPlgDefs.h"

template <typename T>
struct dataBuffer {      
  T      *data;
  int     dataCounter;
  int     id;
};

/* 
Implements a data buffer with asyn callbacks.

The buffer uses two memory areas. When one mem area is full, 
writes are redirected to the other buffer. The full buffer then 
can be transferred to epics. 

*/

template <typename T>
class ecmcDataBuffer {
 public:

  /** ecmc ecmcDataBuffer class
   * This object can throw: 
   *    - bad_alloc
   *    - invalid_argument
   *    - runtime_error
   *    - out_of_range
  */

  ecmcDataBuffer(int objIndex,
                 int bufferIndex,
                 int bufferSize,
                 int dbgMode,
                 const char* asynSuffix,
                 asynPortDriver *asynPort) {
                   // prepare data buffers
    bufferSize_             = bufferSize;
    buffer1_.data = new T[bufferSize_];
    buffer2_.data = new T[bufferSize_];
    memset(&buffer1_.data[0],0,sizeof(T)*bufferSize_);
    memset(&buffer2_.data[0],0,sizeof(T)*bufferSize_);
    buffer1_.dataCounter    = 0;
    buffer1_.id             = 1;
    buffer2_.dataCounter    = 0;
    buffer2_.id             = 2;
    // add data to buffer
    bufferAdd_ = &buffer1_;
    // Buffer ready for writing to epics
    bufferWrite_ = &buffer2_;
    cfgDbgMode_             = dbgMode;
    destructs_              = 0;
    bufferSwitchMutex_      = epicsMutexCreate();  
    bufferIndex_            = bufferIndex;
    objIndex_               = objIndex;
    asynPort_               = asynPort;
    asynSuffix_             = strdup(asynSuffix);
    asynParamId_            = -1;
    enable_                 = true;
    
    initAsyn();
  }

  ~ecmcDataBuffer()  {
    delete[] buffer1_.data;
    delete[] buffer2_.data;
    free(asynSuffix_);
    destructs_ = 1;  // maybe need todo in other way..
  }

  void addData(T data)  {
    // Switch buffer if needed
    if(bufferAdd_->dataCounter >= bufferSize_) {
      switchBuffer();    
    }

    epicsMutexLock(bufferSwitchMutex_);
    bufferAdd_->data[bufferAdd_->dataCounter] = data;
    bufferAdd_->dataCounter++;
    epicsMutexUnlock(bufferSwitchMutex_);
  }

  void clear() {
    //Fill data buffer
    memset(&buffer1_.data[0],0,sizeof(T)*bufferSize_);
    memset(&buffer2_.data[0],0,sizeof(T)*bufferSize_);
    buffer1_.dataCounter = 0;
    buffer2_.dataCounter = 0;
  }

  void setEnable(bool enable) {
    enable_ = enable;
  }

  bool getBufferFull() {
    return bufferAdd_->dataCounter == bufferSize_;
  }
  
  void switchBuffer(){
    // ensure safe buffer switch
    epicsMutexLock(bufferSwitchMutex_);
    dataBuffer<T> *temp = bufferWrite_;
    bufferWrite_ = bufferAdd_;
    bufferAdd_   = temp;
    // start from 0 in new buffer
    bufferAdd_->dataCounter = 0;  
    epicsMutexUnlock(bufferSwitchMutex_);  
  }
 void writeBuffer();
 void initAsyn();

 private:

  static std::string to_string(int value){
    std::ostringstream os;
    os << value;
    return os.str();
  }

  int                   destructs_;
  int                   cfgDbgMode_;
  int                   bufferSize_;
  int                   bufferIndex_;
  int                   objIndex_;
  epicsMutexId          bufferSwitchMutex_;
  dataBuffer<T>         buffer1_;
  dataBuffer<T>         buffer2_;
  dataBuffer<T>        *bufferAdd_;
  dataBuffer<T>        *bufferWrite_;
  asynPortDriver       *asynPort_;
  char                 *asynSuffix_;
  int                   asynParamId_;
  bool                  enable_;
};

// specialized for epicsInt8
template<> inline void ecmcDataBuffer<epicsInt8>::writeBuffer() {
    epicsMutexLock(bufferSwitchMutex_);
    // Write asyn
    asynPort_->lock();
    /*asynStatus stat=*/ asynPort_->doCallbacksInt8Array(&bufferWrite_->data[0], bufferSize_, asynParamId_,0);
    
    asynPort_->unlock();
  
    epicsMutexUnlock(bufferSwitchMutex_);
}

// specialized for epicsInt16
template<> inline void ecmcDataBuffer<epicsInt16>::writeBuffer() {
    epicsMutexLock(bufferSwitchMutex_);
    // Write asyn
    asynPort_->lock();
    /*asynStatus stat=*/ asynPort_->doCallbacksInt16Array(&bufferWrite_->data[0], bufferSize_, asynParamId_,0);
    
    asynPort_->unlock();
  
    epicsMutexUnlock(bufferSwitchMutex_);
}

// specialized for epicsInt32
template<> inline void ecmcDataBuffer<epicsInt32>::writeBuffer() {
    epicsMutexLock(bufferSwitchMutex_);
    // Write asyn
    asynPort_->lock();
    /*asynStatus stat=*/ asynPort_->doCallbacksInt32Array(&bufferWrite_->data[0], bufferSize_, asynParamId_,0);
    
    asynPort_->unlock();
  
    epicsMutexUnlock(bufferSwitchMutex_);
}

// specialized for epicsInt64
template<> inline void ecmcDataBuffer<epicsInt64>::writeBuffer() {
    epicsMutexLock(bufferSwitchMutex_);
    // Write asyn
    asynPort_->lock();
    /*asynStatus stat=*/ asynPort_->doCallbacksInt64Array(&bufferWrite_->data[0], bufferSize_, asynParamId_,0);
    
    asynPort_->unlock();

    epicsMutexUnlock(bufferSwitchMutex_);
}

// specialized for epicsFloat32
template<> inline void ecmcDataBuffer<epicsFloat32>::writeBuffer() {
    epicsMutexLock(bufferSwitchMutex_);
    // Write asyn
    asynPort_->lock();
    /*asynStatus stat=*/ asynPort_->doCallbacksFloat32Array(&bufferWrite_->data[0], bufferSize_, asynParamId_,0);
    
    asynPort_->unlock();

    epicsMutexUnlock(bufferSwitchMutex_);
}

// specialized for epicsFloat64
template<> inline void ecmcDataBuffer<epicsFloat64>::writeBuffer() {
    epicsMutexLock(bufferSwitchMutex_);
    // Write asyn
    asynPort_->lock();
    /*asynStatus stat=*/ asynPort_->doCallbacksFloat64Array(&bufferWrite_->data[0], bufferSize_, asynParamId_,0);
    
    asynPort_->unlock();

    epicsMutexUnlock(bufferSwitchMutex_);
}

template<> inline void ecmcDataBuffer<epicsInt8>::initAsyn() {
 
  std::string paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objIndex_) + 
             "." + std::string(asynSuffix_);
  if( asynPort_->createParam(0, paramName.c_str(), asynParamInt8Array, &asynParamId_ ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter rawdata");
  }
  // use buffer 1 for first callback
  writeBuffer();
}

template<> inline void ecmcDataBuffer<epicsInt16>::initAsyn() {
 
  std::string paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objIndex_) + 
             "." + std::string(asynSuffix_);
  if( asynPort_->createParam(0, paramName.c_str(), asynParamInt16Array, &asynParamId_ ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter rawdata");
  }
  // use buffer 1 for first callback
  writeBuffer();
}

template<> inline void ecmcDataBuffer<epicsInt32>::initAsyn() {
 
  std::string paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objIndex_) + 
             "." + std::string(asynSuffix_);
  if( asynPort_->createParam(0, paramName.c_str(), asynParamInt32Array, &asynParamId_ ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter rawdata");
  }
  // use buffer 1 for first callback
  writeBuffer();
}

template<> inline void ecmcDataBuffer<epicsInt64>::initAsyn() {
 
  std::string paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objIndex_) + 
             "." + std::string(asynSuffix_);
  if( asynPort_->createParam(0, paramName.c_str(), asynParamInt64Array, &asynParamId_ ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter rawdata");
  }
  // use buffer 1 for first callback
  writeBuffer();
}


template<> inline void ecmcDataBuffer<epicsFloat32>::initAsyn() {
 
  std::string paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objIndex_) + 
             "." + std::string(asynSuffix_);
  if( asynPort_->createParam(0, paramName.c_str(), asynParamFloat32Array, &asynParamId_ ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter rawdata");
  }
  // use buffer 1 for first callback
  writeBuffer();
}

template<> inline void ecmcDataBuffer<epicsFloat64>::initAsyn() {
 
  std::string paramName = ECMC_PLUGIN_ASYN_PREFIX "_" + to_string(objIndex_) + 
             "." + std::string(asynSuffix_);
  if( asynPort_->createParam(0, paramName.c_str(), asynParamFloat64Array, &asynParamId_ ) != asynSuccess ) {
    throw std::runtime_error("Failed create asyn parameter rawdata");
  }
  // use buffer 1 for first callback
  writeBuffer();
}

#endif  /* ECMC_DATA_BUFFER_WRITE_H_ */
