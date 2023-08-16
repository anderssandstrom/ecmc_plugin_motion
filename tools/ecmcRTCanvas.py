
#*************************************************************************
# Copyright (c) 2020 European Spallation Source ERIC
# ecmc is distributed subject to a Software License Agreement found
# in file LICENSE that is included with this distribution. 
#
#  ecmcRTCanvas.py
#
#  Created on: July 6, 2020
#      Author: Anders Sandström
#    
#  Heavily inspired by: https://exceptionshub.com/real-time-plotting-in-while-loop-with-matplotlib.html
#
#***************************************************************************
import sys
import os
import epics
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
class ecmcRTCanvas(FigureCanvas, TimedAnimation):
    def __init__(self, title):
        self.pause = 0
        self.addedData = []
        self.exceptCount = 0
        self.autoZoom =  False
        print(matplotlib.__version__)
        # The data
        self.xlim = 1000
        self.n = np.linspace(-(self.xlim - 1), 0, self.xlim)
        self.y = (self.n * 0.0)
        # The window
        self.fig = Figure(figsize=(5,5), dpi=100)
        self.ax1 = self.fig.add_subplot(111)        
        # self.ax1 settings
        self.ax1.set_xlabel('samples')
        self.ax1.set_ylabel('data')
        self.ax1.set_title(title)
        self.line1 = Line2D([], [], color='blue')
        self.line1_tail = Line2D([], [], color='red', linewidth=2)
        self.line1_head = Line2D([], [], color='red', marker='o', markeredgecolor='r')
        self.ax1.add_line(self.line1)
        self.ax1.add_line(self.line1_tail)
        self.ax1.add_line(self.line1_head)
        self.ax1.set_xlim(-(self.xlim - 1),0)
        self.ax1.set_ylim(-100, 100)
        self.ax1.grid()
        self.firstUpdatedData = True
        FigureCanvas.__init__(self, self.fig)
        TimedAnimation.__init__(self, self.fig, interval = 50, blit = True)
        return


    def new_frame_seq(self):
        return iter(range(self.n.size))

    def setBufferSize(self, bufferSize):
        if bufferSize<1000 :
            print("Buffer size out of range: " + str(bufferSize))
            return
        fillValue = self.y[0]
        oldSize = self.xlim
        self.xlim = int(bufferSize)
        self.n = np.linspace(-(self.xlim - 1),0,self.xlim)        
        
        if self.xlim > oldSize:
            tempArray = np.full(self.xlim - oldSize,fillValue)
            self.y = np.concatenate((tempArray, self.y))
        else:
            self.y = self.y[oldSize-self.xlim:-1]

        self.ax1.set_xlim(-(self.xlim-1), 1)
        self.draw()


    def pauseUpdate(self):        
        if self.pause:
          self.pause = 0
        else:
          self.pause = 1

    def _init_draw(self):
        lines = [self.line1, self.line1_tail, self.line1_head]
        for l in lines:
            l.set_data([], [])
        return

    def addData(self, value):      
        if self.pause == 0:
            self.addedData.append(value)

        return

    def zoomAuto(self):
        bottom = np.min(self.y)
        top = np.max(self.y)
        # ensure different values
        if bottom == top:
            top = bottom +1
        self.ax1.clear()
        self.ax1.grid(b=True)
        range = top - bottom
        top += range * 0.1
        bottom -= range *0.1
        self.ax1.set_ylim(bottom,top)
        self.ax1.set_xlim(-(self.xlim-1), 1)        
        self.draw()        
        return
    
    def zoomLow(self, value):
        top = self.ax1.get_ylim()[1]
        bottom = value        
        self.ax1.set_ylim(bottom,top)
        self.draw()
        return

    def zoomHigh(self, value):
        bottom = self.ax1.get_ylim()[0]
        top = value
        self.ax1.set_ylim(bottom,top)
        self.draw()
        return

    def _step(self, *args):
        # Extends the _step() method for the TimedAnimation class.
        try:
            TimedAnimation._step(self, *args)
        except Exception as e:
            self.exceptCount += 1
            print(str(self.exceptCount))
            TimedAnimation._stop(self)
            pass

        return

    def getYLims(self):
        return self.ax1.get_ylim()

    def _draw_frame(self, framedata):
        margin = 1        
        while(len(self.addedData) > 0):
            self.y = np.roll(self.y, -1)
            self.y[-1] = self.addedData[0]
            if self.firstUpdatedData:                
                if len(self.addedData) > 0:
                    self.y[0:-1] = self.addedData[0] # Set entire array to start value
                    self.firstUpdatedData = False
                    self.zoomAuto()
            del(self.addedData[0])            
        
        self.line1.set_data(self.n[ 0 : self.n.size - margin ], self.y[ 0 : self.n.size - margin ])
        self.line1_tail.set_data(np.append(self.n[-10:-1 - margin], self.n[-1 - margin]), np.append(self.y[-10:-1 - margin], self.y[-1 - margin]))
        self.line1_head.set_data(self.n[-1 - margin], self.y[-1 - margin])
        self._drawn_artists = [self.line1, self.line1_tail, self.line1_head]        
        return

    def setYLabel(self,label):
        self.ax1.set_ylabel(label)
        self.draw()

    def setTitle(self,label):
        self.ax1.set_title(label)
        self.draw()
