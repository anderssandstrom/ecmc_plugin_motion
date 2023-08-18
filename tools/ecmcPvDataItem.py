

import epics
import numpy as np
import time
import threading
from PyQt5.QtCore import *

class comSignal(QObject):
    data_signal = pyqtSignal(object)

class ecmcPvDataItem():
    def __init__(self,pvPrefix , pvSuffix, pluginId, bufferSize):
        self.pvPrefix = pvPrefix
        self.pvSuffix = pvSuffix
        self.pluginId = pluginId
        self.bufferSize = int(bufferSize)
        self.data = np.empty(self.bufferSize)
        self.allowDataCollection  = False
        self.extPvMonCallbackFunc = None
        self.extSigCallbackFunc   = None

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
            if hasattr(value, "__len__"): # Array
                self.addData(value)
            else: # Scalar                
                self.data = value
                self.datalength = 1

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
        #if pvSuffix == 'PosAct-Arr'
        #   print(values)

        if not self.allowDataCollection:
            return

        # Check if first assignment
        if self.data is None:            
            self.data = values
            return
        
        self.data = np.append(self.data,values)
        
        # check if delete in beginning is needed
        currcount = len(self.data)
        
        # remove if needed
        if currcount > self.bufferSize:
            self.data=self.data[currcount-self.bufferSize:]
        
        self.datalength = len(self.data)
    
    def setAllowDataCollection(self,allow):
        self.allowDataCollection = allow

    def regExtSigCallback(self, func):
        self.extSigCallbackFunc = func
    
    def regExtPvMonCallback(self, func):
        self.extPvMonCallbackFunc = func

    def pvGet(self):
        return self.pv.get()
    
    def pvPut(self,value):
        self.pv.put(value)
        self.data = value
    
    