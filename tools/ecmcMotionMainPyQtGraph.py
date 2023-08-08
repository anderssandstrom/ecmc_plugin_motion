#*************************************************************************
# Copyright (c) 2020 European Spallation Source ERIC
# ecmc is distributed subject to a Software License Agreement found
# in file LICENSE that is included with this distribution. 
#
#   ecmcMtnMainGui.py
#
#  Created on: October 6, 2020
#      Author: Anders Sandström
#    
#  Plots two waveforms (x vs y) updates for each callback on the y-pv
#  
#*************************************************************************

import sys
import os
import epics
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
#import matplotlib
#matplotlib.use("Qt5Agg")
#from matplotlib.figure import Figure
#from matplotlib.animation import TimedAnimation
#from matplotlib.lines import Line2D
#from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
#from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
#import matplotlib.pyplot as plt 
import pyqtgraph as pg
import threading

# Allow buffering of 10s data, need to add setting for this
xMaxTime = 10

# List of pv names
pvlist = [ 'BuffSze',
           'ElmCnt',
           'PosAct-Arr',
           'PosSet-Arr',
           'PosErr-Arr',
           'Time-Arr',
           'Ena-Arr',
           'EnaAct-Arr',
           'Bsy-Arr',
           'Exe-Arr',
           'TrjSrc-Arr',
           'EncSrc-Arr',
           'AtTrg-Arr',
           'ErrId-Arr',
           'Mde-RB',
           'Cmd-RB',
           'Stat',
           'AxCmd-RB',
           'SmpHz-RB',
           'TrgCmd-RB',
           'EnaCmd-RB' ]

pvAnalog = ['PosAct-Arr',
            'PosSet-Arr',
            'PosErr-Arr',
            'ErrId-Arr']

pvBinary = ['Ena-Arr',
            'EnaAct-Arr',
            'Bsy-Arr',
            'Exe-Arr',
            'TrjSrc-Arr',
            'EncSrc-Arr',
            'AtTrg-Arr']

pvmiddlestring='Plg-Mtn'

class comSignal(QObject):
    data_signal = pyqtSignal(object)

