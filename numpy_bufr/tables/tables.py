"""This is a modified version of the original script by Alexander Maul. You can find the original script here: https://github.com/pytroll/trollbufr
"""

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
logger = logging.getLogger("trollbufr")

class Tables(object):
    # Recocnized types
    type_list = ("double", "long", "string", "code", "flag")

    def __init__(self, master=0, master_vers=0, local_vers=0, centre=0, subcentre=0):
        '''Constructor'''
        self._master = master
        self._vers_master = master_vers
        self._vers_local = local_vers
        self._centre = centre
        self._centre_sub = subcentre
        
        # { code -> meaning }
        self.tab_a = dict()
        # { desc -> TabBelem }
        self.tab_b = dict()
        # { desc -> (name, definition) }
        self.tab_c = dict()
        # { desc -> (desc, ...) }
        self.tab_d = dict()
        # { desc -> {num:value} }
        self.tab_cf = dict()


    def lookup_codeflag(self, descr, val):
        """Interprets value val according the code/flag tables.
        Returns val if it's not of type code table or flag table.
        """
        sval = val
        if not isinstance(descr, int):
            descr = int(descr)
        if descr < 100000:
            b = self.tab_b[descr]
            if self.tab_cf.get(descr) is None:
                return sval
            if b.typ == "code":
                sval = self.tab_cf[descr].get(val)
                logger.debug("CODE %06d: %d -> %s", descr, val, sval)
            elif b.typ == "flag":
                vl = []
                for k, v in self.tab_cf[descr].items():
                    if val & (1 << (b.width - k)):
                        vl.append(v)
                sval = "|".join(vl)
                logger.debug("FLAG %06d: %d -> %s", descr, val, sval)
        return sval or "N/A"

    def lookup_elem(self, descr):
        """Returns name und unit associated with table B or C descriptor."""
        if descr < 100000:
            b = self.tab_b.get(descr)
            if b is None:
                return ("UNKN", "")
            if b.abbrev is not None:
                return (b.abbrev  , b.unit)
            else:
                return (b.full_name, b.unit)
        elif descr >= 200000 and descr < 300000:
            c = self.tab_c.get(descr)
            if c is None:
                return ("UNKN", "")
            return (c[0], "")
        else:
            return (None, None)

    def lookup_common(self, val):
        """Returns meaning for data category value."""
        a = self.tab_a.get(val)
        logger.debug("COMMONS %d -> %s", val, a)
        return a or "UNKN"


class TabBelem(object):
    def __init__(self, descr, typ, unit, abbrev, full_name, scale, refval, width):
        _type_dwd = { "A":'string', "N":"???", "C":"code", "F":"flag"}
        self.descr = descr
        if typ in _type_dwd:
            if typ == "N":
                if scale > 0:
                    self.typ = "double"
                else:
                    self.typ = "long"
            else:
                self.typ = _type_dwd[typ]
        else:
            self.typ = typ
        if self.typ not in Tables.type_list:
            raise BaseException("Invalid entry typ '%s'" % self.typ)
        self.unit = unit
        self.abbrev = abbrev
        self.full_name = full_name
        self.scale = scale
        self.refval = refval
        self.width = width

    def __str__(self):
        if isinstance(self.descr, int):
            return "%06d : '%s' (%s, %s, %s, %s) [%s]" % (self.descr, self.full_name, self.typ, self.scale, self.width, self.refval, self.unit)
        else:
            return "%s : '%s' (%s, %s, %s, %s) [%s]" % (self.descr, self.full_name, self.typ, self.scale, self.width, self.refval, self.unit)
        
        
def get_descr_full(tables,description):
    """List descriptors, with unit and name/description"""
    desc_text = []
    for d in description:
        d = int(d)
        
        if d > 0 and d < 100000:
            desc_text.append(str(tables.tab_b[d]))
        elif d >= 100000 and d < 200000:
            lm = d // 1000 - 100
            ln = d % 1000
            desc_text.append("%06d : LOOP, %d desc., %d times" % (d, lm , ln))
        elif d >= 200000 and d < 300000:
            en = tables.tab_c.get(d)
            am = d // 1000 - 200
            an = d % 1000
            if en is None:
                en = (str(am), "")
            if d < 222000:
                desc_text.append("%06d : OPERATOR %s: %d" % (d, en[0], an))
            else:
                desc_text.append("%06d : OPERATOR '%s'" % (d, en[0]))
    return desc_text