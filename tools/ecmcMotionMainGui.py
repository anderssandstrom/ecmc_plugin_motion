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
import matplotlib
matplotlib.use("Qt5Agg")
from matplotlib.figure import Figure
from matplotlib.animation import TimedAnimation
from matplotlib.lines import Line2D
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt 
import threading

# List of pv names
pvlist= [ 'BuffSze',
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

pvmiddlestring='Plg-Mtn'

class comSignal(QObject):
    data_signal = pyqtSignal(object)

class ecmcMtnMainGui(QtWidgets.QDialog):
    def __init__(self,prefix=None,mtnPluginId=None):        
        super(ecmcMtnMainGui, self).__init__()

        self.pvnames={}
        self.pvs={}
        self.pv_signal_cbs={}
        self.data={}
        for data in self.data:
            data = None;

        self.offline = False
        self.pvPrefixStr = prefix
        self.pvPrefixOrigStr = prefix  # save for restore after open datafile
        self.mtnPluginId = mtnPluginId
        self.mtnPluginOrigId = mtnPluginId
        self.allowSave = False
        self.path =  '.'
        self.unitRawY = "[]"
        self.unitSpectY = "[]"
        self.labelSpectY = "Amplitude"
        self.labelRawY = "Raw"
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
        self.figure = plt.figure()
        self.plottedLineSpect = None
        self.plottedLineRaw = None
        self.axSpect = None
        self.axAnalog = None
        self.canvas = FigureCanvas(self.figure)   
        self.toolbar = NavigationToolbar(self.canvas, self) 
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
        layoutVert.addWidget(self.toolbar) 
        layoutVert.addWidget(self.canvas) 

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

    def buildPvNames(self):
        print('HEHEHEHHEH')
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
           # dbgrep *Plg*Mtn*
        # IOC_TEST:Plg-Mtn0-BuffSze
        # IOC_TEST:Plg-Mtn0-ElmCnt
        # IOC_TEST:Plg-Mtn0-PosAct-Arr
        # IOC_TEST:Plg-Mtn0-PosSet-Arr
        # IOC_TEST:Plg-Mtn0-PosErr-Arr
        # IOC_TEST:Plg-Mtn0-Time-Arr
        # IOC_TEST:Plg-Mtn0-Ena-Arr
        # IOC_TEST:Plg-Mtn0-EnaAct-Arr
        # IOC_TEST:Plg-Mtn0-Bsy-Arr
        # IOC_TEST:Plg-Mtn0-Exe-Arr
        # IOC_TEST:Plg-Mtn0-TrjSrc-Arr
        # IOC_TEST:Plg-Mtn0-EncSrc-Arr
        # IOC_TEST:Plg-Mtn0-AtTrg-Arr
        # IOC_TEST:Plg-Mtn0-ErrId-Arr
        # IOC_TEST:Plg-Mtn0-Mde-RB
        # IOC_TEST:Plg-Mtn0-Cmd-RB
        # IOC_TEST:Plg-Mtn0-Stat
        # IOC_TEST:Plg-Mtn0-AxCmd-RB
        # IOC_TEST:Plg-Mtn0-SmpHz-RB
        # IOC_TEST:Plg-Mtn0-TrgCmd-RB
        # IOC_TEST:Plg-Mtn0-EnaCmd-RB

    def sig_cb_BuffSze(self,value):        
        self.data['BuffSze'] = value

    def sig_cb_ElmCnt(self,value):
        self.data['ElmCnt'] = value

    def sig_cb_PosAct_Arr(self,value):
        if(np.size(value)) > 0:
            self.MtnYDataValid = True
            self.data['PosAct-Arr'] = value
            #print('PosAct-Arr:')
            #print(self.data['PosAct-Arr'])

    def sig_cb_PosSet_Arr(self,value):
        self.data['PosSet-Arr'] = value

    def sig_cb_PosErr_Arr(self,value):
        self.data['PosErr-Ar'] = value

    def sig_cb_Time_Arr(self,value):
        if(np.size(value)) > 0:
            self.data['Time-Arr'] = value
            self.MtnXDataValid = True
        self.plotAll()
        return

    def sig_cb_Ena_Arr(self,value):
        self.data['Ena-Arr'] = value

    def sig_cb_EnaAct_Arr(self,value):
        self.data['EnaAct-Arr'] = value

    def sig_cb_Bsy_Arr(self,value):
        self.data['Bsy-Arr'] = value

    def sig_cb_Exe_Arr(self,value):
        self.data['Exe-Arr'] = value

    def sig_cb_TrjSrc_Arr(self,value):
        self.data['TrjSrc-Arr'] = value

    def sig_cb_EncSrc_Arr(self,value):
        self.data['EncSrc-Arr'] = value

    def sig_cb_AtTrg_Arr(self,value):
        self.data['AtTrg-Arr'] = value

    def sig_cb_ErrId_Arr(self,value):
        self.data['ErrId-Arr'] = value

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
        
        self.plotData(True)

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
        #  self.unitRawY = str(npzfile['unitRawY'])
        #if 'unitSpectY' in npzfile:
        #  self.unitSpectY = str(npzfile['unitSpectY'])
        #if 'labelRawY' in npzfile:
        #  self.labelRawY = str(npzfile['labelRawY'])
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
        #         unitRawY                 = self.unitRawY,
        #         unitSpectY               = self.unitSpectY,
        #         labelRawY                = self.labelRawY,
        #         labelSpectY              = self.labelSpectY,
        #         title                    = self.title
        #         )
#
        #self.path = os.path.dirname(os.path.abspath(fname[0]))

        return

    def plotAll(self):       
        if self.MtnYDataValid and self.MtnXDataValid:
          self.plotData()
          self.MtnYDataValid = False
          self.RawYDataValid = False

    ###### Plotting
   # def plotSpect(self, autozoom=False):
   #     if self.dataX is None:
   #         return
   #     if self.spectY is None:
   #         return
   #     
   #     # create an axis for spectrum
   #     if self.axSpect is None:
   #        self.axSpect = self.figure.add_subplot(212)
#
   #     # plot data 
   #     if self.plottedLineSpect is not None:
   #         self.plottedLineSpect.remove()
#
   #     self.plottedLineSpect, = self.axSpect.plot(self.dataX,self.spectY, 'b*-') 
   #     self.axSpect.grid(True)
#
#
   #     self.axSpect.set_xlabel("Frequency [Hz]")
   #     self.axSpect.set_ylabel(self.labelSpectY + ' ' +self.unitSpectY)        
#
   #     if autozoom:
   #        ymin = np.min(self.spectY)
   #        ymax = np.max(self.spectY)
   #        # ensure different values
   #        if ymin == ymax:
   #            ymin = ymin - 1
   #            ymax = ymax + 1   
   #        range = ymax - ymin
   #        ymax += range * 0.1
   #        ymin -= range * 0.1
   #        xmin = np.min(self.dataX)
   #        xmax = np.max(self.dataX)
   #        if xmin == xmax:
   #            xmin = xmin - 1
   #            xmax = xmax + 1
   #        range = xmax - xmin
   #        xmax += range * 0.02
   #        xmin -= range * 0.02
   #        self.axSpect.set_ylim(ymin,ymax)
   #        self.axSpect.set_xlim(xmin,xmax)
#
   #     # refresh canvas 
   #     self.canvas.draw()
   #     self.axSpect.autoscale(enable=False)
#
    def plotData(self, autozoom=False):
        if self.data['Time-Arr'] is None:
            return

        if self.data['PosAct-Arr'] is None:
            return

        # create an axis
        if self.axAnalog is None:
           self.axAnalog = self.figure.add_subplot(211)

        # plot data 
        if self.plottedLineRaw is not None:
            self.plottedLineRaw.remove()
        self.plottedLineRaw, = self.axAnalog.plot(self.data['Time-Arr'],self.data['PosAct-Arr'], 'b*-') 
        
        self.axAnalog.grid(True)        
        self.axAnalog.set_xlabel('Time [s]')
        self.axAnalog.set_ylabel(self.labelRawY + ' ' + self.unitRawY)
        self.axAnalog.set_title(self.title)

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
           xmin = np.min(self.data['Time-Arr'])
           xmax = np.max(self.data['Time-Arr'])
           if xmin == xmax:
               xmin = xmin - 1
               xmax = xmax + 1
           range = xmax - xmin
           xmax += range * 0.02
           xmin -= range * 0.02
           self.axAnalog.set_ylim(ymin,ymax)
           self.axAnalog.set_xlim(xmin,xmax)
    
        # refresh canvas 
        self.canvas.draw()
        self.allowSave = True
        self.saveBtn.setEnabled(True)
        self.axAnalog.autoscale(enable=False)

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