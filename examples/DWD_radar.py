# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 15:55:40 2018

@author: bramv
"""

filename = 'sweep_pcp_v_0-20170731010033_10908--buf.bz2'

from numpy_bufr import decode_bufr
import os

bufr_decoder = decode_bufr.DecodeBUFR()

tables_basepath = 'D:/Python/numpy_bufr/Tables'
table_type = 'eccodes'
metadata, full_description, data, data_loops = bufr_decoder(filename, os.path.join(tables_basepath,table_type), table_type)

print(metadata,'\n\n',full_description,'\n\n',data,'\n\n',data_loops)
