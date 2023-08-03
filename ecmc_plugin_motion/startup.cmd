
#==============================================================================
# startup.cmd
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

# Only allow call startup.cmd once. if more objects are needed then use addMotionObj.cmd directlly.

#- add One motion plugin object, only run startup once
${ECMC_PLG_MOTION_INIT=""}${SCRIPTEXEC} $(ecmc_plugin_motion_DIR)addMotionObj.cmd "PLUGIN_ID=${PLUGIN_ID},AX=${AX=1},BUFF_SIZE=${BUFF_SIZE=1000},DBG=${DBG=1},ENA=${ENA=1},REPORT=${REPORT=1}"
 
epicsEnvSet("ECMC_PLG_MOTION_INIT" ,"#")
