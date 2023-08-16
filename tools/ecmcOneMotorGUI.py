#!/usr/bin/env python3.6
import epics
import sys
from PyQt5 import QtWidgets, QtGui, QtCore
from ecmcArrayStat import *

#Define pvs
# Axis
ECMC_PV_AXIS_DIAG_ARRAY_SUFFIX =       '-Arr-Stat'
ECMC_PV_AXIS_ERROR_RESET_SUFFIX =      '-ErrRst'
# Controller
ECMC_PV_CNTROLLER_ERROR_ID_SUFFIX =    'MCU-ErrId'
ECMC_PV_CNTROLLER_ERROR_MSG_SUFFIX =   'MCU-ErrMsg'
ECMC_PV_CNTROLLER_ERROR_RESET_SUFFIX = 'MCU-ErrRst'
ECMC_PV_CNTROLLER_ERROR_CND_SUFFIX =   'MCU-Cmd'

BLANK = ' '*4
BACKGROUND_DEFAULT = '#efefef'
#BACKGROUND_DONE_MOVING = 'beige'
BACKGROUND_DONE_MOVING = BACKGROUND_DEFAULT
BACKGROUND_MOVING = 'lightgreen'
BACKGROUND_LVIO_ON = 'yellow'
BACKGROUND_LIMIT_ON = 'red'
TOOLTIPS = {
        'DESC': 'DESC: short description',
        'NAME': 'NAME: EPICS PV name',
        'RBV':  'RBV: motor readback value',
        'VAL':  'VAL: motor target value',
        'EGU':  'EGU: engineering units',
        'STOP': 'STOP: command this motor to stop moving',
        'TWV':  'TWV: tweak value',
        'TWF':  'TWF: increment motor by tweak value',
        'TWR':  'TWR: decrement motor by tweak value',
        '*10':  'multiply tweak value by 10',
        '/10':  'divide tweak value by 10',
        'CNEN': 'enable/disable drive',
        'ArrayStat': 'axis Status',
        'ErrRst': 'reset axis error',
        'JOGR': 'JOGR: jog backward',
        'JOGF': 'JOGF: jog forward',
        'HOMR': 'HOMR: Home reverse',
        'HOMF': 'HOMF: Home forward',     
        'MSTA': 'MSTA: Status',
        'JVEL': 'JVEL: Jog velocity',
        'VELO': 'VELO: Velocity (positioning)'
}
STYLES = {      ### http://doc.qt.digia.com/qt/stylesheet-reference.html
    'self': '''
             MotorPanel { 
                border-style: solid;
                border-color: black;
                border-width: 1px;
             }
            ''',
    'DESC': '''
             QLabel { 
                qproperty-alignment: AlignRight;
                font: bold;
             }
            ''',
    'NAME': '''
             QLabel { 
                qproperty-alignment: AlignRight;
                font: bold;
             }
            ''',
    'RBV': '''
             QLabel { 
                qproperty-alignment: AlignRight;
             }
            ''',
    'EGU': '''
             QLabel { 
                qproperty-alignment: AlignRight;
             }
            ''',
    'VAL': '''
            QLineEdit { 
                   background-color: white;
                   text-align: right;
                   }
           ''',
    'STOP': '''
            QPushButton { 
                   background-color: red;
                   color: black;
                   text-align: center;
                   height: 50px;
                   min-height: 50px;
                   max-height: 50px;
                   }
            QPushButton:hover { 
                   background-color: red;
                   color: yellow;
                   font: bold;
                   text-align: center;
                   }
            ''',
    'CNEN': '''
            QPushButton { 
                   background-color: red;
                   color: black;
                   text-align: center;
                   height: 40px;
                   min-height: 40px;
                   max-height: 40px;
                   }
            QPushButton:hover { 
                   background-color: red;
                   color: yellow;
                   font: bold;
                   text-align: center;
                   }
            ''',
    'BUTTON_ON': '''
            QPushButton { 
                   background-color: green;
                   color: black;
                   text-align: center;
                   height: 40px;
                   min-height: 40px;
                   max-height: 40px;
                   }
            QPushButton:hover { 
                   background-color: green;
                   color: yellow;
                   font: bold;
                   text-align: center;
                   }
            ''',

    'TWV': '''
            QLineEdit { 
                   background-color: white;
                   text-align: right;
                   width: 80px;
                   min-width: 80px;
                   max-width: 80px;
                   height: 40px;
                   min-height: 40px;
                   max-height: 40px;
                   }
           ''',
    'TWF': '''
            QPushButton { 
                   width: 40px;
                   min-width: 40px;
                   max-width: 40px;
                   height: 40px;
                   min-height: 40px;
                   max-height: 40px;                
                   }
           ''',
    'TWR': '''
            QPushButton { 
                   width: 40px;
                   min-width: 40px;
                   max-width: 40px;
                   height: 40px;
                   min-height: 40px;
                   max-height: 40px;

                   }
           ''',
    '*10': '''
            QPushButton { 
                   width: 40px;
                   min-width: 40px;
                   max-width: 40px;
                   height: 40px;
                   min-height: 40px;
                   max-height: 40px;
                   }
           ''',
    '/10': '''
            QPushButton { 
                   width: 40px;
                   min-width: 40px;
                   max-width: 40px;
                   height: 40px;
                   min-height: 40px;
                   max-height: 40px;
                   }
           ''',
    'ArrayStat': '''
            QTableView { 
                   background-color: white;
                   font: bold;
                   width: 350px;
                   min-width: 350px;
                   max-width: 350px;
                   font-size:10pt;
                   height:770px;
                   min-height:770px;
                   max-height:770px;
                   }
           ''',
    'ErrRst': '''
            QPushButton { 
                   background-color: red;
                   color: black;
                   text-align: center;
                   height: 40px;
                   min-height: 40px;
                   max-height: 40px;
                   }
            QPushButton:hover { 
                   background-color: red;
                   color: yellow;
                   font: bold;
                   text-align: center;
                   }

           ''',
    'JOGR': '''
            QPushButton { 
                   background-color: grey;
                   color: black;
                   text-align: center;
                   height: 40px;
                   min-height: 40px;
                   max-height: 40px;
                   }
           ''',
    'JOGF': '''
            QPushButton { 
                   background-color: grey;
                   color: black;
                   text-align: center;
                   height: 40px;
                   min-height: 40px;
                   max-height: 40px;
                   }
           ''',
    'HOMR': '''
            QPushButton { 
                   background-color: grey;
                   color: black;
                   text-align: center;
                   height: 40px;
                   min-height: 40px;
                   max-height: 40px;
                   }
           ''',
    'HOMF': '''
            QPushButton { 
                   background-color: grey;
                   color: black;
                   text-align: center;
                   height: 40px;
                   min-height: 40px;
                   max-height: 40px;
                   }
           ''',
    'MSTA': '''
            QLabel { 
                   text-align: right;
                   }
           ''',
    'PLOT': '''
            QPushButton { 
                   background-color: grey;
                   color: black;
                   text-align: center;
                   height: 40px;
                   min-height: 40px;
                   max-height: 40px;
                   }
           ''',
   
   'VELO': '''
       QLineEdit { 
              background-color: white;
              text-align: right;
              width: 80px;
              min-width: 80px;
              max-width: 80px;
              height: 40px;
              min-height: 40px;
              max-height: 40px;
              }
      ''',
   'JVEL': '''
       QLineEdit { 
              background-color: white;
              text-align: right;
              width: 80px;
              min-width: 80px;
              max-width: 80px;
              height: 40px;
              min-height: 40px;
              max-height: 40px;
              }
      ''',

}

