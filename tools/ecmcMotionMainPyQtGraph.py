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
import epics
from PyQt5.QtWidgets import *
from PyQt5 import QtWidgets
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
from ecmcOneMotorGUI import *
import pyqtgraph as pg
from ecmcPvDataItem import *
from ecmcParseAxisStatusWord import *

# Allow buffering of 10s data, need to add setting for this
xMaxTime = 10

# List of pv names
pvlist = [ 'BuffSze',
           'ElmCnt',
           'PosAct-Arr',
           'PosSet-Arr',
           'PosErr-Arr',
           'Time-Arr',
#           'Ena-Arr',
#           'EnaAct-Arr',
#           'Bsy-Arr',
#           'Exe-Arr',
#           'TrjSrc-Arr',
#           'EncSrc-Arr',
#           'AtTrg-Arr',
           'ErrId-Arr',
           'Stat-Arr',
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
            'ErrId-Arr',
            'Stat-Arr']

pvAnaPLotsDefaultEnabled = ['PosAct-Arr',
                            'PosSet-Arr',
                            'PosErr-Arr']

pvBinPLotsDefaultEnabled = ['enable',
                            'enabled',
                            'busy',
                            'attarget',
                            'moving']
pvBinBlock = ['instartup',
              'inrealtime',
              'axisType',
              'seqstate',
              'lastilock']

# MCU info PVs
pvAxisPrefixNamePart1 ='MCU-Cfg-AX'
pvAxisPrefixNamePart2 ='-Pfx'

pvAxisNamePart1 ='MCU-Cfg-AX'
pvAxisNamePart2 ='-Nam'

pvFistAxisIndexName = 'MCU-Cfg-AX-FrstObjId'
pvNextAxisIndexNamePart1 = 'MCU-Cfg-AX'
pvNextAxisIndexNamePart2 = '-NxtObjId'

pvmiddlestring='Plg-Mtn'

