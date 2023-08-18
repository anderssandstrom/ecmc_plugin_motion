

import numpy as np

# unsigned char              enable        : 1;
# unsigned char              enabled       : 1;
# unsigned char              execute       : 1;
# unsigned char              busy          : 1;
# unsigned char              attarget      : 1;
# unsigned char              moving        : 1;
# unsigned char              limitfwd      : 1;
# unsigned char              limitbwd      : 1;
# unsigned char              homeswitch    : 1;
# unsigned char              homed         : 1;
# unsigned char              inrealtime    : 1;
# unsigned char              trajsource    : 1;
# unsigned char              encsource     : 1;
# unsigned char              plccmdallowed : 1;
# unsigned char              softlimfwdena : 1;
# unsigned char              softlimbwdena : 1;
# unsigned char              instartup     : 1;
# unsigned char              sumilockfwd   : 1;
# unsigned char              sumilockbwd   : 1;
# unsigned char              axisType      : 1;
# unsigned char              seqstate      : 4;
# unsigned char              lastilock     : 8;

names    = ['enable',
            'enabled',
            'execute',
            'busy',
            'attarget',
            'moving',
            'limitfwd',
            'limitbwd',
            'homeswitch',
            'homed',
            'inrealtime',
            'trajsource',
            'encsource',
            'plccmdallowed',
            'softlimfwdena',
            'softlimbwdena',
            'instartup',
            'sumilockfwd',
            'sumilockbwd',
            'axisType',
            'seqstate',
            'lastilock']
      
class ecmcParseAxisStatusWord():

    def convert(self,statuswdArray):
        arraylength = len(statuswdArray)
        data=np.empty([22,arraylength])
        #seqdata=np.empty(arraylength)
        #ilockdata=np.empty(arraylength)
        i = 0
        for statwd in statuswdArray:
            data[0:20:,i] = self.binaryRepr20(statwd)            
            data[20,i]    = self.getSeqState(statwd)
            data[21,i]    = self.getIlockData(statwd)            
            i += 1
        return data

    def getSeqState(self,data):
        localdata = data.astype(int)
        return np.bitwise_and(localdata,0b11110000000000000000000) >> 20

    def getIlockData(self,data):
        localdata = data.astype(int)
        return np.bitwise_and(localdata,0b1111111100000000000000000000000) >> 24

    def binaryRepr32(self,data):
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
        )).flatten() > 0).astype(int)
    
    def binaryRepr20(self,data):
        localdata = data.astype(int)
        return(
        np.dstack((
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
    
    def getNames(self):
        return names
    
