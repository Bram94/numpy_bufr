# -*- coding: utf-8 -*-
"""
Created on Sat Feb 10 12:11:29 2018

@author: bramv
"""
import numpy as np
import datetime
import sys



def bytes_to_array(data, datadepth = 8):
    if sys.byteorder != 'big':
        byteorder = '>'
    else:
        byteorder = '<'
    
    datawidth = int(datadepth / 8)

    datatype = byteorder + 'u' + str(datawidth)

    return np.ndarray((int(len(data) / datawidth),),
                  dtype=datatype, buffer=data)
    
def bits_to_n(bits,signed=False):
    """Convert a sequence of bits to a number, assuming that the most significant bits are placed first (big endian style)
    If signed=True, then it is assumed that the first bit represents the sign of the number, which is 1 when the first bit
    is 0, and -1 otherwise.
    """
    if type(bits)==np.ndarray:
        if signed:
            return -2*(bits[...,0]-0.5)*np.sum(bits[...,1:]*np.array([2**j for j in reversed(range(0,bits.shape[-1]-1))]),axis=-1)
        else:
            return np.sum(bits*np.array([2**j for j in reversed(range(0,bits.shape[-1]))]),axis=-1)      
    else:
        if signed:
            return int(-2*(bits[0]-0.5)*np.sum(bits[1:]*np.array([2**j for j in reversed(range(0,len(bits)-1))])))
        else:
            return int(np.sum(bits*np.array([2**j for j in reversed(range(0,len(bits)))])))
        
def dtg(bits, edition=4):
    """
    edition.3: year [yy], month, day, hour, minute
    edition.4: year [yyyy], month, day, hour, minute, second
    """
    n = 8 if edition < 4 else 16
    year = bits_to_n(bits[:n])

    if edition < 4: 
        if year>50: year += 1900
        else: year += 2000
        
    month = bits_to_n(bits[n:n+8])
    day = bits_to_n(bits[n+8:n+16])
    hour = bits_to_n(bits[n+16:n+24])
    minute = bits_to_n(bits[n+24:n+32])
    second = bits_to_n(bits[n+32:n+40]) if edition==4 else 0
    
    return datetime.datetime(year, month, day, hour, minute, second)