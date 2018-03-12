# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 15:55:40 2018

@author: bramv
"""

filename = 'sweep_pcp_v_0-20170731010033_10908--buf.bz2'

from numpy_bufr import decode_bufr
import os

table_type = 'eccodes'
table_path = os.path.join('D:/Python/numpy_bufr/Tables',table_type)
bufr_decoder = decode_bufr.DecodeBUFR(table_path, table_type)

#It is possible to overwrite here the table_path and table_type that have been specified above during the initialization of DecodeBUFR.
metadata, full_description, data, data_loops = bufr_decoder(filename)

print(metadata,'\n\n',full_description,'\n\n',data,'\n\n',data_loops)
