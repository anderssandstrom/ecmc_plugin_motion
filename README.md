ecmc_plugin_motion
======
Plugin designed for commisioning and troubleshooting of motion axes.
Motion data are sampled, buffered and exposed as epics as waveforms.

# Panel
```
# Plugin loaded once (MTN_ID defaults to 0)
caqtdm -macro "SYS=c6025a" ecmc_plugin_motion_main.ui 

# If loaded more times
caqtdm -macro "SYS=c6025a,MTN_ID=1" ecmc_plugin_motion_main.ui 
```
# Python panels
In tools directory.. WIP...



# PVs

The following PVs are created:
```
c6025a> dbgrep *Plg*
c6025a:Plg-Mtn0-SmpHz
c6025a:Plg-Mtn0-AxCmd-RB
c6025a:Plg-Mtn0-EnaCmd-RB
c6025a:Plg-Mtn0-Stat
c6025a:Plg-Mtn0-PosAct-Arr
c6025a:Plg-Mtn0-PosSet-Arr
c6025a:Plg-Mtn0-PosErr-Arr
c6025a:Plg-Mtn0-Time-Arr
c6025a:Plg-Mtn0-Ena-Arr
c6025a:Plg-Mtn0-EnaAct-Arr
c6025a:Plg-Mtn0-Bsy-Arr
c6025a:Plg-Mtn0-Exe-Arr
c6025a:Plg-Mtn0-TrjSrc-Arr
c6025a:Plg-Mtn0-EncSrc-Arr
c6025a:Plg-Mtn0-AtTrg-Arr
c6025a:Plg-Mtn0-ErrId-Arr
c6025a:Plg-Mtn0-Stat-Arr
```

# Plugin Report

```
Plugin info: 
  Index                = 1
  Name                 = ecmc_plugin_motion
  Description          = Motion plugin for commissioning of ecmc motion axes.
  Option description   = 
    DBG_PRINT=<1/0>     : Enables/disables printouts from plugin, default = disabled.
    AXIS=<axis id>      : Sets default source axis id.
    BUFFER_SIZE=<size>  : Data points to collect, default = 4096.
    RATE=<rate hz>      : Sampling rate in Hz
  Filename             = /gfa/.mounts/sls_ioc/modules/ecmc_plugin_motion/test/R7.0.7//lib/deb10-x86_64/libecmc_plugin_motion.so
  Config string        = AXIS=1;BUFFER_SIZE=2000;DBG_PRINT=0;ENABLE=1;
  Version              = 2
  Interface version    = 65536 (ecmc = 65536)
     max plc funcs     = 64
     max plc func args = 10
     max plc consts    = 64
  Construct func       = @0x7f0badafb780
  Enter realtime func  = @0x7f0badafb7c0
  Exit realtime func   = @0x7f0badafb770
  Realtime func        = @0x7f0badafb7a0
  Destruct func        = @0x7f0badafb760
  dlhandle             = @0x563c3aba7d00
  Plc functions:
  Plc constants:

```

# TODO
* Triggered mode
* Add control functionalities (step response)
* Fix python gui (and venv)
