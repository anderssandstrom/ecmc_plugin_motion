/*************************************************************************\
* Copyright (c) 2023 Paul Scherrer Institute
* ecmc is distributed subject to a Software License Agreement found
* in file LICENSE that is included with this distribution. 
*
*  ecmcMotionPlgWrap.h
*
*  Created on: july 10, 2023
*      Author: anderssandstrom
*
\*************************************************************************/
#ifndef ECMC_MOTION_PLG_WRAP_H_
#define ECMC_MOTION_PLG_WRAP_H_
#include "ecmcMotionPlgDefs.h"

# ifdef __cplusplus
extern "C" {
# endif  // ifdef __cplusplus

/** \brief Create new Motion object
 *
 *  The plugin supports creation of multiple Motion objects\n
 *  (if loaded several times).\n
 *  The different fft are adressed by fftindex (in other functions below).\n
 *  The first loaded fft get index 0 and then increases for each load.\n
 *  This function call will create the custom asynparameters dedicated for this plugin.\
 *  The configuration string needs to define a data source by:\n
 *  "SOURCE=<data source>;"\n
 *  Example:\n
 *  "SOURCE=ec0.s1.AI_1";\n
 *  \param[in] configStr Configuration string.\n
 *
 *  \return 0 if success or otherwise an error code.\n
 */
int         createMotionObj(char *configStr);

/** \brief Enable/disable Motion object
 *
 *  Enable/disable Motion object. If disabled no data will be acquired\n
 *  and no calculations will be made.\n
 *  \param[in] fftIndex Index of fft (first loaded fft have index 0 then increases)\n
 *  \param[in] enable enable/disable (1/0).\n
 *
 *  \return 0 if success or otherwise an error code.\n
 */
int         enableMotionObj(int objIndex, int enable);

/** \brief Clear FFT object\n
 *
 *  Clears buffers. After this command the acquistion can start from scratch.\n
 *  \param[in] fftIndex Index of fft (first loaded fft have index 0 then increases)\n
 *
 *  \return 0 if success or otherwise an error code.\n
 */
int         clearMotionObj(int objIndex);

/** \brief Set mode of FFT object
 *
 *  The FFT object can measure in two differnt modes:\n
 *    CONT(1) : Continious measurement (Acq data, calc, then Acq data ..)\n
 *    TRIGG(2): Measurements are triggered from plc or over asyn and is only done once (untill next trigger)\n
 *  \param[in] fftIndex Index of fft (first loaded fft have index 0 then increases)\n
 *  \param[in] mode Mode CONT(1) or TRIGG(2)\n
 *
 *  \return 0 if success or otherwise an error code.\n
 */
//int         modeMotionObj(int objIndex, FFT_MODE mode);

/** \brief Trigger FFT object\n
 *
 *  If in triggered mode a new measurment cycle is initiated (fft will be cleared first).\n
 *  \param[in] fftIndex Index of fft (first loaded fft have index 0 then increases)\n
 *
 *  \return 0 if success or otherwise an error code.\n
 */
int         triggMotionObj(int objIndex);


/** \brief execute FFT object\n
 *
 *  If in triggered mode a new measurment cycle is initiated (fft will be cleared first).\n
 *  \param[in] fftIndex Index of fft (first loaded fft have index 0 then increases)\n
 *
 *  \return 0 if success or otherwise an error code.\n
 */
int         executeMotionObjs();

/** \brief Link data to _all_ fft objects
 *
 *  This tells the FFT lib to connect to ecmc to find it's data source.\n
 *  This function should be called just before entering realtime since then all\n
 *  data sources in ecmc will be definded (plc sources are compiled just before runtime\n
 *  so are only fist accesible now).\n
 *  \return 0 if success or otherwise an error code.\n
 */
int  linkDataTomotionObjs();

/** \brief Deletes all created fft objects\n
 *
 * Should be called when destructs.\n
 */

void deleteAllMotionObjs();

# ifdef __cplusplus
}
# endif  // ifdef __cplusplus

#endif  /* ECMC_MOTION_PLG_WRAP_H_ */
