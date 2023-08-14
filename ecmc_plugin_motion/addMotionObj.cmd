
#==============================================================================
# addMotionObj.cmd
#-------------- Information:
#- Description: ecmc_plugin_motion startup.cmd
#-
#- by Anders Sandström, Paul Scherrer Institute, 2023
#- email: anders.sandstroem@psi.ch
#-
#-###############################################################################
#-
#- Arguments
#- [mandatory]
#- PLUGIN_ID         = Plugin instansiation index, must be unique for each call
#-
#- [optional]
#- AX                = Axis id, default 1
#- BUFF_SIZE         = Buffer size, default 1000
#- DBG               = Debug mode, default 1
#- ENA               = Enable operation, default 1
#- REPORT            = Printout plugin details, default 1

#################################################################################

#- Load plugin: MOTION

#- Note: ECMC_PLG_MOTION_OBJ_INDEX is the index of motion object in motion plugin and not PLUGIN_ID.
#- First loaded object will therefore have index
epicsEnvSet(ECMC_PLG_MOTION_OBJ_INDEX,${ECMC_PLG_MOTION_OBJ_INDEX=0})

# Might need differet paths for PSI and ESS.. must check
epicsEnvSet(ECMC_PLUGIN_FILNAME,"$(ecmc_plugin_motion_DIR)/lib/${EPICS_HOST_ARCH=linux-x86_64}/libecmc_plugin_motion.so")
epicsEnvSet(ECMC_PLUGIN_CONFIG,"AXIS=${AX};BUFFER_SIZE=${BUFF_SIZE};DBG_PRINT=${DBG=1};ENABLE=${ENA=1};")
${SCRIPTEXEC} ${ecmccfg_DIR}loadPlugin.cmd, "PLUGIN_ID=${PLUGIN_ID},FILE=${ECMC_PLUGIN_FILNAME},CONFIG='${ECMC_PLUGIN_CONFIG}', REPORT=${REPORT=1}"

dbLoadRecords(${ecmc_plugin_motion_TEMPLATES}ecmcPluginMotion.template,"P=$(IOC):,INDEX=${ECMC_PLG_MOTION_OBJ_INDEX=0},NELM=${BUFF_SIZE=1000}")

#- Increase of index (need to keep track in order to load correct db)
ecmcEpicsEnvSetCalc("ECMC_PLG_MOTION_OBJ_INDEX" ,${ECMC_PLG_MOTION_OBJ_INDEX=0}+1)

