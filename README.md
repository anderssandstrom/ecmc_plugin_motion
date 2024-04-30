ecmc_plugin_motion
======
Plugin designed for commisioning and troubleshooting of motion axes.
Motion data are sampled, buffered and exposed to epics as waveforms.

# Panel
```
# Plugin loaded once (MTN_ID defaults to 0)
caqtdm -macro "SYS=c6025a" ecmc_plugin_motion_main.ui 

# If loaded more times
caqtdm -macro "SYS=c6025a,MTN_ID=1" ecmc_plugin_motion_main.ui 
```

# Python panels
In tools directory is WIP.
