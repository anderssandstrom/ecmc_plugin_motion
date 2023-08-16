#*************************************************************************
# Copyright (c) 2020 European Spallation Source ERIC
# ecmc is distributed subject to a Software License Agreement found
# in file LICENSE that is included with this distribution. 
#
#  ecmcTrend.py
#
#  Created on: July 6, 2020
#      Author: Anders Sandström
#    
#  Heavily inspired by: https://exceptionshub.com/real-time-plotting-in-while-loop-with-matplotlib.html
#
#*************************************************************************

import sys
import os
import ecmcRTCanvas
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

class ecmcTrend(QtWidgets.QDialog):
    def __init__(self):
        super(ecmcTrend, self).__init__()
        # Define the geometry of the main window
        self.setGeometry(300, 300, 900, 700)
        self.setWindowTitle("ecmc plot")
        self.main_frame= QtWidgets.QFrame(self)
        self.main_layout = QtWidgets.QHBoxLayout()

        self.left_frame = QFrame(self)
        self.left_layout = QVBoxLayout()

        self.right_frame = QFrame(self)
        self.right_layout = QVBoxLayout()
        
        # Manual zoom High
        self.zoomHigh_frame = QFrame(self)
        self.zoomHigh_layout = QGridLayout()
        self.lblYMax= QLabel(text = "y-max:")
        self.lineEditZoomHigh = QLineEdit(text = '100')
        self.lineEditZoomHigh.setFixedSize(100, 50)
        self.zoomHighBtn = QPushButton(text = '>')
        self.zoomHighBtn.setFixedSize(10, 50)
        self.zoomHighBtn.clicked.connect(self.zoomHighBtnAction)
        self.zoomHigh_layout.addWidget(self.lblYMax,0,0,alignment = Qt.AlignRight | Qt.AlignBottom)
        self.zoomHigh_layout.addWidget(self.lineEditZoomHigh,1,0,alignment = Qt.AlignRight | Qt.AlignTop)
        self.zoomHigh_layout.addWidget(self.zoomHighBtn,1,1,alignment = Qt.AlignLeft | Qt.AlignTop)
        self.zoomHigh_frame.setLayout(self.zoomHigh_layout)

        # Auto zoom
        self.zoomBtn = QPushButton(text = 'zoom auto')
        self.zoomBtn.setFixedSize(100, 50)
        self.zoomBtn.clicked.connect(self.zoomBtnAction)
        
        # Pause
        self.pauseBtn = QPushButton(text = 'pause')
        self.pauseBtn.setFixedSize(100, 50)
        self.pauseBtn.clicked.connect(self.pauseBtnAction)

        # Manual zoom Low
        self.zoomLow_frame = QFrame(self)
        self.zoomLow_layout = QGridLayout()
        self.lblYMin= QLabel(text = "y-min:")
        self.lineEditZoomLow = QLineEdit(text = '-100')
        self.lineEditZoomLow.setFixedSize(100, 50)        
        self.zoomLowBtn = QPushButton(text = '>')
        self.zoomLowBtn.setFixedSize(10, 50)
        self.zoomLowBtn.clicked.connect(self.zoomLowBtnAction)
        self.zoomLow_layout.addWidget(self.lblYMin,0,0,alignment = Qt.AlignRight | Qt.AlignBottom)
        self.zoomLow_layout.addWidget(self.lineEditZoomLow,1,0,alignment = Qt.AlignRight | Qt.AlignTop)
        self.zoomLow_layout.addWidget(self.zoomLowBtn,1,1,alignment = Qt.AlignLeft | Qt.AlignTop)
        self.zoomLow_frame.setLayout(self.zoomLow_layout)

        # Write PV
        self.pvPut_frame = QFrame(self)
        self.pvPut_layout = QGridLayout()
        self.lblYMin= QLabel(text = "Write PV:")
        self.lineEditpvPut = QLineEdit(text = '0')
        self.lineEditpvPut.setFixedSize(100, 50)        
        self.pvPutBtn = QPushButton(text = '>')
        self.pvPutBtn.setFixedSize(10, 50)
        self.pvPutBtn.clicked.connect(self.pvPutBtnAction)
        self.pvPut_layout.addWidget(self.lblYMin,0,0,alignment = Qt.AlignRight | Qt.AlignBottom)
        self.pvPut_layout.addWidget(self.lineEditpvPut,1,0,alignment = Qt.AlignRight | Qt.AlignTop)
        self.pvPut_layout.addWidget(self.pvPutBtn,1,1,alignment = Qt.AlignLeft | Qt.AlignTop)
        self.pvPut_frame.setLayout(self.pvPut_layout)

        # Buffer size
        self.bufferSize_frame = QFrame(self)
        self.bufferSize_layout = QGridLayout()
        self.lblBufferSize= QLabel(text = "Buffer size []")
        self.lineBufferSize = QLineEdit(text = '1000')
        self.lineBufferSize.setFixedSize(100, 50)
        self.setBufferSizeBtn = QPushButton(text = '>')
        self.setBufferSizeBtn.setFixedSize(10, 50)
        self.setBufferSizeBtn.clicked.connect(self.setBufferSizeBtnAction)
        self.bufferSize_layout.addWidget(self.lblBufferSize,0,0,alignment = Qt.AlignRight | Qt.AlignBottom) # row, col
        self.bufferSize_layout.addWidget(self.lineBufferSize, 1,0,alignment = Qt.AlignRight | Qt.AlignTop)
        self.bufferSize_layout.addWidget(self.setBufferSizeBtn, 1,1,alignment = Qt.AlignLeft | Qt.AlignTop)
        self.bufferSize_frame.setLayout(self.bufferSize_layout)


        self.spacerTop = QSpacerItem(100,50)
        self.spacerZoomUpper = QSpacerItem(100,10)
        self.spacerZoomLower = QSpacerItem(100,10)
        
        self.left_layout.addWidget(self.zoomHigh_frame)
        self.left_layout.addWidget(self.zoomBtn)        
        self.left_layout.addWidget(self.pauseBtn)        
        self.left_layout.addWidget(self.zoomLow_frame)
        self.left_layout.addWidget(self.pvPut_frame)

        # Place the matplotlib figure
        self.myFig = ecmcRTCanvas.ecmcRTCanvas("ecmc plot")
        self.myFig.setFixedSize(700,500 )
        self.toolbar = NavigationToolbar(self.myFig, self)
        self.right_layout.addWidget(self.toolbar)
        self.right_layout.addWidget(self.myFig)
        self.right_layout.addWidget(self.bufferSize_frame)
        self.lineEditZoomLow.setText(str(self.myFig.getYLims()[0]))
        self.lineEditZoomHigh.setText(str(self.myFig.getYLims()[1]))
        
        self.left_frame.setLayout(self.left_layout)
        self.right_frame.setLayout(self.right_layout)
        self.main_layout.addWidget(self.left_frame)
        self.main_layout.addWidget(self.right_frame)
        self.main_frame.setLayout(self.main_layout)

        return

    def setBufferSizeBtnAction(self):
        value = float(self.lineBufferSize.text())
        self.myFig.setBufferSize(value)

    def zoomBtnAction(self):        
        self.myFig.zoomAuto()
        return

    def zoomHighBtnAction(self):
        value = float(self.lineEditZoomHigh.text())
        self.myFig.zoomHigh(value)
        return

    def zoomLowBtnAction(self):
        value = float(self.lineEditZoomLow.text())
        self.myFig.zoomLow(value)
        return

    def pvPutBtnAction(self):
        value = float(self.lineEditpvPut.text())
        self.writePV(value)
        return        

    def pauseBtnAction(self):        
        self.myFig.pauseUpdate()
        return

    def lineEditHighAction(self):
        value = float(self.lineEditZoomHigh.text())
        self.myFig.zoomHigh(value)
        return

    def lineEditLowAction(self):
        value = float(self.lineEditZoomLow.text())
        self.myFig.zoomLow(value)
        return

    def addData_callbackFunc(self, value):
        self.myFig.addData(value)
        return

    def setYLabel(self,label):
        self.myFig.setYLabel(label)
    
    def setTitle(self,label):
        self.myFig.setTitle(label)
        self.setWindowTitle("ecmc plot: " + label)
    
    def enablePut(self,enable):
        self.pvPut_frame.setEnabled(enable)
        self.pvPutBtn.setEnabled(enable)
        self.lineEditpvPut.setEnabled(enable)
        QCoreApplication.processEvents()


