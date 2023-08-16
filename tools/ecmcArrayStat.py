#!/usr/bin/python3.6
import sys
import epics
import numpy as np

from PyQt5 import QtCore,QtWidgets, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtCore import QObject
from PyQt5.QtGui import *

import random
import ecmcTrend
#import ecmcGraphWrapper as graphWrap
#import matplotlib as mpl
#mpl.use('Qt5Agg')
#import matplotlib.pyplot as plt
#import matplotlib.lines
from datetime import datetime
import threading


PARSE_ERROR_ELEMENT_COUNT_OUT_OF_RANGE = 1000
ELEMENT_COUNT = 30
TIMESTAMP_INDEX = 30
TREND_DEFAULT_INDEX = 2

ECMC_COMMAND = {
    'MOVE_VEL': 1,
    'MOVE_REL' :2,
    'MOVE_ABS' :3,
    'MOVE_HOME' :10,
}

DATASOURCE = {
    'AX_ID': 0,
    'POS_SET' :1,
    'POS_ACT' :2,
    'POS_ERR' :3,
    'POS_TARG' :4,
    'POS_ERR_TARG' :5,
    'POS_RAW' :6,
    'CNTRL_OUT' :7,
    'VEL_SET' :8,
    'VEL_ACT' :9,
    'VEL_FF_RAW' :10,
    'VEL_RAW' :11,
    'CYCLE_COUNTER' :12,
    'ERROR' :13,
    'COMMAND' :14,
    'CMD_DATA' :15,
    'SEQ_STATE' :16,
    'ILOCK' :17,
    'ILOCK_LAST_ACTIVE' :18,
    'TRAJ_SOURCE' :19,
    'ENC_SOURCE' :20,
    'ENABLE' :21,
    'ENABLED' :22,
    'EXECUTE' :23,
    'BUSY' :24,
    'AT_TAGEY' :25,
    'HOMED' :26,
    'LOW_LIM' :27,
    'HIGH_LIM' :28,
    'HOME_SENSOR' :29
    }

DESCRIPTION = [
    'axId',
    'posSet',
    'posAct',
    'posErr',
    'posTarg',
    'posErrTarg',
    'posRaw',
    'cntrlOut',
    'velSet',
    'velAct',
    'velFFraw',
    'velRaw',
    'cycleCounter',
    'error',
    'command',
    'cmdData',
    'seqState',
    'ilock',
    'ilockLastActive',
    'trajSource',
    'encSource',
    'enable',
    'enabled',
    'execute',
    'busy',
    'atTarget',
    'homed',
    'lowLim',
    'highLim',
    'homeSensor',
]
STYLES={
 'ArrayStat': '''
            QTableView{ 
                   background-color: white;
                   foreground-color: black;
                   font: bold;
                   width: 430px;
                   min-width: 430px;
                   max-width: 430px;
                   font-size:10pt;
                   height:750px;
                   min-height:750px;
                   max-height:750px;
                   }
                   '''
}

# You need to setup a signal slot mechanism, to
# send data to your GUI in a thread-safe way.
# Believe me, if you don't do this right, things
# go very very wrong..
class comTable(QObject):
    data_signal = pyqtSignal(str,float)

''' End Class '''
# You need to setup a signal slot mechanism, to
# send data to your GUI in a thread-safe way.
# Believe me, if you don't do this right, things
# go very very wrong..
class comTrend(QObject):
    data_signal = pyqtSignal(float)

''' End Class '''