class ecmcMtnMainGui(QtWidgets.QDialog):
    def __init__(self,prefix="IOC_TEST:",mtnPluginId=0):
        super(ecmcMtnMainGui, self).__init__()
        self.pvItems           = {}
        self.parseAxisStatWd    = ecmcParseAxisStatusWord()  
        self.axisStatWdNames = self.parseAxisStatWd.getNames()    
        self.plottedLineAnalog = {}
        self.plottedLineBinary = {}
        self.pvAnalogDefaultCbState = {}
        self.pvBinaryDefaultCbState = {}
        self.dataStatWd = None
        self.bufferSize = 0
        for pv in pvlist:
            self.pvItems[pv] = None

        for pv in pvAnalog:
            self.plottedLineAnalog[pv] = None
            self.pvAnalogDefaultCbState[pv] = False
        
        for pv in self.axisStatWdNames:
            self.plottedLineBinary[pv] = None
            self.pvBinaryDefaultCbState[pv] = False
        
        for pv in pvBinPLotsDefaultEnabled:
            self.pvBinaryDefaultCbState[pv] = True

        for pv in pvAnaPLotsDefaultEnabled:
            self.pvAnalogDefaultCbState[pv] = True

        #Set some default plot colours
        self.plotColor = {}

        # Analog
        self.plotColor['PosAct-Arr'] = 'g'
        self.plotColor['PosSet-Arr'] = 'b'
        self.plotColor['PosErr-Arr'] = 'r'
        self.plotColor['ErrId-Arr']  = 'k'
        self.plotColor['Stat-Arr']   = 'm'
        
        self.checkboxColor={}
        self.checkboxColor['PosAct-Arr'] ='green'
        self.checkboxColor['PosSet-Arr'] ='blue'
        self.checkboxColor['PosErr-Arr'] ='red'
        self.checkboxColor['ErrId-Arr']  ='black'
        self.checkboxColor['Stat-Arr']   ='magenta'

        # Binary
        self.plotColor['Ena-Arr']    = 'b'
        self.plotColor['EnaAct-Arr'] = 'c'
        self.plotColor['Bsy-Arr']    = 'r'
        self.plotColor['Exe-Arr']    = 'm'
        self.plotColor['TrjSrc-Arr'] = 'y'
        self.plotColor['EncSrc-Arr'] = 'k'
        self.plotColor['AtTrg-Arr']  = 'g'

        self.checkboxColor['Ena-Arr']    = 'blue'
        self.checkboxColor['EnaAct-Arr'] = 'cyan'
        self.checkboxColor['Bsy-Arr']    = 'red'
        self.checkboxColor['Exe-Arr']    = 'magenta'
        self.checkboxColor['TrjSrc-Arr'] = 'yellow'
        self.checkboxColor['EncSrc-Arr'] = 'black'
        self.checkboxColor['AtTrg-Arr']  = 'green'

        self.offline = True
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

        self.sampleRate = 1000
        self.sampleRateValid = False
        self.MtnYDataValid = False
        self.MtnXDataValid = False

        if prefix is None or mtnPluginId is None:
          self.offline = True
          self.pause = True

        self.startupDone=False 
        self.pause = 0

        self.createWidgets()
        self.resize(1000,850)

        self.connectToEcmc()
        self.bufferSize = int(self.sampleRate*xMaxTime)
        self.initPVs(self.bufferSize)
    
        # read sample rate to bea able to deduce buffer size
        self.setStatusOfWidgets()
        return
   
    def connectToEcmc(self):

        # Check connection and read sample rate
        pvSampleRate = epics.PV(self.pvPrefixStr + pvmiddlestring + str(int(self.mtnPluginId))+ '-SmpHz-RB')
        connected = pvSampleRate.wait_for_connection(timeout = 2)                  
        if connected:
            print('Connected to ecmc')
            self.offline = False
            self.pause = False
            self.sampleRate = pvSampleRate.get()
            if self.sampleRate is None:              
                print("Read sample rate failed. fallback to 1000Hz")
                self.sampleRate = 1000
        else: 
            print('Not Connected')
            self.offline = True
            self.pause = True            

        self.sampleRateValid = True

        # calc x Array
        step=1/self.sampleRate           
        self.x = np.arange(-xMaxTime,0,step)

        # Read available axes
        self.readAxisList()
        
        
    def initPVs(self,bufferSize):
        for pvname in pvlist:
            if pvname in pvAnalog:
                self.pvItems[pvname] = ecmcPvDataItem(prefix + pvmiddlestring,pvname,self.mtnPluginId,bufferSize)
            else:
                self.pvItems[pvname] = ecmcPvDataItem(prefix + pvmiddlestring,pvname,self.mtnPluginId,1)
        
            self.pvItems[pvname].setAllowDataCollection(True)

        # register special callbacks
        self.pvItems['PosAct-Arr'].regExtSigCallback(self.sig_cb_PosAct_Arr)
        self.pvItems['Time-Arr'].regExtSigCallback(self.sig_cb_Time_Arr)
        self.pvItems['Mde-RB'].regExtSigCallback(self.sig_cb_Mde_RB)
        self.pvItems['AxCmd-RB'].regExtSigCallback(self.sig_cb_AxCmd_RB)
        self.pvItems['EnaCmd-RB'].regExtSigCallback(self.sig_cb_EnaCmd_RB)
        self.pvItems['Stat-Arr'].regExtSigCallback(self.sig_cb_Stat_Arr)

        # Example calls to ecmcPvDataItem:
        #self.testPV.regExtSigCallback(self.testSigCallback)
        #self.testPV.regExtPvMonCallback(self.testPVMonCallback)
        #self.testPV.setAllowDataCollection(True)

    def createWidgets(self):
        self.graphicsLayoutWidget = pg.GraphicsLayoutWidget()
        self.graphicsLayoutWidget.setBackground('w')
        self.plotItemAnalog = self.graphicsLayoutWidget.addPlot(row=0,col=0)        
        self.plotItemBinary = self.graphicsLayoutWidget.addPlot(row=1,col=0)
        self.plotItemBinary.setFixedHeight(150)
        self.plotItemBinary.setMouseEnabled(y=False)
        self.plotItemBinary.setLabel('bottom', 'Time [s]')
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
        self.setGeometry(300, 300, 1200, 900)

        frameMainLeft = QFrame(self)
        layoutVertMain = QVBoxLayout()

        # Bottom button section
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

        # Centre section
        framePlots = QFrame(self)
        layoutHorPlots = QHBoxLayout()
        framePlots.setLayout(layoutHorPlots)

        # Centre left
        layoutHorPlots.addWidget(self.graphicsLayoutWidget)
    
        # Centre right
        framePlotsSelection = QFrame(self)
        layoutVertPlotsSelection = QVBoxLayout()
        framePlotsSelection.setFixedWidth(150)
        
        # Centre right upper (analog selection)
        framePlotsSelectionUpper = QFrame(self)
        layoutVertPlotsSelection.setSpacing(0)
        layoutVertPlotsSelectionUpper = QVBoxLayout()
        anaSelectLabel = QLabel('Analog:')
        layoutVertPlotsSelectionUpper.addWidget(anaSelectLabel)

        self.checkBoxListAnalog={}
        for pv in pvAnalog:
            self.checkBoxListAnalog[pv] = QCheckBox(pv)
            self.checkBoxListAnalog[pv].setChecked(self.pvAnalogDefaultCbState[pv])
            self.checkBoxListAnalog[pv].setStyleSheet("color: " + self.checkboxColor[pv])
            layoutVertPlotsSelectionUpper.addWidget(self.checkBoxListAnalog[pv])
            self.checkBoxListAnalog[pv].toggled.connect(self.checkBoxStateChangedAnalog)

        layoutVertPlotsSelectionUpper.addSpacing(0)

        framePlotsSelectionUpper.setLayout(layoutVertPlotsSelectionUpper)
        layoutVertPlotsSelection.addWidget(framePlotsSelectionUpper)

        # Centre right lower (binary selection)
        framePlotsSelectionLower = QFrame(self)
        layoutVertPlotsSelectionLower = QVBoxLayout()
        binSelectLabel=QLabel('Binary:')
        layoutVertPlotsSelectionLower.addWidget(binSelectLabel)
        self.checkBoxListBinary={}
        
        i = 0
        for pv in self.axisStatWdNames:
            if pv in pvBinBlock:
                i += 1
                continue

            self.checkBoxListBinary[pv] = QCheckBox(pv)
            self.checkBoxListBinary[pv].setChecked(self.pvBinaryDefaultCbState[pv])
            color = pg.intColor(i)
            p = QPalette(color)
            p.setBrush(QPalette.WindowText,color)
            self.checkBoxListBinary[pv].setPalette(p)
            layoutVertPlotsSelectionLower.addWidget(self.checkBoxListBinary[pv])
            self.checkBoxListBinary[pv].toggled.connect(self.checkBoxStateChangedBinary)
            i += 1

        framePlotsSelectionLower.setLayout(layoutVertPlotsSelectionLower)

        layoutVertPlotsSelection.addSpacing(200)

        layoutVertPlotsSelection.addWidget(framePlotsSelectionLower)

        framePlotsSelection.setLayout(layoutVertPlotsSelection)
        layoutHorPlots.addWidget(framePlotsSelection)

        layoutVertMain.addWidget(framePlots)
        layoutVertMain.addWidget(frameControl)
        layoutVertMain.addWidget(self.progressBar)
         
        frameMainLeft.setLayout(layoutVertMain)        

        frameMotion = QFrame(self)
        layoutMotionGrid = QGridLayout()
        frameMotion.setLayout(layoutMotionGrid)
        self.btnMotorRecord = QPushButton(text = 'Motor Record')
        self.btnMotorRecord.clicked.connect(self.openMotorRecordPanel)
        self.btnMotorRecord.setFixedSize(100, 50)
        layoutMotionGrid.addWidget(self.btnMotorRecord,0,0)

        label = QLabel('Axis id:')
        self.cmbBxSelectAxis = QComboBox()
        self.cmbBxSelectAxis.currentIndexChanged.connect(self.changeAxisIndex)

        layoutMotionGrid.addWidget(label,1,0)
        layoutMotionGrid.addWidget(self.cmbBxSelectAxis,1,1)


        layoutVertMain.addWidget(frameMotion)
        layoutMain = QHBoxLayout()
        layoutMain.addWidget(frameMainLeft)
        layoutMain.addWidget(frameMotion)

        self.setLayout(layoutMain)

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
            enable = self.pvItems['EnaCmd-RB'].pvGet()
            if enable is None:
                print("pvs['EnaCmd-RB'].get() failed")
                return
            if(enable>0):
                self.enableBtn.setStyleSheet("background-color: green")                
            else:
                self.enableBtn.setStyleSheet("background-color: red")                
          
            # Mode
            self.mode = self.pvItems['Mde-RB'].pvGet()    
            if self.mode is None:
                print("pvs['Mde-RB'].get() failed")
            self.modeStr = "NO_MODE"

            self.triggBtn.setEnabled(False) # Only enable if mode = TRIGG = 2
            if self.mode == 1:
                self.modeStr = "CONT"
                self.modeCombo.setCurrentIndex(self.pvItems['Mde-RB'].getData()-1) # Index start at zero
    
            if self.mode == 2:
                self.modeStr = "TRIGG"
                self.triggBtn.setEnabled(True)
                self.modeCombo.setCurrentIndex(self.pvItems['Mde-RB'].getData()-1) # Index start at zero
            

            self.setWindowTitle("ecmc Mtn Main plot: prefix=" + self.pvPrefixStr + " , mtnId=" + str(self.mtnPluginId) + 
                                ", rate=" + str(self.sampleRate))            

        QCoreApplication.processEvents()

    def sig_cb_PosAct_Arr(self,value):
        if(np.size(value)) > 0:
            self.MtnYDataValid = True            

    def sig_cb_Time_Arr(self,value):
        if(np.size(value)) > 0:
            self.MtnXDataValid = True
        self.plotAll()
        return

    def sig_cb_Mde_RB(self,value):        
        if value < 1 or value> 2:
            self.modeStr = "NO_MODE"
            print('callbackFuncMode: Error Invalid mode.')
            return

        self.modeCombo.setCurrentIndex(value-1) # Index starta t zero
        
        if value == 1:
            self.modeStr = "CONT"
            self.triggBtn.setEnabled(False) # Only enable if mode = TRIGG = 2
                        
        if value == 2:
           self.modeStr = "TRIGG"
           self.triggBtn.setEnabled(True)        
        return

    def sig_cb_AxCmd_RB(self,value):
        if value is None:
            return
        print('Axis Id Value: ' + str(value))

        id = self.cmbBxSelectAxis.findText(str(int(value)))
        if id >= 0:
            self.cmbBxSelectAxis.setCurrentIndex(id)

        axisPrefixPvName = self.pvPrefixStr + pvAxisPrefixNamePart1 + str(int(value)) + pvAxisPrefixNamePart2
        prefixPV = epics.PV(axisPrefixPvName)
        axisPrefix = prefixPV.get()
        if axisPrefix is not None:
            self.axisPrefix = axisPrefix

        axisNamePvName = self.pvPrefixStr + pvAxisNamePart1 + str(int(value)) + pvAxisNamePart2
        namePV = epics.PV(axisNamePvName)
        axisName = namePV.get()
        if axisName is not None:
            self.axisName = axisName

    def sig_cb_EnaCmd_RB(self,value):
        self.pvItems['EnaCmd-RB'].pvPut(value)
        if value:
          self.enableBtn.setStyleSheet("background-color: green")
        else:
          self.enableBtn.setStyleSheet("background-color: red")        
        return

    def sig_cb_Stat_Arr(self,value):

        data = self.parseAxisStatWd.convert(value)
        self.addStatWdData(data)

    def addStatWdData(self, values):

        # Check if first assignment
        if self.dataStatWd is None:            
            self.dataStatWd = values
            return
        
        self.dataStatWd = np.append(self.dataStatWd,values,axis=1)
        
        # check if delete in beginning is needed
        currcount = self.dataStatWd.shape[1]        
        
        # remove if needed
        if currcount > self.bufferSize:
            self.dataStatWd=self.dataStatWd[:,currcount-self.bufferSize:]
        
        self.dataStatWdlength = len(self.dataStatWd)

    # State chenge for Analog checkboxes
    def checkBoxStateChangedAnalog(self, int):
        # refresh plots
        self.plotAnalog()

    # State chenge for Binary checkboxes
    def checkBoxStateChangedBinary(self, int):
        # refresh plots
        self.plotBinary()
    
    def readAxisList(self):        
        axIdPV = epics.PV(self.pvPrefixStr + pvFistAxisIndexName)
        axId = axIdPV.get()        
        if axId is None:
            print('ERROR: First Axis Index PV not found.') 
            return

        self.cmbBxSelectAxis.clear()        
        self.cmbBxSelectAxis.addItem(str(int(axId)))
        
        while axId >= 0:
           # Get next axis id
           pvName = self.pvPrefixStr + pvNextAxisIndexNamePart1 + str(int(axId)) + pvNextAxisIndexNamePart2
           axIdPV = epics.PV(pvName)
           axId = axIdPV.get()
           
           if axId > 0:              
              self.cmbBxSelectAxis.addItem(str(int(ax)))

    def changeAxisIndex(self,xxx):
        if self.cmbBxSelectAxis.currentData() is not None:
            self.pvItems['AxCmd-RB'].pvPut(self.cmbBxSelectAxis.currentData(), use_complete=True)

    def openMotorRecordPanel(self,xxx):
        self.dialog = MotorPanel(self,self.axisPrefix ,self.axisName)
        self.dialog.resize(500, 900)
        self.dialog.show()

    ###### Widget callbacks
    def pauseBtnAction(self):   
        self.pause = not self.pause
        if self.pause:
            self.pauseBtn.setStyleSheet("background-color: red")
        else:
            self.pvPrefixStr = self.pvPrefixOrigStr  # Restore if dataset  was opened
            self.mtnPluginId = self.mtnPluginOrigId  # Restore if dataset  was opened            
            self.pauseBtn.setStyleSheet("background-color: green")

        return

    def enableBtnAction(self):
        
        currValue = self.pvItems['EnaCmd-RB'].getData()

        self.pvItems['EnaCmd-RB'].pvPut(not currValue)
        if self.pvItems['EnaCmd-RB'].getData():
          self.enableBtn.setStyleSheet("background-color: green")
        else:
          self.enableBtn.setStyleSheet("background-color: red")
        return

    def triggBtnAction(self):
        self.pvItems['TrgCmd-RB'].pvPut(True)        
        return

    def zoomBtnAction(self):
        if self.pvItems['Time-Arr'].getData() is None:
            return

        if self.pvItems['PosAct-Arr'].getData() is None:
            return
        
        self.plotAnalog(True)
        self.plotBinary(True)
        return

    def newModeIndexChanged(self,index):
        if self.pvItems is None:
           return
        
        if self.pvItems['Mde-RB'] is None:
           return
        
        if index==0 or index==1:
            if not self.offline and self.pvItems['Mde-RB'] is not None:
               self.pvItems['Mde-RB'].pvPut(index+1)
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
    
    def convertStatusWordToBits(self,statwd):
        print('test')


    def plotAnalog(self, autozoom=False):
        
        if self.pvItems['Time-Arr'].getData() is None:
            print('Error: No data')
            return

        if self.pvItems['PosAct-Arr'].getData() is None:
            print('Error: No data')
            return
       
        # plot data 
        minimum_x = 0
        for pv in pvAnalog:
            if self.pvItems[pv] is not None:
   
                y = self.pvItems[pv].getData()                
                if y is None:
                    print('Y is None')
                    continue
                if self.x is None:
                    print('X is None')
                    continue

                x_len=len(self.x)
                y_len=len(y)

                if self.checkBoxListAnalog[pv].isChecked():
                    if self.plottedLineAnalog[pv] is None:
                         plotpen=pg.mkPen(self.plotColor[pv],width=2)
                         self.plottedLineAnalog[pv] = self.plotItemAnalog.plot(self.x[x_len-y_len:],y,pen=plotpen)
                         self.plotItemAnalog.showGrid(x=True,y=True)
                    else:     
                        self.plottedLineAnalog[pv].setData(self.x[x_len-y_len:],y)
                        minimum_x_temp=-y_len/self.sampleRate
                        if minimum_x_temp < minimum_x:
                            minimum_x = minimum_x_temp
                else:
                    if self.plottedLineAnalog[pv] is not None:
                        self.plotItemAnalog.removeItem(self.plottedLineAnalog[pv])
                        self.plottedLineAnalog[pv] = None

        self.allowSave = True
        self.saveBtn.setEnabled(True)

    def plotBinary(self, autozoom=False):


        if self.dataStatWd is None:
            print('Error: No data')
            return
        if self.x is None:
            print('X is None')
            return
    
        # plot data
        minimum_x = 0
        x_len=len(self.x)

        i = 0

        for pv in self.axisStatWdNames:
            if pv in pvBinBlock:
                i += 1
                continue

            if self.checkBoxListBinary[pv].isChecked():
                y = self.dataStatWd[i,:]
                if y is None:
                    print('Y is None')
                    return
                
                y_len=len(y)

                if self.plottedLineBinary[pv] is None:
                    self.plottedLineBinary[pv] = self.plotItemBinary.plot(self.x[x_len-y_len:],self.dataStatWd[i,:],pen=pg.mkPen(i, width=2))
                    self.plotItemBinary.showGrid(x=True,y=True)
                    self.plotItemBinary.setXLink(self.plotItemAnalog)
                    self.plotItemBinary.setYRange(-0.1, 1.1, padding=0)        
                else:
                    self.plottedLineBinary[pv].setData(self.x[x_len-y_len:],self.dataStatWd[i,:])
                    minimum_x_temp=-y_len/self.sampleRate
                    if minimum_x_temp < minimum_x:
                        minimum_x = minimum_x_temp
            else:
                if self.plottedLineBinary[pv] is not None:
                    self.plotItemBinary.removeItem(self.plottedLineBinary[pv])
                    self.plottedLineBinary[pv] = None
            i += 1
        
        return

        #if autozoom:
        #    ymin = -0.1
        #    ymax = 1.1
        #    xmin = minimum_x
        #    xmax = 0
        #    if xmin == xmax:
        #        xmin = xmin - 1
        #        xmax = xmax + 1
        #    range = xmax - xmin
        #    xmax += range * 0.02
        #    xmin -= range * 0.02
        #    self.plotItemBinary.setYRange(ymin, ymax, padding=0)
        #    self.plotItemBinary.setXRange(xmin, xmax, padding=0)
        #
        #self.allowSave = True
        #self.saveBtn.setEnabled(True)

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

