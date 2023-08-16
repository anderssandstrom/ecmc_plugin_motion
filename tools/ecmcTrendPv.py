#*************************************************************************
# Copyright (c) 2020 European Spallation Source ERIC
# ecmc is distributed subject to a Software License Agreement found
# in file LICENSE that is included with this distribution. 
#
#   ecmcTrendPv.py
#
#  Created on: July 6, 2020
#      Author: Anders Sandström
#    
#  Heavily inspired by: https://exceptionshub.com/real-time-plotting-in-while-loop-with-matplotlib.html
#
#  Extends the ecmcTrend class will epics pv callbacks
#  
#*************************************************************************

import sys
import os
import epics
import ecmcTrend
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import functools
import numpy as np
import random as rd
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.figure import Figure
from matplotlib.animation import TimedAnimation
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import time
import threading


class comTrend(QObject):
    data_signal = pyqtSignal(float)


class ecmcTrendPv(ecmcTrend.ecmcTrend):
    def __init__(self,pvName=None):        
        super(ecmcTrendPv, self).__init__()        
        self.comTrend = comTrend()        
        self.comTrend.data_signal.connect(self.addData_callbackFunc) # update trend
        self.startval = 0
        self.pvName = pvName
        self.connectPv(self.pvName) # Epics
        self.setTitle(pvName)
        return

    def connectPv(self, pvname):
        if pvname is None:            
            raise RuntimeError("pvname must not be 'None'")
            if len(pvname)==0:
                raise RuntimeError("pvname must not be ''")
        self.pv = epics.PV(self.pvName)
        self.startval = self.pv.get()
        self.pv.add_callback(self.onChangePv)
        self.myFig.addData(self.startval)
        QCoreApplication.processEvents()
    
    def onChangePv(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.comTrend.data_signal.emit(value)

    def writePV(self,value):
        self.pv.put(value)
        self.myFig.addData(value)
