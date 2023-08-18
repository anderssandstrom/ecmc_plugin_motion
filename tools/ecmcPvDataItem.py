

import epics
import numpy as np
import time
import threading

class comSignal(QObject):
    data_signal = pyqtSignal(object)

class dataItem():
    def __init__(self,pvPrefix , pvSuffix, pluginId, sampleRateHz, maxTimeSeconds):
        self.pvPrefix = pvPrefix
        self.pvSuffix = pvSuffix
        self.sampleRateHz = sampleRateHz
        self.pluginId = pluginId
        self.maxTimeSeconds = maxTimeSeconds
        self.maxElements = int(self.maxTimeSeconds * self.sampleRateHz)        
        self.data = {}
        self.allowDataCollection = False

        self.pvName   = self.pvPrefix + str(self.pluginId) + '-' + self.pvSuffix
        if self.pvName is None:
            raise RuntimeError("pvname must not be 'None'")
        if len(self.pvName) == 0:
            raise RuntimeError("pvname must not be ''")
        
        # Signals
        self.pvSignalCallback = comSignal()        
        self.pvSignalCallback.data_signal.connect(self.sigCallback)
        
        # pv monitor callback
        self.pv = epics.PV(self.pvName)
        self.pv.add_callback(self.pvMonCallback)

        # Signal callbacks (update gui)
    def sigCallback(self, value):
        if value is not None:
            if len(value) > 1: # Array
                self.addData(value)
            else: # Scalar                
                self.data = value
        
        # Call custom callback if needed
        if self.extSigCallbackFunc is not None:
            self.extSigCallbackFunc(value)

    # Pv monitor callbacks
    def pvMonCallback(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pvSignalCallback.data_signal.emit(value)

        # Call custom callback if needed
        if self.extPvMonCallbackFunc is not None:
            self.extPvMonCallbackFunc(pvname, value, char_value,timestamp, **kw)

    def getData(self):
        return self.data

    def addData(self, values):
        if not self.allowDataCollection:
            return

        # Check if first assignment
        if self.data is None:            
            self.data = values
            return
        
        self.data=np.append(self.data,values)
        
        # check if delete in beginning is needed
        currcount = len(self.data)
        
        # remove if needed
        if currcount > self.maxElements:
            self.data=self.data[currcount-self.maxElements:]
        
        self.datalength = len(self.data)
    
    def setAllowDataCollection(self,allow):
        self.allowDataCollection = allow

    def regExtSigCallback(self, func):
        self.extSigCallbackFunc = func
    
    def regExtPvMonCallback(self, func):
        self.extPvMonCallbackFunc = func

