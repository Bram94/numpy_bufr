# -*- coding: utf-8 -*-
"""
Created on Sat Feb 10 14:17:27 2018

@author: bramv


Is for a large part based on/ copied from the script trollbufr/read/bufr_sect.py from Alex Maul, see: https://github.com/alexmaul/trollbufr
"""
import numpy as np

from . import bufr_functions as bf




def decode_sect0(sec0):
    """
    RETURN offset, length, {size, edition}
    """
    if str(np.packbits(sec0[:32]),'utf-8') != "BUFR":
        return {}
    
    size = bf.bits_to_n(sec0[32:56])
    edition = bf.bits_to_n(sec0[-8:])
    return {'size':size, 'edition':edition}


"""
Section 1
=========
BUFR Vers. 3
-----------
0-2   Section length
3     Master table
4     Sub-centre
5     Centre
6     Update sequence number (0 = original, 1.. = updates)
7     Flag: 00 = no sect2, 01 = sect2 present, 02-ff = reserved
8     Data category
9     Sub-category
10    Master table version
11    Local table version
12    Year [yy]
13    Month
14    Day
15    Hour
16    Minute
17-n  Reserved
BUFR Vers. 4
------------
0-2   Section length
3     Master table
4-5   Centre
6-7   Sub-centre
8     Update sequence number (0 = original, 1.. = updates)
9     Flag, 0x00 = no sect2, 0x01 = sect2 present, 0x02-0xff = reserved
10    Data-category
11    Internat. sub-category
12    Local sub-category
13    Master table version
14    Local table version
15-16 Year [yyyy]
17    Month
18    Day
19    Hour
20    Minute
21    Second
(22-n Reserved)
"""
def decode_sect1(sec1, edition=3):
    """
    RETURN offset, length, {master, center, subcenter, update, cat, cat_int, cat_loc, mver, lver, datetime, sect2}
    """
    key_offs = {
                2:(("length", 0, 2), ("master", 3, 3), ("center", 5, 5), ("subcenter", 4 , 4),
                   ("update", 6, 6), ("cat", 8, 8), ("cat_int", 9, 9), ("cat_loc", 9, 9),
                   ("mver", 10, 10), ("lver", 11, 11), ("datetime", 12 , 16), ("sect2", 7, 7),
                ),
                3:(("length", 0, 2), ("master", 3, 3), ("center", 5, 5), ("subcenter", 4 , 4),
                   ("update", 6, 6), ("cat", 8, 8), ("cat_int", 9, 9), ("cat_loc", 9, 9),
                   ("mver", 10, 10), ("lver", 11, 11), ("datetime", 12 , 16), ("sect2", 7, 7),
                ),
                4:(("length", 0, 2), ("master", 3, 3), ("center", 4, 5), ("subcenter", 6 , 7),
                   ("update", 8, 8), ("cat", 10, 10), ("cat_int", 11, 11), ("cat_loc", 12, 12),
                   ("mver", 13, 13), ("lver", 14, 14), ("datetime", 15 , 21), ("sect2", 9, 9),
                ),
            }
    meta_dict = {}
    for t in key_offs[edition]:
        if t[0]=='datetime':
            meta_dict[t[0]] = bf.dtg(sec1[t[1]*8:(t[2]+1)*8], edition)
        else:
            meta_dict[t[0]] = bf.bits_to_n(sec1[t[1]*8:(t[2]+1)*8])
    meta_dict['sect2'] = meta_dict['sect2'] & 128

    return meta_dict


"""
Section 3
=========
0-2   Section length
3     Reserved
4-5   Number of subsets
6     Flag: &128 = other|observation, &64 = not compressed|compressed
7-n   List of descriptors
        FXXYYY: F = 2bit, & 0xC000 ; XX = 6bit, & 0x3F00 ; YYY = 8bit, & 0xFF
        F=0: element/Tab.B, F=1: repetition, F=2: operator/Tab.C, F=3: sequence/Tab.D
"""
def decode_sect3(sec3, sec3_length):
    """Get the list of data descriptors that is given in section 3
    """
    desc_start = 56 #Index at which the listing of data descriptors starts
    desc_end = sec3_length-int(np.mod(desc_start,16))
    desc_range = desc_end-desc_start
    
    n_descriptors = int(desc_range/16) #Descriptors are represented by 16 bits according to the FXY format,
    #where F represents the type of descriptor, X its class, and Y its number within that class. F is represented by the first
    #2 bits, X by the next 6, and Y by the last 8.
    sec3_reshaped = np.reshape(sec3[desc_start:desc_end], (n_descriptors,int(desc_range/n_descriptors)))
    F = bf.bits_to_n(sec3_reshaped[:,:2]); X = bf.bits_to_n(sec3_reshaped[:,2:8]); Y = bf.bits_to_n(sec3_reshaped[:,8:])
    
    descriptors = [str(F[j])+format(X[j],'02')+format(Y[j],'03') for j in range(n_descriptors)]
    return {'descr':descriptors}