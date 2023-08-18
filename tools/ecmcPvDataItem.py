

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
    
    def binaryRepr(self,data):
        localdata = data.astype(int)
        return(
        np.dstack((
        np.bitwise_and(localdata, 0b10000000000000000000000000000000) >> 31,
        np.bitwise_and(localdata, 0b1000000000000000000000000000000) >> 30,
        np.bitwise_and(localdata, 0b100000000000000000000000000000) >> 29,
        np.bitwise_and(localdata, 0b10000000000000000000000000000) >> 28,
        np.bitwise_and(localdata, 0b1000000000000000000000000000) >> 27,
        np.bitwise_and(localdata, 0b100000000000000000000000000) >> 26,
        np.bitwise_and(localdata, 0b10000000000000000000000000) >> 25,
        np.bitwise_and(localdata, 0b1000000000000000000000000) >> 24,
        np.bitwise_and(localdata, 0b100000000000000000000000) >> 23,
        np.bitwise_and(localdata, 0b10000000000000000000000) >> 22,
        np.bitwise_and(localdata, 0b1000000000000000000000) >> 21,
        np.bitwise_and(localdata, 0b100000000000000000000) >> 20,
        np.bitwise_and(localdata, 0b10000000000000000000) >> 19,
        np.bitwise_and(localdata, 0b1000000000000000000) >> 18,
        np.bitwise_and(localdata, 0b100000000000000000) >> 17,
        np.bitwise_and(localdata, 0b10000000000000000) >> 16,
        np.bitwise_and(localdata, 0b1000000000000000) >> 15,
        np.bitwise_and(localdata, 0b100000000000000) >> 14,
        np.bitwise_and(localdata, 0b10000000000000) >> 13,
        np.bitwise_and(localdata, 0b1000000000000) >> 12,
        np.bitwise_and(localdata, 0b100000000000) >> 11,
        np.bitwise_and(localdata, 0b10000000000) >> 10,
        np.bitwise_and(localdata, 0b1000000000) >> 9,
        np.bitwise_and(localdata, 0b100000000) >> 8,
        np.bitwise_and(localdata, 0b10000000) >> 7,
        np.bitwise_and(localdata, 0b1000000) >> 6,
        np.bitwise_and(localdata, 0b100000) >> 5,
        np.bitwise_and(localdata, 0b10000) >> 4,
        np.bitwise_and(localdata, 0b1000) >> 3,
        np.bitwise_and(localdata, 0b100) >> 2,
        np.bitwise_and(localdata, 0b10) >> 1,
        np.bitwise_and(localdata, 0b1)
        )).flatten() > 0)