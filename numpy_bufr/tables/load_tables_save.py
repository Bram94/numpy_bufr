#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (c) 2016 Alexander Maul
#
# Author(s):
#
#   Alexander Maul <alexander.maul@dwd.de>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''
Created on Sep 15, 2016
@author: amaul
'''

import logging
from .tables import Tables

from . import parse_bufrdc, parse_eccodes, parse_libdwd

parse_modules = {'bufrdc': parse_bufrdc, 'eccodes': parse_eccodes, 'libdwd': parse_libdwd}

logger = logging.getLogger("trollbufr")



def load_tables(tables,meta,tab_p, tab_f):
    """Load all tables referenced by the BUFR"""
    if tables is None or tables.differs(
                    meta['master'], meta['mver'], meta['lver'],
                    meta['center'], meta['subcenter']):
        tables = load_all(
                meta['master'], meta['center'], meta['subcenter'], meta['mver'],
                meta['lver'], tab_p, tab_f
                )
    return tables

def load_all(master, center, subcenter, master_vers, local_vers, base_path, tab_f = 'eccodes'):
    """Load all given versions of tables"""
    
    tables = Tables(master, master_vers, local_vers, center, subcenter)
    
    print(tab_f,'tab_f')
    tparse = parse_modules[tab_f]
    
    # Table A (centres)
    mp, _ = tparse.get_file("A", base_path, master, center, subcenter, master_vers, local_vers)
    tparse.load_tab_a(tables, mp)
    # Table B (elements)
    mp, lp = tparse.get_file("B", base_path, master, center, subcenter, master_vers, local_vers)
    # International (master) table
    tparse.load_tab_b(tables, mp)
    # Local table
    if local_vers:
        tparse.load_tab_b(tables, lp)
    # Table C (operators)
    mp, _ = tparse.get_file("C", base_path, master, center, subcenter, master_vers, local_vers)
    tparse.load_tab_c(tables, mp)
    # Table D (sequences)
    mp, lp = tparse.get_file("D", base_path, master, center, subcenter, master_vers, local_vers)
    # International (master) table
    tparse.load_tab_d(tables, mp)
    # Local table
    if local_vers:
        tparse.load_tab_d(tables, lp)
    # Table CF (code/flags)
    mp, lp = tparse.get_file("CF", base_path, master, center, subcenter, master_vers, local_vers)
    # International (master) table
    tparse.load_tab_cf(tables, mp)
    # Local table
    if False and local_vers:
        tparse.load_tab_cf(tables, lp)

    return tables