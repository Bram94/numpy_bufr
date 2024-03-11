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
from .errors import BufrTableError
from .tables import Tables

from . import parse_bufrdc, parse_eccodes, parse_libdwd

parse_modules = {'bufrdc': parse_bufrdc, 'eccodes': parse_eccodes, 'libdwd': parse_libdwd}

logger = logging.getLogger("trollbufr")


loaded_tables = {}
def load_differ(tables,meta,tab_p, tab_f):
    global loaded_tables
    """Load all tables referenced by the BUFR, if the versions differ from those already loaded."""
    s = ','.join(list(map(str, [meta['master'], meta['mver'], meta['lver'], meta['center'], meta['subcenter']])))
    if not s in loaded_tables:
        loaded_tables[s] = load_all(
                meta['master'], meta['center'], meta['subcenter'], meta['mver'],
                meta['lver'], tab_p, tab_f
                )
    return loaded_tables[s]

_text_tab_loaded = "Table loaded: '%s'"
def load_all(master, center, subcenter, master_vers, local_vers, base_path, tabf="eccodes"):
    """Load all given versions of tables"""
    try:
        tparse = parse_modules[tabf]
    except:
        raise BufrTableError("Unknown table parser '%s'!" % tabf)
    tables = Tables(master, master_vers, local_vers, center, subcenter)

    # Table A (centres)
    try:
        mp, _ = tparse.get_file("A", base_path, master, center, subcenter, master_vers, local_vers)
        tparse.load_tab_a(tables, mp)
        logger.info(_text_tab_loaded, mp)
    except Exception as e:
        logger.warning(e)
    #
    # Table B (elements)
    try:
        mp, lp = tparse.get_file("B", base_path, master, center, subcenter, master_vers, local_vers)
        # International (master) table
        tparse.load_tab_b(tables, mp)
        logger.info(_text_tab_loaded, mp)
        # Local table
        if local_vers:
            tparse.load_tab_b(tables, lp)
            logger.info(_text_tab_loaded, lp)
    except Exception as e:
        logger.error(e)
        raise e
    #
    # Table C (operators)
    try:
        mp, _ = tparse.get_file("C", base_path, master, center, subcenter, master_vers, local_vers)
        tparse.load_tab_c(tables, mp)
        logger.info(_text_tab_loaded, mp)
    except Exception as e:
        logger.warning(e)
    #
    # Table D (sequences)
    try:
        mp, lp = tparse.get_file("D", base_path, master, center, subcenter, master_vers, local_vers)
        # International (master) table
        tparse.load_tab_d(tables, mp)
        logger.info(_text_tab_loaded, mp)
        # Local table
        if local_vers:
            tparse.load_tab_d(tables, lp)
            logger.info(_text_tab_loaded, lp)
    except Exception as e:
        logger.error(e)
        raise e
    #
    # Table CF (code/flags)
    try:
        mp, lp = tparse.get_file("CF", base_path, master, center, subcenter, master_vers, local_vers)
        # International (master) table
        tparse.load_tab_cf(tables, mp)
        logger.info(_text_tab_loaded, mp)
        # Local table
        if local_vers:
            tparse.load_tab_cf(tables, lp)
            logger.info(_text_tab_loaded, lp)
    except Exception as er:
        logger.warning(er)

    return tables