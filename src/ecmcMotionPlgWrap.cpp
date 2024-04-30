/*************************************************************************\
* Copyright (c) 2023 Paul Scherrer Institute
* ecmc is distributed subject to a Software License Agreement found
* in file LICENSE that is included with this distribution. 
*
*  ecmcMotionPlgWrap.cpp
*
*  Created on: july 10, 2023
*      Author: anderssandstrom
*      Credits to  https://github.com/sgreg/dynamic-loading 
*
\*************************************************************************/

// Needed to get headers in ecmc right...
#define ECMC_IS_PLUGIN

#include <vector>
#include <stdexcept>
#include <string>
#include "ecmcMotionPlgWrap.h"
#include "ecmcMotionPlg.h"

#define ECMC_PLUGIN_MAX_PORTNAME_CHARS 64
#define ECMC_PLUGIN_PORTNAME_PREFIX "PLUGIN.MOTION"

static std::vector<ecmcMotionPlg*>  motionObjs;
static int                    motionObjCounter = 0;
static char                   portNameBuffer[ECMC_PLUGIN_MAX_PORTNAME_CHARS];

int createMotionObj(char* configStr) {

  // create new ecmcMotionPlg object
  ecmcMotionPlg* motionObj = NULL;

  // create asynport name for new object ()
  memset(portNameBuffer, 0, ECMC_PLUGIN_MAX_PORTNAME_CHARS);
  snprintf (portNameBuffer, ECMC_PLUGIN_MAX_PORTNAME_CHARS,
            ECMC_PLUGIN_PORTNAME_PREFIX "_%d", motionObjCounter);
  try {
    motionObj = new ecmcMotionPlg(motionObjCounter, configStr, portNameBuffer);
  }
  catch(std::exception& e) {
    if(motionObj) {
      delete motionObj;
    }
    printf("Exception: %s. Plugin will unload.\n",e.what());
    return ECMC_PLUGIN_MOTION_ERROR_CODE;
  }
  
  motionObjs.push_back(motionObj);
  motionObjCounter++;

  return 0;
}

void deleteAllMotionObjs() {
  for(std::vector<ecmcMotionPlg*>::iterator pMotionObj = motionObjs.begin(); pMotionObj != motionObjs.end(); ++pMotionObj) {
    if(*pMotionObj) {
      delete (*pMotionObj);
    }
  }
}

int  linkDataTomotionObjs() {
  for(std::vector<ecmcMotionPlg*>::iterator pMotionObj = motionObjs.begin(); pMotionObj != motionObjs.end(); ++pMotionObj) {
    if(*pMotionObj) {
      try {
        (*pMotionObj)->connectToDataSource();
      }
      catch(std::exception& e) {
        printf("Exception: %s. Plugin will unload.\n",e.what());
        return ECMC_PLUGIN_MOTION_ERROR_CODE;
      }
    }
  }
  return 0;
}

int enableMotionObj(int objIndex, int enable) {
  try {
    motionObjs.at(objIndex)->setEnable(enable);
  }
  catch(std::exception& e) {
    printf("Exception: %s. Motion object index out of range.\n",e.what());
    return ECMC_PLUGIN_MOTION_ERROR_CODE;
  }
  return 0;
}

int clearMotionObj(int objIndex) {
  try {
    motionObjs.at(objIndex)->clearBuffers();
  }
  catch(std::exception& e) {
    printf("Exception: %s. Motion object index out of range.\n",e.what());
    return ECMC_PLUGIN_MOTION_ERROR_CODE;
  }  
  return 0;
}

int triggMotionObj(int objIndex) {
  try {
    motionObjs.at(objIndex)->triggMotionObject();
  }
  catch(std::exception& e) {
    printf("Exception: %s. Motion object index out of range.\n",e.what());
    return ECMC_PLUGIN_MOTION_ERROR_CODE;
  }  
  return 0;
}

int executeMotionObjs() {

  for(std::vector<ecmcMotionPlg*>::iterator pMotionObj = motionObjs.begin(); pMotionObj != motionObjs.end(); ++pMotionObj) {
    if(*pMotionObj) {
      try {
        (*pMotionObj)->executeMotionObject();
      }
      catch(std::exception& e) {
        printf("Exception: %s. Plugin will unload.\n",e.what());
        return ECMC_PLUGIN_MOTION_ERROR_CODE;
      }
    }
  }
  return 0;
}
