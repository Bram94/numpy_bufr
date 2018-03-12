# -*- coding: utf-8 -*-
"""
Created on Mon Mar 12 16:30:21 2018

@author: bramv
"""

from setuptools import setup

setup(name='numpy_bufr',
      version='1.0',
      description='A numpy-based and very efficient BUFR decoder, for at least data from weather radars provided by the DWD.',
      author="Bram van't Veen",
      packages=['numpy_bufr', 'numpy_bufr.tables'],
     )