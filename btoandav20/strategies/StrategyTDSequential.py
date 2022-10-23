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

import backtrader as bt
from backtrader.observers import *
from backtrader.indicators import *

class StrategyTDSequential(bt.Strategy):

    lines = (
        'setup_sell',                   # sell setup
        'setup_buy',                    # buy setup
        'setup_sell_perf',              # sell setup perfected
        'setup_buy_perf',               # buy setup perfected
        'countdown_sell',               # sell countdown
        'countdown_buy',                # buy countdown
        'countdown_sell_defer',
        'countdown_buy_defer',
        'countdown_count_up_recycle',
        'countdown_count_down_recycle',
    )

    def __init__(self):
        '''Initialization '''
        #  add indicator TDSequentialInd
        self.td_seq = TDSequentialInd()
        #  add observer TDSequentialObs, def _addobserver(self, multi, obscls, *obsargs, **obskwargs):
        # self.data onward will send as parameters (obsargs) to the observer TDSequenctialObs, treated as param 
        self._addobserver(
            False,
            TDSequentialObs,
            self.data,
            td_seq=self.td_seq,
            plot_setup_signals=True, # show setup_buy, setup_sell, setup_buy_perf, setup_sell_perf, 
            plot_setup_count=True,  # SetupShowCount = input(title="Setup: Show Count", type=bool
            plot_setup_tdst=True,   # SetupTrendShow = input(title="Setup Trend: Show", type=bool, defval=true)
            plot_countdown_signals=True,    # CntdwnAggressive = input(title="Countdown: Aggressive", type=bool, defval=false)
            plot_countdown_count=True,  # CntdwnShowCount = input(title="Countdown: Show Count", type=bool, defval=true)
            plot_risk_level=True)   # RiskLevelShow = input(title="Risk Level: Show", type=bool, defval=false)

# PriceSource = input(title="Price: Source", type=source, defval=close)
# SetupBars = input(title="Setup: Bars", type=integer, defval=9, minval=4, maxval=31)
# SetupLookback = input(title="Setup: Lookback Bars", type=integer, defval=4, minval=1, maxval=14)
# SetupEqualEnable = input(title="Setup: Include Equal Price", type=bool, defval=false)
# SetupPerfLookback = input(title="Setup: Perfected Lookback", type=integer, defval=3, minval=1, maxval=14)
# SetupShowCount = input(title="Setup: Show Count", type=bool, defval=true)
# SetupTrendExtend = input(title="Setup Trend: Extend", type=bool, defval=false)
# SetupTrendShow = input(title="Setup Trend: Show", type=bool, defval=true)
# CntdwnBars = input(title="Countdown: Bars", type=integer, defval=13, minval=3, maxval=31)
# CntdwnLookback = input(title="Countdown: Lookback Bars", type=integer, defval=2, minval=1, maxval=30)
# CntdwnQualBar = input(title="Countdown: Qualifier Bar", type=integer, defval=8, minval=3, maxval=30)
# CntdwnAggressive = input(title="Countdown: Aggressive", type=bool, defval=false)
# CntdwnShowCount = input(title="Countdown: Show Count", type=bool, defval=true)
# RiskLevelShow = input(title="Risk Level: Show", type=bool, defval=false)
# Transp = input(title="Transparency", type=integer, defval=0, minval=0, maxval=100)