class ecmcMtnMainGui(QtWidgets.QDialog):
    def __init__(self,prefix=None,mtnPluginId=None):        
        super(ecmcMtnMainGui, self).__init__()

        self.pvnames = {}
        self.pvs = {}
        self.pv_signal_cbs = {}
        self.data = {}
        self.datalength = {}
        self.plottedLineAnalog = {}
        self.plottedLineBinary = {}

        for pv in pvAnalog:
            self.plottedLineAnalog[pv] = None
        
        for pv in pvBinary:
            self.plottedLineBinary[pv] = None

        for pv in pvlist:
            self.data[pv] = None
            self.datalength[pv] = 0

        #Set some default plot colours
        self.plotColor={}
        # Analog
        #self.plotColor['PosAct-Arr']='g'
        #self.plotColor['PosSet-Arr']='b'
        #self.plotColor['PosErr-Arr']='k'
        #self.plotColor['ErrId-Arr']='r'
        
                
        # Binary
        #self.plotColor['Ena-Arr']='b'
        #self.plotColor['EnaAct-Arr']='c'
        #self.plotColor['Bsy-Arr']='r'
        #self.plotColor['Exe-Arr']='m'
        #self.plotColor['TrjSrc-Arr']='y'
        #self.plotColor['EncSrc-Arr']='k'
        #self.plotColor['AtTrg-Arr']='g'

        self.offline = False
        self.pvPrefixStr = prefix
        self.pvPrefixOrigStr = prefix  # save for restore after open datafile
        self.mtnPluginId = mtnPluginId
        self.mtnPluginOrigId = mtnPluginId
        self.allowSave = False
        self.path =  '.'
        self.unitAnalogY  = "[]"
        self.unitBinaryY  = "[]"
        self.labelBinaryY = "Binary"
        self.labelAnalogY = "Analog"
        self.title = ""
        #self.NMtn = 1024
        self.sampleRate = 1000
        self.sampleRateValid = False
        self.MtnYDataValid = False
        self.MtnXDataValid = False

        if prefix is None or mtnPluginId is None:
          self.offline = True
          self.pause = True
          self.data['EnaCmd-RB'] = False           
        else:
          #Check for connection else go offline
          self.buildPvNames()          
          connected = self.pvs['BuffSze'].wait_for_connection(timeout=2)
          if connected:
            self.offline = False
            self.pause = False
          else: 
            self.offline = True
            self.pause = True
            self.data['EnaCmd-RB'] = False          

        self.startupDone=False        
        self.pause = 0
        self.createWidgets()
        self.setStatusOfWidgets()
        self.resize(1000,850)
        return

    def createWidgets(self):
        #self.figure = plt.figure()
        #self.plottedLineAnalog = None
        #self.plottedLineBinary = None
        self.axAnalog = None
        self.axBinary = None
        #self.canvas = FigureCanvas(self.figure)   
        #self.toolbar = NavigationToolbar(self.canvas, self)
        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        #self.graphicsLayout = pg.GraphicsLayout()
        self.plotItemAnalog = self.graphicsLayoutWidget.addPlot(row=0,col=0)
        self.plotitemBinary = self.graphicsLayoutWidget.addPlot(row=1,col=0)
        self.pauseBtn = QPushButton(text = 'pause')
        self.pauseBtn.setFixedSize(100, 50)
        self.pauseBtn.clicked.connect(self.pauseBtnAction)        
        self.pauseBtn.setStyleSheet("background-color: green")
        self.openBtn = QPushButton(text = 'open data')
        self.openBtn.setFixedSize(100, 50)
        self.openBtn.clicked.connect(self.openBtnAction)
        self.saveBtn = QPushButton(text = 'save data')
        self.saveBtn.setFixedSize(100, 50)
        self.saveBtn.clicked.connect(self.saveBtnAction)
        self.enableBtn = QPushButton(text = 'enable Mtn')
        self.enableBtn.setFixedSize(100, 50)
        self.enableBtn.clicked.connect(self.enableBtnAction)
        self.triggBtn = QPushButton(text = 'trigg Mtn')
        self.triggBtn.setFixedSize(100, 50)
        self.triggBtn.clicked.connect(self.triggBtnAction)
        self.zoomBtn = QPushButton(text = 'auto zoom')
        self.zoomBtn.setFixedSize(100, 50)
        self.zoomBtn.clicked.connect(self.zoomBtnAction)
        self.modeCombo = QComboBox()
        self.modeCombo.setFixedSize(100, 50)
        self.modeCombo.currentIndexChanged.connect(self.newModeIndexChanged)
        self.modeCombo.addItem("CONT")
        self.modeCombo.addItem("TRIGG")    
        self.progressBar = QProgressBar()
        self.progressBar.reset()
        self.progressBar.setMinimum(0)
        self.progressBar.setMaximum(100) #100%
        self.progressBar.setValue(0)
        self.progressBar.setFixedHeight(20)
    
        # Fix layout
        self.setGeometry(300, 300, 900, 700)
  
        layoutVert = QVBoxLayout()
        #layoutVert.addWidget(self.toolbar) 
        
        #layoutVert.addWidget(self.canvas) 
        layoutVert.addWidget(self.graphicsLayoutWidget) 

        layoutControl = QHBoxLayout() 
        layoutControl.addWidget(self.pauseBtn)
        layoutControl.addWidget(self.enableBtn)
        layoutControl.addWidget(self.triggBtn)
        layoutControl.addWidget(self.modeCombo)
        layoutControl.addWidget(self.zoomBtn)
        layoutControl.addWidget(self.saveBtn)
        layoutControl.addWidget(self.openBtn)

        frameControl = QFrame(self)
        frameControl.setFixedHeight(70)
        frameControl.setLayout(layoutControl)

        layoutVert.addWidget(frameControl)
        layoutVert.addWidget(self.progressBar)
        self.setLayout(layoutVert)

    def setStatusOfWidgets(self):
        self.saveBtn.setEnabled(self.allowSave)
        if self.offline:
            self.enableBtn.setStyleSheet("background-color: grey")
            self.enableBtn.setEnabled(False)
            self.pauseBtn.setStyleSheet("background-color: grey")
            self.pauseBtn.setEnabled(False)
            self.modeCombo.setEnabled(False)
            self.triggBtn.setEnabled(False)
            self.setWindowTitle("ecmc Mtn Main plot: Offline")            
        else:
           self.modeCombo.setEnabled(True)
           # Check actual value of pvs
           enable = self.pvs['EnaCmd-RB'].get()
           if enable is None:
             print("pvs['EnaCmd-RB'].get() failed")
             return
           if(enable>0):
             self.enableBtn.setStyleSheet("background-color: green")
             self.data['EnaCmd-RB'] = True
           else:
             self.enableBtn.setStyleSheet("background-color: red")
             self.data['EnaCmd-RB'] = False
   
           #self.sourceStr = self.pvSource.get(as_string=True)
           #if self.sourceStr is None:
           #  print("pvSource.get() failed")
           #  return

           self.sampleRate = self.pvs['SmpHz-RB'].get()
           if self.sampleRate is None:              
              print("pvs['SmpHz-RB'].get() failed")
              return
           self.sampleRateValid = True
           
           # calc x Array
           step=1/self.sampleRate
           
           self.x = np.arange(-xMaxTime-step,0+step,step)
           print('x')
           print(self.x)

           self.data['Mde-RB'] = self.pvs['Mde-RB'].get()    
           if self.data['Mde-RB'] is None:
             print("pvs['Mde-RB'].get() failed")
             return

           self.modeStr = "NO_MODE"
           self.triggBtn.setEnabled(False) # Only enable if mode = TRIGG = 2
           if self.data['Mde-RB'] == 1:
               self.modeStr = "CONT"
               self.modeCombo.setCurrentIndex(self.data['Mde-RB']-1) # Index starta t zero
   
           if self.data['Mde-RB'] == 2:
               self.modeStr = "TRIGG"
               self.triggBtn.setEnabled(True)
               self.modeCombo.setCurrentIndex(self.data['Mde-RB']-1) # Index starta t zero
   
           self.setWindowTitle("ecmc Mtn Main plot: prefix=" + self.pvPrefixStr + " , mtnId=" + str(self.mtnPluginId) + 
                               ", rate=" + str(self.sampleRate))       

    def addData(self, pvName, values):
        # Check if first assignment
        if self.data[pvName] is None:            
            self.data[pvName] = values
            return
        
        self.data[pvName]=np.append(self.data[pvName],values)
        
        # check if delete in beginning is needed
        currcount = len(self.data[pvName])
        if self.sampleRateValid:          
          allowedcount = int(xMaxTime * self.sampleRate)
        else:
          print('Warning sample rate not defined, fallback to max 10000 values')
          allowedcount = 10000
        
        # remove if needed
        if currcount > allowedcount:
            self.data[pvName]=self.data[pvName][currcount-allowedcount:]
        
        self.datalength[pvName] = len(self.data[pvName])


    def buildPvNames(self):        
        # Pv names based on structure:  <prefix>Plugin-Mtn<mtnPluginId>-<suffixname>
        for pv in pvlist:
            self.pvnames[pv]=self.buildPvName(pv)
            if self.pvnames[pv] is None:
                raise RuntimeError("pvname must not be 'None'")
            if len(self.pvnames[pv])==0:
                raise RuntimeError("pvname must not be ''")
            self.pvs[pv] = epics.PV(self.pvnames[pv])
            self.pv_signal_cbs[pv] = comSignal()
            
            # Signal callbacks (update gui)
            # replace any '-' with '_' since '-' not allowed in funcion names
            sig_cb_func=getattr(self,'sig_cb_' + pv.replace('-','_'))
            self.pv_signal_cbs[pv].data_signal.connect(sig_cb_func)

            # Pv monitor callbacks
            mon_cb_func=getattr(self,'on_change_' + pv.replace('-','_'))
            self.pvs[pv].add_callback(mon_cb_func)                        

        QCoreApplication.processEvents()

    def buildPvName(self, suffixname):
        return self.pvPrefixStr + pvmiddlestring + str(self.mtnPluginId) + '-' + suffixname 
        
    ###### Pv monitor callbacks
    def on_change_BuffSze(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['BuffSze'].data_signal.emit(value)

    def on_change_ElmCnt(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['ElmCnt'].data_signal.emit(value)

    def on_change_PosAct_Arr(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['PosAct-Arr'].data_signal.emit(value)

    def on_change_PosSet_Arr(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):        
        self.pv_signal_cbs['PosSet-Arr'].data_signal.emit(value)

    def on_change_PosErr_Arr(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['PosErr-Arr'].data_signal.emit(value)

    def on_change_Time_Arr(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['Time-Arr'].data_signal.emit(value)

    def on_change_Ena_Arr(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['Ena-Arr'].data_signal.emit(value)

    def on_change_EnaAct_Arr(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['EnaAct-Arr'].data_signal.emit(value)

    def on_change_Bsy_Arr(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['Bsy-Arr'].data_signal.emit(value)

    def on_change_Exe_Arr(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['Exe-Arr'].data_signal.emit(value)

    def on_change_TrjSrc_Arr(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['TrjSrc-Arr'].data_signal.emit(value)

    def on_change_EncSrc_Arr(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['EncSrc-Arr'].data_signal.emit(value)

    def on_change_AtTrg_Arr(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['AtTrg-Arr'].data_signal.emit(value)

    def on_change_ErrId_Arr(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['ErrId-Arr'].data_signal.emit(value)

    def on_change_Mde_RB(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['Mde-RB'].data_signal.emit(value)

    def on_change_Cmd_RB(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['Cmd-RB'].data_signal.emit(value)

    def on_change_Stat(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['Stat'].data_signal.emit(value)

    def on_change_AxCmd_RB(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['AxCmd-RB'].data_signal.emit(value)

    def on_change_SmpHz_RB(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['SmpHz-RB'].data_signal.emit(value)

    def on_change_TrgCmd_RB(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['TrgCmd-RB'].data_signal.emit(value)

    def on_change_EnaCmd_RB(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
        self.pv_signal_cbs['EnaCmd-RB'].data_signal.emit(value)

#    def onChangePvMode(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
#        if self.pause: 
#            return
#        self.comSignalMode.data_signal.emit(value)
#
#    def onChangePvEnable(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
#        if self.pause: 
#            return
#        self.comSignalEnable.data_signal.emit(value)
#
#    def onChangeX(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
#        if self.pause: 
#            return
#        self.comSignalX.data_signal.emit(value)
#
#    def onChangePvSpectY(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
#        if self.pause: 
#            return
#        self.comSignalSpectY.data_signal.emit(value)        
#
#    def onChangePvrawData(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
#        if self.pause: 
#            return
#        self.comSignalRawData.data_signal.emit(value)    
#
#    def onChangePvBuffIdAct(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
#        if self.pause: 
#            return
#        self.comSignalBuffIdAct.data_signal.emit(value)

    ###### Signal callbacks
    def sig_cb_BuffSze(self,value):        
        self.data['BuffSze'] = value

    def sig_cb_ElmCnt(self,value):
        self.data['ElmCnt'] = value

    def sig_cb_PosAct_Arr(self,value):
        if(np.size(value)) > 0:
            self.MtnYDataValid = True
            self.addData('PosAct-Arr', value)                        

    def sig_cb_PosSet_Arr(self,value):
        self.addData('PosSet-Arr', value)

    def sig_cb_PosErr_Arr(self,value):
        self.addData('PosErr-Arr', value)

    def sig_cb_Time_Arr(self,value):
        if(np.size(value)) > 0:
            self.addData('Time-Arr', value)
            self.MtnXDataValid = True
        self.plotAll()
        return

    def sig_cb_Ena_Arr(self,value):
        self.addData('Ena-Arr', value)

    def sig_cb_EnaAct_Arr(self,value):
        self.addData('EnaAct-Arr', value)

    def sig_cb_Bsy_Arr(self,value):
        self.addData('Bsy-Arr', value)

    def sig_cb_Exe_Arr(self,value):
        self.addData('Exe-Arr', value)

    def sig_cb_TrjSrc_Arr(self,value):
        self.addData('TrjSrc-Arr', value)

    def sig_cb_EncSrc_Arr(self,value):
        self.addData('EncSrc-Arr', value)

    def sig_cb_AtTrg_Arr(self,value):
        self.addData('AtTrg-Arr', value)

    def sig_cb_ErrId_Arr(self,value):
        self.addData('ErrId-Arr', value)

    def sig_cb_Mde_RB(self,value):        
        if value < 1 or value> 2:
            self.modeStr = "NO_MODE"
            print('callbackFuncMode: Error Invalid mode.')
            return

        self.data['Mde-RB'] = value
        self.modeCombo.setCurrentIndex(self.data['Mde-RB']-1) # Index starta t zero
        
        if self.data['Mde-RB'] == 1:
            self.modeStr = "CONT"
            self.triggBtn.setEnabled(False) # Only enable if mode = TRIGG = 2
                        
        if self.data['Mde-RB'] == 2:
           self.modeStr = "TRIGG"
           self.triggBtn.setEnabled(True)        
        return

    def sig_cb_Cmd_RB(self,value):
        self.data['Cmd-RB'] = value

    def sig_cb_Stat(self,value):
        self.data['Stat'] = value

    def sig_cb_AxCmd_RB(self,value):
        self.data['AxCmd-RB'] = value

    def sig_cb_SmpHz_RB(self,value):
        self.data['SmpHz-RB'] = value

    def sig_cb_TrgCmd_RB(self,value):
        self.data['TrgCmd-RB'] = value

    def sig_cb_EnaCmd_RB(self,value):
        self.data['EnaCmd-RB'] = value

        self.data['EnaCmd-RB'] = value    
        if self.data['EnaCmd-RB']:
          self.enableBtn.setStyleSheet("background-color: green")
        else:
          self.enableBtn.setStyleSheet("background-color: red")
        self.data['EnaCmd-RB'] = value
        return


#    def callbackFuncSpectY(self, value):
#        if(np.size(value)) > 0:
#
#            self.spectY = value
#            self.MtnYDataValid = self.RawXDataValid
#            self.plotAll()            
#        return
#
#    def callbackFuncrawData(self, value):
#        if(np.size(value)) > 0:
#            if (self.data['Time-Arr'] is None or np.size(value) != np.size(self.rawdataY)) and self.sampleRateValid:
#                self.data['Time-Arr'] = np.arange(-np.size(value)/self.sampleRate, 0, 1/self.sampleRate)
#                self.RawXDataValid = True
#                
#            self.rawdataY = value
#            self.RawYDataValid = True
#            self.plotAll()
#        return
#
#    def callbackFuncBuffIdAct(self, value):
#        if self.NMtn is None:
#          return
#        if(self.NMtn>0):
#          self.progressBar.setValue(value/self.NMtn*100)
#          if value/self.NMtn*100 < 80 and value/self.NMtn*100 >1:
#            self.MtnYDataValid = False
#            self.RawYDataValid = False
#        return

    ###### Widget callbacks
    def pauseBtnAction(self):   
        self.pause = not self.pause
        if self.pause:
            self.pauseBtn.setStyleSheet("background-color: red")
        else:
            self.pvPrefixStr = self.pvPrefixOrigStr  # Restore if dataset  was opened
            self.mtnPluginId = self.mtnPluginOrigId  # Restore if dataset  was opened
            self.buildPvNames()

            self.pauseBtn.setStyleSheet("background-color: green")
            # Retrigger plots with newest values
            #self.comSignalSpectY.data_signal.emit(self.spectY)
            #self.comSignalRawData.data_signal.emit(self.rawdataY)
        return

    def enableBtnAction(self):
        self.data['EnaCmd-RB'] = not self.data['EnaCmd-RB']
        self.pvs['EnaCmd-RB'].put(self.data['EnaCmd-RB'])
        if self.data['EnaCmd-RB']:
          self.enableBtn.setStyleSheet("background-color: green")
        else:
          self.enableBtn.setStyleSheet("background-color: red")
        return

    def triggBtnAction(self):
        self.pvTrigg.put(True)
        return

    def zoomBtnAction(self):        
        if self.data['Time-Arr'] is None:
            return

        if self.data['PosAct-Arr'] is None:
            return
        
        self.plotAnalog(True)
        self.plotBinary(True)
        return

    def newModeIndexChanged(self,index):
        if index==0 or index==1:
            if not self.offline and self.pvs['Mde-RB'] is not None:
               self.pvs['Mde-RB'].put(index+1)
        return
    
    def openBtnAction(self):
        #if not self.offline:
        #   self.pause = 1  # pause while open if online
        #   self.pauseBtn.setStyleSheet("background-color: red")
        #   QCoreApplication.processEvents()
        #           
        #fname = QFileDialog.getOpenFileName(self, 'Open file', self.path, "Data files (*.npz)")
        #if fname is None:
        #    return
        #if np.size(fname) != 2:            
        #    return
        #if len(fname[0])<=0:
        #    return
        #self.path = os.path.dirname(os.path.abspath(fname[0]))     
        #
        #npzfile = np.load(fname[0])
#
        ## verify scope plugin
        #if npzfile['plugin'] != "Mtn":
        #    print ("Invalid data type (wrong plugin type)")
        #    return
        #
        ## File valid                 
        #self.data['Time-Arr']     = npzfile['rawdataX']        
        #self.rawdataY     = npzfile['rawdataY']        
        #self.dataX        = npzfile['spectX']          
        #self.spectY       = npzfile['spectY']                  
        #self.sampleRate   = npzfile['sampleRate']      
        #self.NMtn         = npzfile['NMtn']            
        #self.data['Mde-RB']         = npzfile['mode']            
        #self.pvPrefixStr  = str(npzfile['pvPrefixStr'])
        #self.mtnPluginId  = npzfile['mtnPluginId']
        #if 'unitRawY' in npzfile:
        #  self.unitAnalogY = str(npzfile['unitRawY'])
        #if 'unitSpectY' in npzfile:
        #  self.unitSpectY = str(npzfile['unitSpectY'])
        #if 'labelRawY' in npzfile:
        #  self.labelAnalogY = str(npzfile['labelRawY'])
        #if 'labelSpectY' in npzfile:
        #  self.labelSpectY = str(npzfile['labelSpectY'])                  
        #if 'title' in npzfile:
        #  self.title = str(npzfile['title'])
#
        #self.buildPvNames()
        #
        ## trigg draw
        #self.MtnYDataValid = True
        #self.MtnXDataValid = True
        #self.RawYDataValid = True
        #self.RawXDataValid = True
        #self.sampleRateValid = True


        #self.comSignalMode.data_signal.emit(self.data['Mde-RB'])
        #self.comSignalX.data_signal.emit(self.dataX)
        #self.comSignalSpectY.data_signal.emit(self.spectY)
        #self.comSignalRawData.data_signal.emit(self.rawdataY)
        
        #self.setStatusOfWidgets()
#
        #self.startupDone=True
        #self.zoomBtnAction()
        return

    def saveBtnAction(self):
        #fname = QFileDialog.getSaveFileName(self, 'Save file', self.path, "Data files (*.npz)")
        #if fname is None:
        #    return
        #if np.size(fname) != 2:            
        #    return
        #if len(fname[0])<=0:
        #    return
        ## Save all relevant data
        #np.savez(fname[0],
        #         plugin                   = "Mtn",
        #         rawdataX                 = self.data['Time-Arr'],
        #         rawdataY                 = self.rawdataY,
        #         spectX                   = self.dataX,
        #         spectY                   = self.spectY,
        #         sampleRate               = self.sampleRate,
        #         NMtn                     = self.NMtn,
        #         mode                     = self.data['Mde-RB'],
        #         pvPrefixStr              = self.pvPrefixStr,
        #         mtnPluginId              = self.mtnPluginId,
        #         unitRawY                 = self.unitAnalogY,
        #         unitSpectY               = self.unitSpectY,
        #         labelRawY                = self.labelAnalogY,
        #         labelSpectY              = self.labelSpectY,
        #         title                    = self.title
        #         )
#
        #self.path = os.path.dirname(os.path.abspath(fname[0]))

        return

    def plotAll(self):       
        if self.MtnYDataValid and self.MtnXDataValid:
            self.plotAnalog()
            self.plotBinary()
            self.MtnYDataValid = False
            self.RawYDataValid = False

    def plotAnalog(self, autozoom=False):
        if self.data['Time-Arr'] is None:
            print('Error: No data')
            return

        if self.data['PosAct-Arr'] is None:
            print('Error: No data')
            return

        # create an axis
        #if self.axAnalog is None:
        #   self.axAnalog = self.figure.add_subplot(211)
        #   self.axAnalog.set_xlim(-10,0)
        
        minimum_x=0
        # plot data 
        i = 1
        for pv in pvAnalog:
            
            if self.data[pv] is not None:
                x_len=len(self.x)
                y = self.data[pv]
                y_len=len(y)
                if self.plottedLineAnalog[pv] is None:
                     #self.plottedLineAnalog[pv].remove()
                     self.plottedLineAnalog[pv] = self.plotItemAnalog.plot(self.x[x_len-y_len:],y,pen=(i,len(pvAnalog)))

                #self.plottedLineAnalog[pv], = self.axAnalog.plot(self.x[x_len-y_len:],y,self.plotColor[pv])
                self.plottedLineAnalog[pv].setData(self.x[x_len-y_len:],y)
                minimum_x_temp=-y_len/self.sampleRate
                if minimum_x_temp < minimum_x:
                    minimum_x = minimum_x_temp

            else:
                print("Data null for pv: " + pv)

            i = i +1

        #self.axAnalog.grid(True)        
        #self.axAnalog.set_xlabel('Time [s]')
        #self.axAnalog.set_ylabel(self.labelAnalogY + ' ' + self.unitAnalogY)
        #self.axAnalog.set_title(self.title)

        if autozoom:
           ymin = np.min(self.data['PosAct-Arr'])
           ymax = np.max(self.data['PosAct-Arr'])
           # ensure different values
           if ymin == ymax:
               ymin=ymin-1
               ymax=ymax+1
           range = ymax - ymin
           ymax += range * 0.1
           ymin -= range * 0.1
           #xmin = np.min(self.data['Time-Arr'])
           xmin=minimum_x
           #xmax = np.max(self.data['Time-Arr'])
           xmax = 0
           if xmin == xmax:
               xmin = xmin - 1
               xmax = xmax + 1
           range = xmax - xmin
           xmax += range * 0.02
           xmin -= range * 0.02
           #self.axAnalog.set_ylim(ymin,ymax)
           #self.axAnalog.set_xlim(xmin,xmax)
    
        # refresh canvas 
        #self.canvas.draw()
        self.allowSave = True
        self.saveBtn.setEnabled(True)
        #self.axAnalog.autoscale(enable=False)

    def plotBinary(self, autozoom=False):
        return
        if self.data['Time-Arr'] is None:
            return

        #if self.data['PosAct-Arr'] is None:
        #    return

        # create an axis
        if self.axBinary is None:
           self.axBinary = self.figure.add_subplot(212)
           self.axBinary.set_xlim(-10,0)

        
        # plot data
        minimum_x = 0
        for pv in pvBinary:
            if self.plottedLineBinary[pv] is not None:
                self.plottedLineBinary[pv].remove()
            if self.data[pv] is not None:
                y = self.data[pv]
                y_len=len(y)
                x_len=len(self.x)                
                self.plottedLineBinary[pv], = self.axBinary.plot(self.x[x_len-y_len:],y,self.plotColor[pv])
                
                minimum_x_temp=-y_len/self.sampleRate
                if minimum_x_temp < minimum_x:
                    minimum_x = minimum_x_temp

            else:
                print("Data null for pv: " + pv)


        self.axBinary.grid(True)        
        self.axBinary.set_xlabel('Time [s]')
        self.axBinary.set_ylabel(self.labelBinaryY + ' ' + self.unitBinaryY)
        self.axBinary.set_title(self.title)

        if autozoom:
           ymin = -0.1
           ymax = 1.1
           # ensure different values
           if ymin == ymax:
               ymin=ymin-1
               ymax=ymax+1
           range = ymax - ymin
           ymax += range * 0.1
           ymin -= range * 0.1
           #xmin = np.min(self.data['Time-Arr'])
           xmin=minimum_x
           #xmax = np.max(self.data['Time-Arr'])
           xmax = 0
           if xmin == xmax:
               xmin = xmin - 1
               xmax = xmax + 1
           range = xmax - xmin
           xmax += range * 0.02
           xmin -= range * 0.02
           self.axBinary.set_ylim(ymin,ymax)
           self.axBinary.set_xlim(xmin,xmax)
    
        # refresh canvas 
        self.canvas.draw()
        self.allowSave = True
        self.saveBtn.setEnabled(True)
        self.axBinary.autoscale(enable=False)

def printOutHelp():
  print("ecmcMtnMainGui: Plots waveforms of Mtn data (updates on Y data callback). ")
  print("python ecmcMtnMainGui.py <prefix> <mtnId>")
  print("<prefix>:  Ioc prefix ('IOC_TEST:')")
  print("<mtnId> :  Id of mtn plugin ('0')")
  print("example : python ecmcMotionMainGui.py 'IOC_TEST:' '0'")
  print("Will connect to Pvs: <prefix>Plg-Mtn<mtnId>-*")

if __name__ == "__main__":
    import sys    
    prefix = None
    mtnid = None
    if len(sys.argv) == 1:
       prefix = None
       mtnid = None
    elif len(sys.argv) == 3:
       prefix = sys.argv[1]
       mtnid = int(sys.argv[2])
    else:
       printOutHelp()
       sys.exit()    
    app = QtWidgets.QApplication(sys.argv)
    window=ecmcMtnMainGui(prefix=prefix,mtnPluginId=mtnid)
    window.show()
    sys.exit(app.exec_())
