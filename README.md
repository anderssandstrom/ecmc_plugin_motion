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

# TODO
Much ..

The following interfaces are not implemented resulting in annoying error printouts.
```
2024/04/30 16:00:24.923 c6025a:Plg-Mtn0-PosAct-Arr devAsynFloat64Array::callbackWfIn read error 
2024/04/30 16:00:24.923 c6025a:Plg-Mtn0-PosSet-Arr devAsynFloat64Array::callbackWfIn read error 
2024/04/30 16:00:24.923 c6025a:Plg-Mtn0-PosErr-Arr devAsynFloat64Array::callbackWfIn read error 
2024/04/30 16:00:24.923 c6025a:Plg-Mtn0-Time-Arr devAsynFloat64Array::callbackWfIn read error 
2024/04/30 16:00:24.923 c6025a:Plg-Mtn0-Ena-Arr devAsynInt8Array::callbackWfIn read error asynPortDriver:readArray not implemented
2024/04/30 16:00:24.923 c6025a:Plg-Mtn0-EnaAct-Arr devAsynInt8Array::callbackWfIn read error asynPortDriver:readArray not implemented
2024/04/30 16:00:24.923 c6025a:Plg-Mtn0-Bsy-Arr devAsynInt8Array::callbackWfIn read error asynPortDriver:readArray not implemented
2024/04/30 16:00:24.923 c6025a:Plg-Mtn0-Exe-Arr devAsynInt8Array::callbackWfIn read error asynPortDriver:readArray not implemented
2024/04/30 16:00:24.923 c6025a:Plg-Mtn0-TrjSrc-Arr devAsynInt8Array::callbackWfIn read error asynPortDriver:readArray not implemented
2024/04/30 16:00:24.923 c6025a:Plg-Mtn0-EncSrc-Arr devAsynInt8Array::callbackWfIn read error asynPortDriver:readArray not implemented
2024/04/30 16:00:24.923 c6025a:Plg-Mtn0-AtTrg-Arr devAsynInt8Array::callbackWfIn read error asynPortDriver:readArray not implemented
2024/04/30 16:00:24.923 c6025a:Plg-Mtn0-ErrId-Arr devAsynInt32Array::callbackWfIn read error asynPortDriver:readArray not implemented
2024/04/30 16:00:24.923 c6025a:Plg-Mtn0-Stat-Arr devAsynInt32Array::callbackWfIn read error asynPortDriver:readArray not implemented

2024/04/30 16:00:33.476 c6025a:Plg-Mtn0-AxCmd-RB devAsynInt32::processCallbackOutput process write error 
...
...

```
