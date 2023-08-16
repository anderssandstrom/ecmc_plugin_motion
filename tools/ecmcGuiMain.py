#!/usr/bin/python3.6
# coding: utf-8

from PyQt5 import QtWidgets,uic
import numpy as np
import epics
from ecmcArrayStat import *
from ecmcOneMotorGUI import *
from ecmcMainWndDesigner import Ui_MainWindow
from ecmcFFTMainGui import *
from ecmcScopeMainGui import *
import ecmcTrendPv
import time

# Needed packages:
# 1. sudo yum -y install https://rhel7.iuscommunity.org/ius-release.rpm
# 2. sudo pip3.6 install pyqt5
# 3. sudo yum install qt5-qtbase-devel
# 4. sudo python3.6 -m pip install numpy scipy matplotlib
# 5. sudo pip3 install pyepics
# 6. sudo yum install python3-matplotlib


# Regenerate py from ui file:
# pyuic5 -x ecmcMainWndDesigner.ui -o ecmcMainWndDesigner.py

class ecmcMainWindow(QtWidgets.QMainWindow):
  def __init__(self):
    
    super(ecmcMainWindow,self).__init__()
    self.prefix=""
    self.pvName=""
    self.pv=None

    self.ui = Ui_MainWindow()
    self.ui.setupUi(self)
    self.ui.pbStartGUI.clicked.connect(self.showGUI)
    self.ui.pbStartGUI.setToolTip("Start GUI for ioc-prefix + pv-name")    

    self.ui.lineIOCPrefix.textChanged.connect(self.newIOCPrefix)
    self.ui.lineIOCPrefix.setToolTip("Enter ioc-prefix to to use.")
    self.ui.linepvName.textChanged.connect(self.newIOCpvName)
    self.ui.linepvName.setToolTip("Enter pv-name to plot/trend (or control)")

    self.ui.comboPrefix.currentIndexChanged.connect(self.newPrefixComboIndex)
    self.ui.comboPrefix.addItem("IOC_TEST:")
    self.ui.comboPrefix.addItem("IOC:")
    self.ui.comboPrefix.addItem("IOC2:")
    self.ui.comboPrefix.addItem("IOC_SLIT:")
    self.ui.comboPrefix.addItem("TEST")
    self.ui.comboPrefix.setToolTip("Predefined ioc-prefix. Choose one to use..")

    self.ui.comboPvName.currentIndexChanged.connect(self.newPvComboIndex)
    self.ui.comboPvName.addItem("Axis1")
    self.ui.comboPvName.addItem("Axis2")
    self.ui.comboPvName.addItem("MCU-ThdLatMax")
    self.ui.comboPvName.addItem("MCU-ThdLatMin")
    self.ui.comboPvName.addItem("MCU-ThdPrdMax")
    self.ui.comboPvName.addItem("MCU-ThdPrdMin")
    self.ui.comboPvName.addItem("MCU-ThdSndMax")
    self.ui.comboPvName.addItem("MCU-ThdSndMin")
    self.ui.comboPvName.addItem("m0-DomFailCntrTot")
    self.ui.comboPvName.addItem("MCU-ErrId")
    self.ui.comboPvName.addItem("m0s001-BI01")
    self.ui.comboPvName.addItem("m0s001-BI02")
    self.ui.comboPvName.addItem("m0s003-Enc01-PosAct")
    self.ui.comboPvName.addItem("FFT-0")
    self.ui.comboPvName.addItem("Scope-0")
    self.ui.comboPvName.setToolTip("Predefined pv-names. Choose one to use..")    
    
    if len(sys.argv)>1:
      self.prefix=sys.argv[1]
      self.ui.lineIOCPrefix.setText(self.prefix)
      if len(sys.argv)>2:       
        self.pvName=sys.argv[2]
        self.ui.linepvName.setText(self.pvName)
    
    
    if (len(sys.argv)>2): 
      for i in range(2,len(sys.argv)):
        self.ui.linepvName.setText(str(sys.argv[i]))
        self.showGUI()

  def showGUI(self):
    
    #Check and start FFT gui
    if self.showGuiFFT(self.prefix, self.pvName):
      return

    #Check and start Scope gui
    if self.showGuiScope(self.prefix, self.pvName):
      return

    # See if scalar or motor
    self.ui.pbStartGUI.setText("Connecting to: " + self.prefix + self.pvName + "...")
    self.ui.pbStartGUI.setEnabled(False)
    self.ui.pbStartGUI.update()
    QtCore.QCoreApplication.processEvents()

    self.prefix=self.ui.lineIOCPrefix.text()
    self.pvName=self.ui.linepvName.text()
    entirePvName = self.prefix+self.pvName
    pos = entirePvName.rfind('.')
    
    # ensure record/pv exist
    
    pvtest  = epics.PV(entirePvName)
    connected = pvtest.wait_for_connection(timeout=2)
    self.ui.pbStartGUI.setEnabled(True)
    self.ui.pbStartGUI.setText("Start GUI for: " + self.prefix + self.pvName)
    self.ui.pbStartGUI.update()    
    if not(connected):
      print("Timeout. Could not connect to: " + entirePvName + ". Probably not a valid PV name.")  
      return
    del(pvtest)
    

    # Check if motor    
    if pos < 0:
      pv  = epics.PV(entirePvName + '.RTYP')      
      if pv.get() == 'motor':
        self.showMotorGUI(self.prefix, self.pvName)
        return

    # Normal PV
    self.showGuiPv(self.prefix+self.pvName)

  def showMotorGUI(self,prefix,pvName):
    self.dialog = MotorPanel(self,prefix,pvName)
    self.dialog.resize(500, 900)
    self.dialog.show()
    
  def showGuiPv(self, pvName):
    dialog = ecmcTrendPv.ecmcTrendPv(pvName)
    dialog.show()

  def showGuiFFT(self, prefix, pvName):
    # Check if FFT gui
    if pvName.find('FFT-') == 0 and len(prefix) > 0:
      pvNameTemp = pvName.split('-')
      if np.size(pvNameTemp)==2:
        if pvNameTemp[1].isdigit():
          self.dialog = ecmcFFTMainGui(prefix,int(pvNameTemp[1]))
          self.dialog.show()
          return 1
    return 0

  def showGuiScope(self, prefix, pvName):
    # Check if FFT gui
    if pvName.find('Scope-') == 0 and len(prefix) > 0:
      pvNameTemp = pvName.split('-')
      if np.size(pvNameTemp)==2:
        if pvNameTemp[1].isdigit():
          self.dialog = ecmcScopeMainGui(prefix,int(pvNameTemp[1]))
          self.dialog.show()
          return 1
    return 0

  def newIOCPrefix(self,iocPrefix):
    self.prefix=iocPrefix
    self.ui.pbStartGUI.setText("Start GUI for: " + self.prefix + self.pvName)

  def newIOCpvName(self,pvName):
    self.pvName=pvName
    self.ui.pbStartGUI.setText("Start GUI for: " + self.prefix + self.pvName)

  def newPrefixComboIndex(self,index):
    self.prefix=self.ui.comboPrefix.itemText(index)
    self.ui.lineIOCPrefix.setText(self.prefix)
    self.ui.pbStartGUI.setText("Start GUI for: " + self.prefix + self.pvName)

  def newPvComboIndex(self,index):    
    self.pvName=self.ui.comboPvName.itemText(index)
    self.ui.linepvName.setText(self.pvName)
    self.ui.pbStartGUI.setText("Start GUI for: " + self.prefix + self.pvName)

  def quit(self):
    self.close()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window=ecmcMainWindow();
    window.show()
    sys.exit(app.exec_())
    