class ecmcArrayStat(QtWidgets.QTableView):
  def __init__(self,parent=None):
    super(ecmcArrayStat, self).__init__(parent)
    self.background=None
    self.startToPlot=False; 
    self.axId=0
    self.posSet=0
    self.posAct=0
    self.posErr=0
    self.posTarg=0
    self.posErrTarg=0
    self.posRaw=0
    self.cntrlOut=0
    self.velSet=0
    self.velAct=0
    self.velFFraw=0
    self.velRaw=0
    self.cycleCounter=0
    self.error=0
    self.errorCode=0
    self.strTime=0
    self.command=0
    self.cmdData=0
    self.seqState=0
    self.ilock=0
    self.ilockLastActive=0
    self.trajSourc=0
    self.encSource=0
    self.enable=0
    self.enabled=0
    self.execute=0
    self.busy=0
    self.atTarget=0
    self.homed=0
    self.lowLim=0
    self.highLim=0
    self.homeSensor=0
    self.trendValue = 0
    self.trendDataIndex = TREND_DEFAULT_INDEX # Pos-Act
    self.dataList=[]
    self.dataSourceConvFuncPoint = {
      0 :self.defaultStrFunc,
      1 :self.defaultStrFunc,
      2 :self.defaultStrFunc,
      3 :self.defaultStrFunc,
      4 :self.defaultStrFunc,
      5 :self.defaultStrFunc,
      6 :self.defaultStrFunc,
      7 :self.defaultStrFunc,
      8 :self.defaultStrFunc,
      9 :self.defaultStrFunc,
      10 :self.defaultStrFunc,
      11 :self.defaultStrFunc,
      12 :self.defaultStrFunc,
      13 :self.errorFunc,
      14 :self.commandStrFunc,
      15 :self.cmdDataStrFunc,
      16 :self.defaultStrFunc,
      17 :self.iLockFunc,
      18 :self.iLockFunc,
      19 :self.sourceFunc,
      20 :self.sourceFunc,
      21 :self.defaultStrFunc,
      22 :self.defaultStrFunc,
      23 :self.defaultStrFunc,
      24 :self.busyFunc,
      25 :self.highOKLowNotOKFunc,
      26 :self.highOKLowNotOKFunc,
      27 :self.highOKLowNotOKFunc,
      28 :self.highOKLowNotOKFunc,
      29 :self.defaultStrFunc,
    }

    self.axisDiagPvName=""

    self.stdItemArrayName=[]
    self.stdItemArrayData=[]
    self.stdItemArraySelect=[]
    
    self.create_GUI()

    self.comTable = comTable()    
    self.comTable.data_signal.connect(self.updateGUI)

    self.comTrend = comTrend()
    self.comTrend.data_signal.connect(self.trend.addData_callbackFunc)
    return

  def create_GUI(self):
    self.table = QtWidgets.QTableView(self)  # SELECTING THE VIEW
    self.model = QtGui.QStandardItemModel(self)  # SELECTING THE MODEL - FRAMEWORK THAT HANDLES QUERIES AND EDITS
    self.table.setModel(self.model)  # SETTING THE MODEL    
    self.populate()    
    self.model.setHorizontalHeaderLabels(['Parameter', 'Value', ''])
    self.btnPlot=QtWidgets.QPushButton('Plot',default=False, autoDefault=False)    
    self.trend=ecmcTrend.ecmcTrend()
    # Disable put button
    self.trend.enablePut(False)
    self.trend.setTitle("ecmc plot")
    self.show()

  def populate(self):
    for i in range(0,ELEMENT_COUNT):
      row= []
      cell=QtGui.QStandardItem(DESCRIPTION[i])
      cell.setFlags(QtCore.Qt.ItemIsEditable)
      cell.setBackground(QtGui.QBrush(QtCore.Qt.white))
      cell.setForeground(QtGui.QBrush(QtCore.Qt.black))
      self.stdItemArrayName.append(cell)
      row.append(cell)
      cell=QtGui.QStandardItem('value'+str(i))
      cell.setFlags(QtCore.Qt.ItemIsEditable)
      cell.setBackground(QtGui.QBrush(QtCore.Qt.white))
      cell.setForeground(QtGui.QBrush(QtCore.Qt.black))      
      self.stdItemArrayData.append(cell)
      row.append(cell)            
      cell=QtGui.QStandardItem(True)
      cell.setCheckable(True)
      cell.setCheckState(QtCore.Qt.Unchecked)
      row.append(cell)            
      self.stdItemArraySelect.append(cell)
      self.model.appendRow(row)   

    #Timestamp
    row= []    
    cell=QtGui.QStandardItem("Timestamp")
    cell.setFlags(QtCore.Qt.ItemIsEditable)
    cell.setBackground(QtGui.QBrush(QtCore.Qt.white))
    cell.setForeground(QtGui.QBrush(QtCore.Qt.black))
    self.stdItemArrayName.append(cell)
    row.append(cell)
    cell=QtGui.QStandardItem('empty')
    cell.setFlags(QtCore.Qt.ItemIsEditable)
    cell.setBackground(QtGui.QBrush(QtCore.Qt.white))
    cell.setForeground(QtGui.QBrush(QtCore.Qt.black))      
    self.stdItemArrayData.append(cell)
    row.append(cell)            
    cell=QtGui.QStandardItem(True)
    cell.setCheckable(True)
    cell.setCheckState(QtCore.Qt.Unchecked)
    row.append(cell)            
    self.stdItemArraySelect.append(cell)
    self.model.appendRow(row)       
    self.formatTableView()

  def formatTableView(self):
    self.table.resizeRowsToContents()
    #self.table.resizeColumnToContents(0)
    self.table.setColumnWidth(0,100)
    self.table.setColumnWidth(1,200)
    self.table.setColumnWidth(2,20)
    #self.table.setHorizontalHeaderLabels(['Parameter', 'Value','Select'])

  def parseAxisStatArray(self,charData):
    self.dataList=charData.split(',')
    if len(self.dataList)!=ELEMENT_COUNT:
      return PARSE_ERROR_ELEMENT_COUNT_OUT_OF_RANGE

    #Update table view  
    for i in range(0,ELEMENT_COUNT):
      if self.dataList[i] is not None:
        if len(self.dataList[i])>0:                    
          func=self.dataSourceConvFuncPoint[i]
          func(self.dataList[i],self.stdItemArrayData[i])
    
    self.covertStringToData(self.dataList)
    self.update()
    if self.startToPlot:
      self.updateDataPlot()

  def defaultStrFunc(self,strValue,cell):
    cell.setData(strValue,role=QtCore.Qt.DisplayRole)

  def sourceFunc(self,strValue,cell):
    if int(strValue)==0:
      strToSet="Internal"
    else:
      strToSet="PLC"

    cell.setData(strToSet,role=QtCore.Qt.DisplayRole)

  def commandStrFunc(self,strValue,cell):
    switcher = {
        1:  "Move Vel",
        2:  "Move Rel",
        3:  "Move Abs",
        10: "Move Home",
    }
    strToSet=switcher.get(int(strValue),strValue)
    if strToSet==strValue:
      cell.setBackground(QtGui.QBrush(QtCore.Qt.red))      
    else:
      cell.setBackground(QtGui.QBrush(QtCore.Qt.white))      
    cell.setData(strToSet,role=QtCore.Qt.DisplayRole)

  def highOKLowNotOKFunc(self,strValue,cell):
    if int(strValue)==1:
      strToSet="OK"
      cell.setBackground(QtGui.QBrush(QtCore.Qt.green))      
    else:
      strToSet="Not OK"
      cell.setBackground(QtGui.QBrush(QtCore.Qt.red))      
    cell.setData(strToSet,role=QtCore.Qt.DisplayRole)

  def busyFunc(self,strValue,cell):
    if int(strValue)==0:
      strToSet="Ready"
      cell.setBackground(QtGui.QBrush(QtCore.Qt.green))      
    else:      
      strToSet="Busy"
      cell.setBackground(QtGui.QBrush(QtCore.Qt.red))      
    cell.setData(strToSet,role=QtCore.Qt.DisplayRole)

  def errorFunc(self,strValue,cell):
    if int(strValue,16)==0:
      cell.setBackground(QtGui.QBrush(QtCore.Qt.green))      
    else:      
      cell.setBackground(QtGui.QBrush(QtCore.Qt.red))      
    cell.setData(strValue,role=QtCore.Qt.DisplayRole)

  def lowOKHighNotOKShowValFunc(self,strValue,cell):
    if int(strValue)==0:
      cell.setBackground(QtGui.QBrush(QtCore.Qt.green))      
    else:      
      cell.setBackground(QtGui.QBrush(QtCore.Qt.red))      
    cell.setData(strValue,role=QtCore.Qt.DisplayRole)

  def iLockFunc(self,strValue,cell):
    if int(strValue)==0:
      cell.setBackground(QtGui.QBrush(QtCore.Qt.green))
      cell.setData("OK",role=QtCore.Qt.DisplayRole)
      return
    
    switcher = {
        1:  "Soft Bwd",
        2:  "Soft Fwd",
        3:  "Hard Bwd",
        4:  "Hard Fwd",
        5:  "No Execute",
        6:  "Pos. Lag",
        7:  "Both Lim.",
        8:  "External",
        9:  "Transform",
        10: "Max Vel.",
        11: "Cntrl High Lim.",
        12: "Cntrl Inc at Lim.",
        13: "Axis Error",
        14: "Unexp. Lim.",
        15: "Vel. diff",
        16: "Hardware",
        17: "PLC",
        18: "PLC Bwd",
        19: "PLC Fwd",
    }
    
    strToSet=switcher.get(int(strValue),strValue)    
    cell.setData(strToSet,role=QtCore.Qt.DisplayRole)
    cell.setBackground(QtGui.QBrush(QtCore.Qt.red))      

  def cmdDataStrFunc(self,strValue,cell):        
    if self.command!=ECMC_COMMAND['MOVE_HOME']:
      self.defaultStrFunc(strValue,cell)      
      return
      
    switcher = {
        0: "Not defined",
        1: "Low Lim",
        2: "High Lim",
        3: "Low Lim, Home Sens",
        4: "High Lim, Home Sens",
        5: "Low Lim, Center Home Sens",
        6: "High Lim, Center Home Sens",
        7: "Bwd, Home sens",
        8: "Fwd, Home sens",
        9: "Bwd, Center Home Sens",
        10: "Fwd, Center Home Sens",
        11: "Low Lim, Enc index",
        12: "High Lim, Enc index",
        15: "Home Direct",
        21: "Low Lim Part Abs",
        22: "High Lim Part Abs",
    }
    
    strToSet=switcher.get(int(strValue),strValue)
    if strToSet==strValue:
      cell.setBackground(QtGui.QBrush(QtCore.Qt.red))      
    else:
      cell.setBackground(QtGui.QBrush(QtCore.Qt.white))      
    cell.setData(strToSet,role=QtCore.Qt.DisplayRole)

  def covertStringToData(self,dataList):    
    self.axId=int(dataList[0])
    self.posSet=float(dataList[1])
    self.posAct=float(dataList[2])
    self.posErr=float(dataList[3])
    self.posTarg=float(dataList[4])
    self.posErrTarg=float(dataList[5])
    self.posRaw=float(dataList[6])
    self.cntrlOut=float(dataList[7])
    self.velSet=float(dataList[8])
    self.velAct=float(dataList[9])
    self.velFFraw=float(dataList[10])
    self.velRaw=float(dataList[11])
    self.cycleCounter=int(dataList[12])
    self.error=int(dataList[13],16)
    self.command=int(dataList[14])
    self.cmdData=int(dataList[15])
    self.seqState=int(dataList[16])
    self.ilock=int(dataList[17])
    self.ilockLastActive=int(dataList[18])
    self.trajSource=int(dataList[19])
    self.encSource=int(dataList[20])
    self.enable=int(dataList[21])
    self.enabled=int(dataList[22])
    self.execute=int(dataList[23])
    self.busy=int(dataList[24])
    self.atTarget=int(dataList[25])
    self.homed=int(dataList[26])
    self.lowLim=int(dataList[27])
    self.highLim=int(dataList[28])
    self.homeSensor=int(dataList[29])
    self.trendValue = float(dataList[self.trendDataIndex])

  def onChangeAxisDiagPv(self,pvname=None, value=None, char_value=None,timestamp=None, **kw):
    self.comTable.data_signal.emit(char_value,timestamp)

  # All update of GUI here..
  def updateGUI(self, char_value, timestamp):
    self.errorCode=self.parseAxisStatArray(char_value)

    if self.errorCode:
      print("Parse failed with error code: " + str(self.errorCode))
    
    self.strTime=datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S%f')
    self.stdItemArrayData[TIMESTAMP_INDEX].setData(self.strTime,role=QtCore.Qt.DisplayRole)


  def connect(self, pvname):
    if pvname is None:            
      raise RuntimeError("pvname must not be 'None'")

    if len(pvname)==0:
      raise RuntimeError("pvname must not be ''")

    self.axisDiagPvName = pvname
    self.axisDiagPv = epics.PV(self.axisDiagPvName)
    self.axisDiagPv.add_callback(self.onChangeAxisDiagPv)
    self.trend.setTitle(self.axisDiagPvName)
    

  def disconnect(self):
    if self.axisDiagPv is not None:
      self.axisDiagPv.clear_callbacks()

  def printInfo(self):
    print("axId             :  " + str(self.axId))
    print("posSet           :  " + str(self.posSet))
    print("posAct           :  " + str(self.posAct))
    print("posErr           :  " + str(self.posErr))
    print("posTarg          :  " + str(self.posTarg))
    print("posErrTarg       :  " + str(self.posErrTarg))
    print("posRaw           :  " + str(self.posRaw))
    print("cntrlOut         :  " + str(self.cntrlOut))
    print("velSet           :  " + str(self.velSet))
    print("velAct           :  " + str(self.velAct))
    print("velFFraw         :  " + str(self.velFFraw))
    print("velRaw           :  " + str(self.velRaw))
    print("cycleCounter     :  " + str(self.cycleCounter))
    print("error            :  " + str(self.error))
    print("command          :  " + str(self.command))
    print("cmdData          :  " + str(self.cmdData))
    print("seqState         :  " + str(self.seqState))
    print("ilock            :  " + str(self.ilock))
    print("ilockLastActive  :  " + str(self.ilockLastActive))
    print("trajSource       :  " + str(self.trajSource))
    print("encSource        :  " + str(self.encSource))
    print("enable           :  " + str(self.enable))
    print("enabled          :  " + str(self.enabled))
    print("execute          :  " + str(self.execute))
    print("busy             :  " + str(self.busy))
    print("atTarget         :  " + str(self.atTarget))
    print("homed            :  " + str(self.homed))
    print("lowLim           :  " + str(self.lowLim))
    print("highLim          :  " + str(self.highLim))
    print("homeSensor       :  " + str(self.homeSensor))
    return

  def startPlot(self):
    self.trendDataIndex, label = self.checkPlotVar()
    self.trend.setYLabel(label)
    self.trend.show()
    self.startToPlot=True;  

  def updateDataPlot(self): 
    if self.startToPlot:
       self.comTrend.data_signal.emit(self.trendValue)
  
  # return first index of selected data (only support one var currently)
  def checkPlotVar(self):
    for i in range(0,ELEMENT_COUNT):
      if self.stdItemArraySelect[i].checkState():
        return i, self.stdItemArrayName[i].text()

    return TREND_DEFAULT_INDEX, self.stdItemArrayName[TREND_DEFAULT_INDEX].text()
