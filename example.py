# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 15:55:40 2018

@author: bramv
"""

filename = 'sweep_pcp_v_0-20170731010033_10908--buf.bz2'

from numpy_BUFR import decode_bufr

bufr_decoder = decode_bufr.DecodeBUFR()

metadata, full_description, data, data_loops = bufr_decoder(filename)

print(metadata,'\n\n',full_description,'\n\n',data,'\n\n',data_loops)