class MotorPanel(QtWidgets.QDialog):
    
    def __init__(self, parent=None,iocPrefix=None,axisName=None):
        super(MotorPanel, self).__init__(parent)
        QtWidgets.QToolTip.setFont(QtGui.QFont('SansSerif', 10))
        self.motorPv = None
        self.motorPvName = ""
        self.axisDiagPvName=""
        self.axisErrorResetPv = None
        self.axisErrorResetPvName = ""
        self.cntrlErrorIdPv = None
        self.cntrlErrorIdPvName = ""
        self.cntrlErrorResetPv = None
        self.cntrlErrorResetPvName = ""
        self.cntrlErrorMsgPv = None
        self.cntrlErrorMsgPvName = ""
        self.cntrlErrorMsg=""
        self.cntrlCmdPv = None
        self.cntrlCmdPvName = ""
        self.create_GUI()
        self.apply_styles()
        self.create_actions()

        if isinstance(axisName, str) and  isinstance(iocPrefix, str):
            self.connect(iocPrefix,axisName)

    def create_GUI(self):
        '''define controls AND set the layout'''    
        self.controls = {}
        for field in ['DESC', 'NAME', 'EGU', 'RBV']:
            self.controls[field] = QtWidgets.QLabel(BLANK)
        self.controls['VAL'] = QtWidgets.QLineEdit()
        self.controls['STOP'] = QtWidgets.QPushButton('STOP',default=False, autoDefault=False)
        self.controls['TWF'] = QtWidgets.QPushButton('>>',default=False, autoDefault=False)
        self.controls['TWV'] = QtWidgets.QLineEdit()
        self.controls['TWR'] = QtWidgets.QPushButton('<<',default=False, autoDefault=False)
        self.controls['*10'] = QtWidgets.QPushButton('*10',default=False, autoDefault=False)
        self.controls['/10'] = QtWidgets.QPushButton('/10',default=False, autoDefault=False)
        self.controls['CNEN'] = QtWidgets.QPushButton('CNEN',default=False, autoDefault=False)
        self.controls['ArrayStat']=ecmcArrayStat(self)
        self.controls['JVEL'] = QtWidgets.QLineEdit()
        self.controls['VELO'] = QtWidgets.QLineEdit()
        self.controls['ErrRst'] = QtWidgets.QPushButton('Reset Error',default=False, autoDefault=False)
        self.controls['JOGR'] = QtWidgets.QPushButton('JOGR',default=False, autoDefault=False)
        self.controls['JOGF'] = QtWidgets.QPushButton('JOGF',default=False, autoDefault=False)
        self.controls['HOMR'] = QtWidgets.QPushButton('HOMR',default=False, autoDefault=False)
        self.controls['HOMF'] = QtWidgets.QPushButton('HOMF',default=False, autoDefault=False)
        self.controls['PLOT'] = QtWidgets.QPushButton('Plot',default=False, autoDefault=False)
        self.controls['MSTA'] = QtWidgets.QLabel()
        self.controls['RBV'].setAutoFillBackground(True)
        self.setLabelBackground(self.controls['RBV'], BACKGROUND_DONE_MOVING)
        
        main_frame= QtWidgets.QFrame(self)
        main_layout = QtWidgets.QHBoxLayout()
   
        left_frame = QtWidgets.QFrame(self)
        left_layout = QtWidgets.QVBoxLayout()
        for field in ['NAME','DESC', 'EGU', 'RBV', 'VAL','VELO','MSTA']:
            tmp_frame = QtWidgets.QFrame(self)
            tmp_layout = QtWidgets.QHBoxLayout()
            tmp_label=QtWidgets.QLabel()
            tmp_label.setText(field+ ':')
            tmp_layout.addWidget(tmp_label)
            tmp_layout.addWidget(self.controls[field])
            tmp_frame.setLayout(tmp_layout)
            left_layout.addWidget(tmp_frame)   

        #Tweak
        tweak_label= QtWidgets.QLabel()
        tweak_label.setText('TWEAK:')
        left_layout.addWidget(tweak_label)        

        tweak_frame = QtWidgets.QFrame(self)
        tweak_layout = QtWidgets.QHBoxLayout()
        for field in ['TWR', '/10', 'TWV', '*10', 'TWF']:
            tweak_layout.addWidget(self.controls[field])
        tweak_frame.setLayout(tweak_layout)
        
        left_layout.addWidget(tweak_frame)

        #Jog
        jog_label= QtWidgets.QLabel()
        jog_label.setText('JOG:')
        left_layout.addWidget(jog_label)        
        jvel_frame = QtWidgets.QFrame(self)
        jvel_layout = QtWidgets.QHBoxLayout()
        jvel_label=QtWidgets.QLabel()
        jvel_label.setText('JVEL' + ':')
        jvel_layout.addWidget(jvel_label)
        jvel_layout.addWidget(self.controls['JVEL'])
        jvel_frame.setLayout(jvel_layout)
        left_layout.addWidget(jvel_frame)
        jog_frame = QtWidgets.QFrame(self)
        jog_layout = QtWidgets.QHBoxLayout()
        jog_layout.addWidget(self.controls['JOGR'])
        jog_layout.addWidget(self.controls['JOGF'])
        jog_frame.setLayout(jog_layout)
        left_layout.addWidget(jog_frame)

        #Home
        home_label= QtWidgets.QLabel()
        home_label.setText('HOME:')
        left_layout.addWidget(home_label)        
        home_frame = QtWidgets.QFrame(self)
        home_layout = QtWidgets.QHBoxLayout()
        home_layout.addWidget(self.controls['HOMR'])
        home_layout.addWidget(self.controls['HOMF'])
        home_frame.setLayout(home_layout)
        left_layout.addWidget(home_frame)

        control_label= QtWidgets.QLabel()
        control_label.setText('CONTROL:')
        left_layout.addWidget(control_label)        

        left_layout.addWidget(self.controls['STOP'])
        left_layout.addWidget(self.controls['CNEN'])
        left_layout.addWidget(self.controls['ErrRst'])

        left_frame.setLayout(left_layout)
        main_layout.addWidget(left_frame)

        right_frame = QtWidgets.QFrame(self)
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(self.controls['ArrayStat'])
        right_layout.addWidget(self.controls['PLOT'])
        right_frame.setLayout(right_layout);

        main_layout.addWidget(right_frame)
        main_frame.setLayout(main_layout)

        self.setLayout(main_layout)
        self.setWindowTitle("ecmc: axis control")
        

    def apply_styles(self):
        '''apply styles and tips'''     
        for field in ['DESC', 'NAME', 'EGU', 'RBV', 'VAL', 
                      'STOP','CNEN','TWV', 'TWF', 'TWR', '*10', 
                      '/10','ArrayStat','ErrRst','JOGR','JOGF',
                      'HOMR','HOMF','MSTA','JVEL','VELO']:
            if field in STYLES:
                self.controls[field].setStyleSheet(STYLES[field])
            if field in TOOLTIPS:
                self.controls[field].setToolTip(TOOLTIPS[field])
        
        self.setStyleSheet(STYLES['self'])

    def create_actions(self):
        '''define actions'''
        self.controls['VAL'].returnPressed.connect(self.onReturnVAL)
        self.controls['VELO'].returnPressed.connect(self.onReturnVELO)
        self.controls['TWV'].returnPressed.connect(self.onReturnTWV)
        self.controls['TWR'].clicked.connect(self.onPushTWR)
        self.controls['TWF'].clicked.connect(self.onPushTWF)
        self.controls['*10'].clicked.connect(self.onPush10x)
        self.controls['/10'].clicked.connect(self.onPush_1x)
        self.controls['STOP'].clicked.connect(self.onPushSTOP)
        self.controls['CNEN'].clicked.connect(self.onPushCNEN)
        self.controls['ErrRst'].clicked.connect(self.onPushErrRst)
        self.controls['JVEL'].returnPressed.connect(self.onReturnJVEL)
        self.controls['JOGR'].clicked.connect(self.onPushJOGR)
        self.controls['JOGF'].clicked.connect(self.onPushJOGF)
        self.controls['HOMR'].clicked.connect(self.onPushHOMR)
        self.controls['HOMF'].clicked.connect(self.onPushHOMF)
        self.controls['PLOT'].clicked.connect(self.onPushPLOT)
        

    def setPvNames(self,iocPrefix=None,axisName=None):
        self.motorPvName = (iocPrefix + axisName).split('.')[0]  # keep everything to left of first dot
        self.axisDiagPvName = self.motorPvName + ECMC_PV_AXIS_DIAG_ARRAY_SUFFIX
        self.axisErrorResetPvName = self.motorPvName + ECMC_PV_AXIS_ERROR_RESET_SUFFIX
        self.cntrlErrorIdPvName = iocPrefix + ECMC_PV_CNTROLLER_ERROR_ID_SUFFIX
        self.cntrlErrorResetPvName = iocPrefix + ECMC_PV_CNTROLLER_ERROR_RESET_SUFFIX
        self.cntrlErrorMsgPvName = iocPrefix + ECMC_PV_CNTROLLER_ERROR_MSG_SUFFIX
        self.cntrlCmdPvName = iocPrefix + ECMC_PV_CNTROLLER_ERROR_CND_SUFFIX

    def connect(self, iocPrefix=None,axisName=None):
        '''connect this panel with an EPICS motor PV'''
        if iocPrefix is None:            
            raise RuntimeError("iocPrefix must not be 'None'")
        if axisName is None:            
            raise RuntimeError("axisName must not be 'None'")
        
        self.setPvNames(iocPrefix,axisName)

        if len(iocPrefix) == 0 or len(axisName) == 0:
            raise RuntimeError("iocPrefix or axisName must not be ''")
        
        if self.motorPv is not None:
            self.disconnect()
        
        self.controls['NAME'].setText(self.motorPvName)
        self.motorPv = epics.Motor(self.motorPvName)   # verifies that self.motor_pv has RTYP='motor'

        callback_dict = {
            #field:  callback function
            'DESC': self.onChangeDESC,
            'EGU':  self.onChangeEGU,
            'RBV':  self.onChangeRBV,
            'VAL':  self.onChangeVAL,
            'VELO':  self.onChangeVELO,
            'TWV':  self.onChangeTWV,
            'DMOV': self.onChangeDMOV,
            'HLS':  self.onChangeHLS,
            'LLS':  self.onChangeLLS,
            'CNEN': self.onChangeCNEN,            
            'JOGR': self.onChangeJOGR,
            'JOGF': self.onChangeJOGF,
            'JVEL':  self.onChangeJVEL,
            'HOMR': self.onChangeHOMR,
            'HOMF': self.onChangeHOMF,
            'MSTA': self.onChangeMSTA,            
        }
        for field, func in callback_dict.items():
            self.motorPv.set_callback(attr=field, callback=func)

        self.controls['DESC'].setText(self.motorPv.description)
        self.controls['EGU'].setText(self.motorPv.units)
        
        # display initial values
        self.onChangeRBV(value=self.motorPv.get('RBV'))
        self.onChangeVAL(value=self.motorPv.get('VAL'))
        self.onChangeTWV(value=self.motorPv.get('TWV'))
        self.onChangeDMOV(value=self.motorPv.get('DMOV'))
        self.onChangeCNEN(value=self.motorPv.get('CNEN'))        
        self.onChangeJOGR(value=self.motorPv.get('JOGR'))
        self.onChangeJOGF(value=self.motorPv.get('JOGF'))
        self.onChangeHOMR(value=self.motorPv.get('HOMR'))
        self.onChangeHOMF(value=self.motorPv.get('HOMF'))
        self.onChangeMSTA(value=self.motorPv.get('MSTA'))
        self.onChangeVELO(value=self.motorPv.get('VELO'))
        self.onChangeJVEL(value=self.motorPv.get('JVEL'))
        
        # additional records
        self.axisErrorResetPv = epics.PV(self.axisErrorResetPvName)
        self.cntrlErrorIdPv = epics.PV(self.cntrlErrorIdPvName)
        self.cntrlErrorIdPv.add_callback(self.onChangeCntrlErrorIdPv)
        self.cntrlErrorResetPv = epics.PV(self.cntrlErrorResetPvName)
        self.cntrlErrorMsgPv = epics.PV(self.cntrlErrorMsgPvName)
        self.cntrlCmdPv = epics.PV(self.cntrlCmdPvName)
        self.cntrlCmdPv.add_callback(self.onChangeCntrlCmdPv)
        if self.controls['ArrayStat'] is not None:
          self.controls['ArrayStat'].connect(self.axisDiagPvName)

    def disconnect(self):
        '''disconnect this panel from EPICS'''
        if self.motorPv is not None:
            for field in ['VAL', 'RBV', 'DESC', 'EGU', 'TWV', 'DMOV', 'HLS', 'LLS']:
                self.motorPv.clear_callback(attr=field)
            self.motorPv = None
            for field in ['DESC', 'NAME', 'EGU', 'RBV', 'VAL', 'TWV']:
                self.controls[field].setText(BLANK)

        if self.cntrlErrorIdPv is not None:
            self.cntrlErrorIdPv.clear_callbacks()
        if self.cntrlCmdPv is not None:
            self.cntrlCmdPv.clear_callbacks()

        if self.controls['ArrayStat'] is not None:
          self.controls['ArrayStat'].disconnect()

    def closeEvent(self, event):
        '''be sure to disconnect from EPICS when closing'''
        self.disconnect()

    def onPushSTOP(self):
        '''stop button was pressed'''
        if self.motorPv is not None:
            self.motorPv.stop()

    def onPushCNEN(self):
        '''cnen button was pressed'''
        if self.motorPv is not None:
            self.motorPv.put('CNEN',not self.motorPv.get('CNEN'))

    def onPushErrRst(self):
        '''ErrRst button was pressed'''
        if self.axisErrorResetPv is not None:
            self.axisErrorResetPv.put(1)

    def onPushJOGR(self):
        '''jogr button was pressed'''
        if self.motorPv is not None:
            self.motorPv.put('JOGR',not self.motorPv.get('JOGR'))

    def onPushJOGF(self):
        '''jogf button was pressed'''
        if self.motorPv is not None:
            self.motorPv.put('JOGF',not self.motorPv.get('JOGF'))

    def onPushHOMR(self):
        '''homr button was pressed'''
        if self.motorPv is not None:
            self.motorPv.put('HOMR',1)

    def onPushHOMF(self):
        '''homf button was pressed'''
        if self.motorPv is not None:
            self.motorPv.put('HOMF',1)

    def onPushPLOT(self):
        '''plot button was pressed'''
        self.controls['ArrayStat'].startPlot()

    def onPushTWF(self):
        '''tweak forward button was pressed'''
        if self.motorPv is not None:
            self.motorPv.put('TWF', 1)

    def onPushTWR(self):
        '''tweak reverse button was pressed'''
        if self.motorPv is not None:
            self.motorPv.put('TWR', 1)

    def onPush10x(self):
        '''multiply TWV*10 button was pressed'''
        if self.motorPv is not None:
            self.motorPv.put('TWV', 10*self.motorPv.get('TWV'))

    def onPush_1x(self):
        '''multiply TWV*0.1 button was pressed'''
        if self.motorPv is not None:
            self.motorPv.put('TWV', 0.1*self.motorPv.get('TWV'))            

    def onReturnTWV(self):
        '''new target value was entered in this panel'''
        if self.motorPv is not None:
            number = float(self.controls['TWV'].text())
            self.motorPv.put('TWV', number)

    def onReturnVAL(self):
        '''new target value was entered in this panel'''
        if self.motorPv is not None:
            number = float(self.controls['VAL'].text())            
            #self.motorPv.move(number)
            self.motorPv.put('VAL',number)

    def onReturnVELO(self):
        '''new target velocity was entered in this panel'''
        if self.motorPv is not None:
            number = float(self.controls['VELO'].text())
            self.motorPv.put('VELO',number)

    def onReturnJVEL(self):
        '''new target jog velocity was entered in this panel'''
        if self.motorPv is not None:
            number = float(self.controls['JVEL'].text())
            self.motorPv.put('JVEL',number)

    def onChangeCNEN(self, value = None, **kws):
        '''EPICS monitor on CNEN called this'''
        field='CNEN'
        if value:            
            self.controls[field].setStyleSheet(STYLES['BUTTON_ON'])
        else:
            self.controls[field].setStyleSheet(STYLES[field])

    def onChangeJOGR(self, value = None, **kws):
        '''EPICS monitor on JOGR called this'''
        field='JOGR'
        if value:
            self.controls[field].setStyleSheet(STYLES['BUTTON_ON'])
        else:
            self.controls[field].setStyleSheet(STYLES[field])

    def onChangeJOGF(self, value = None, **kws):
        '''EPICS monitor on JOGF called this'''
        field='JOGF'
        if value:
            self.controls[field].setStyleSheet(STYLES['BUTTON_ON'])
        else:
            self.controls[field].setStyleSheet(STYLES[field])

    def onChangeHOMR(self, value = None, **kws):
        '''EPICS monitor on HOMR called this'''
        field='HOMR'
        if value:
            self.controls[field].setStyleSheet(STYLES['BUTTON_ON'])
        else:
            self.controls[field].setStyleSheet(STYLES[field])

    def onChangeHOMF(self, value = None, **kws):
        '''EPICS monitor on HOMF called this'''
        field='HOMF'
        if value:
            self.controls[field].setStyleSheet(STYLES['BUTTON_ON'])
        else:
            self.controls[field].setStyleSheet(STYLES[field])

    def onChangeMSTA(self, value = None, **kws):
        '''EPICS monitor on MSTA called this'''
        field='MSTA'                
        self.controls[field].setText(bin(int(value))[2:])

    def onChangeDESC(self, char_value=None, **kws):
        '''EPICS monitor on DESC called this'''
        self.controls['DESC'].setText(char_value)

    def onChangeDMOV(self, value = None, **kws):
        '''EPICS monitor on DMOV called this, change the color of the RBV label'''
        if value is not None:
            color = {1: BACKGROUND_DONE_MOVING, 0: BACKGROUND_MOVING}[value]
            self.setLabelBackground(self.controls['RBV'], color)

    def onChangeHLS(self, value=None, **kws):
        '''EPICS monitor on HLS called this, change the color of the TWF button'''
        if value is not None:
            color = {0: BACKGROUND_DEFAULT, 1: BACKGROUND_LIMIT_ON}[value]
            self.setLabelBackground(self.controls['TWF'], color)

    def onChangeLLS(self, value=None, **kws):
        '''EPICS monitor on LLS called this, change the color of the TWR button'''        
        if value is not None:
            color = {0: BACKGROUND_DEFAULT, 1: BACKGROUND_LIMIT_ON}[value]
            self.setLabelBackground(self.controls['TWR'], color)

    def onChangeEGU(self, char_value=None, **kws):
        '''EPICS monitor on EGU called this'''
        self.controls['EGU'].setText(char_value)

    def onChangeRBV(self, value=None, **kws):
        '''EPICS monitor on RBV called this'''
        field='RBV'
        if value is not None:
            self.controls[field].setText(str(value))

    def onChangeTWV(self, value=None, **kws):
        '''EPICS monitor on TWV called this'''
        field='TWV'
        if value is not None:            
            self.controls[field].setText(str(value))
            self.controls[field].setAlignment(QtCore.Qt.AlignRight)

    def onChangeVAL(self, value=None, **kws):
        '''EPICS monitor on VAL called this'''
        field='VAL'
        if value is not None:
            self.controls[field].setText(str(value))
            self.controls[field].setAlignment(QtCore.Qt.AlignRight)

    def onChangeVELO(self, value=None, **kws):
        '''EPICS monitor on VELO called this'''
        field='VELO'
        if value is not None:
            self.controls[field].setText(str(value))
            self.controls[field].setAlignment(QtCore.Qt.AlignRight)

    def onChangeJVEL(self, value=None, **kws):
        '''EPICS monitor on JVEL called this'''
        field='JVEL'
        if value is not None:
            self.controls[field].setText(str(value))
            self.controls[field].setAlignment(QtCore.Qt.AlignRight)

    def onChangeCntrlErrorIdPv(self,pvname=None, value=None, char_value=None, **kw):        
        self.cntrlErrorMsg=self.cntrlErrorMsgPv.get(as_string=True)
        print("new Error message: " +str(self.cntrlErrorMsg))

    def onChangeCntrlErrorMsgPv(self,pvname=None, value=None, char_value=None, **kw):
        print("onChangeCntrlErrorMsgPv:" + char_value)

    def onChangeCntrlCmdPv(self,pvname=None, value=None, char_value=None, **kw):
        print("onChangeCntrlCmdPv")

    def setLabelBackground(self, widget = None, color = BACKGROUND_DEFAULT):
        '''change the background color of a Qt widget'''
        if widget is not None:
            palette = QtGui.QPalette()
            palette.setColor(widget.backgroundRole(), QtGui.QColor(color))
            widget.setPalette(palette)


def main():
    '''demo: display the named motors in a horizontal block'''
    if len(sys.argv) != 2:
        raise RuntimeError ("usage: %s motor".format(sys.argv[0]))
    app = QtWidgets.QApplication(sys.argv)
    panel = MotorPanel(pvname=sys.argv[1])
    #panel.connect()
    panel.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()