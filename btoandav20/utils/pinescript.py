#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015-2020 Daniel Rodriguez
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
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import numpy as np

def line2arr(line, size=-1):
    '''
    Creates an numpy array from a backtrader line

    This method wraps the lines array in numpy. This can
    be used for conditions.
    '''
    if size <= 0:
        return np.array(line.array)
    else:
        return np.array(line.get(size=size))


def na(val):
    '''
    RETURNS
    true if x is not a valid number (x is NaN), otherwise false.
    '''
    return val != val


def nz(x, y=None):
    '''
    RETURNS
    Two args version: returns x if it's a valid (not NaN) number, otherwise y
    One arg version: returns x if it's a valid (not NaN) number, otherwise 0
    ARGUMENTS
    x (val) Series of values to process.
    y (float) Value that will be inserted instead of all NaN values in x series.
    '''
    if isinstance(x, np.generic):
        return x.fillna(y or 0)
    if x != x:
        if y is not None:
            return y
        return 0
    return x

def iff(condition, true_value, false_value):
    # cond_len = len(condition)
    if condition:
        return true_value
    else:
        return false_value


def barssince(condition, occurrence=0):
    '''
    Impl of barssince

    RETURNS
    Number of bars since condition was true.
    REMARKS
    If the condition has never been met prior to the current bar, the function returns na.
    '''
    cond_len = len(condition)
    occ = 0
    since = 0
    res = float('nan')
    while cond_len - (since+1) >= 0:
        cond = condition[cond_len-(since+1)]
        # check for nan cond != cond == True when nan
        if cond and not cond != cond:
            if occ == occurrence:
                res = since
                break
            occ += 1
        since += 1
    return res


def valuewhen(condition, source, occurrence=0):
    '''
    Impl of valuewhen
    + added occurrence

    RETURNS
    Source value when condition was true
    '''
    res = float('nan')
    since = barssince(condition, occurrence)
    if since is not None:
        res = source[-(since+1)]
    return res

def highestbars(condition, length):
    '''
    Impl of highestbars

    RETURNS
    Number of bars since highest was true.
    REMARKS
    If the condition has never been met prior to the current bar, the function returns na.
    '''
    cond_len = len(condition)
    since = 0
    res = 0
    prev_cond = condition[cond_len-1]
    print(f"highestbars: cond_len={cond_len}, prev_cond={prev_cond}, length={length}")
    while since < length:
        since += 1
        cond = condition[cond_len-(since+2)]
        if cond and not cond != cond and prev_cond and not prev_cond != prev_cond:
            if cond > prev_cond:
                res = since
            prev_cond = max(cond, prev_cond)
            print(f"highestbars_1: cond={cond}, since={since}, res={res}, prev_cond={prev_cond}")
    return res

def lowestbars(condition, length):
    '''
    Impl of highestbars

    RETURNS
    Number of bars since highest was true.
    REMARKS
    If the condition has never been met prior to the current bar, the function returns na.
    '''
    cond_len = len(condition)
    since = 0
    res = 0
    prev_cond = condition[cond_len-1]
    print(f"lowestbars: cond_len={cond_len}, prev_cond={prev_cond}, length={length}")
    while since < length:
        since += 1
        cond = condition[cond_len-(since+2)]
        if cond and not cond != cond and prev_cond and not prev_cond != prev_cond:
            if cond < prev_cond:
                res = since
            prev_cond = min(cond, prev_cond)
            print(f"lowestbars_1: cond={cond}, since={since}, res={res}, prev_cond={prev_cond}")
    return res