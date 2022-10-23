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
from . import Indicator, MovAv
from backtrader.utils import *

class TDSequentialInd(Indicator):

    '''
    TD Sequential

    This indicator implements a flexible rendition of TD Sequentials
    Reference: DeMark Indicators by Jason Perl

    based on:
    https://www.tradingview.com/script/t08BkTIg-TD-Sequential/
    http://practicaltechnicalanalysis.blogspot.com/2013/01/tom-demark-sequential.html


    TD Indicators:
    - TD Price Flips (setup_count_up/setup_count_down = 1)
    - TD Setup count up (self.setup_count_up)
    - TD Setup count down (self.setup_count_down)
    - TD Sell Setup (self.setup_sell: price, self.l.setup_sell: signal)
    - TD Sell Setup perfected (self.setup_sell_perf: price, self.l.setup_sell_perf: signal), can be deferred
    - TD Buy Setup (self.setup_buy: price, self.l.setup_buy: signal)
    - TD Buy Setup perfected (self.setup_buy_perf: price, self.l.setup_buy_perf: signal), can be deferred
    - TD Setup Trend support (self.setup_trend_support)
    - TD Setup Trend resistance (self.setup_trend_resistance)
    - TD Countdown up (self.countdown_up)
    - TD Countdown down (self.countdown_down)
    - TD Sell Countdown qualify bar (self.countdown_count_up_imp == self.p.countdown_qual_bar)
    - TD Sell Countdown deferred (self.countdown_sell_defer: price, self.l.countdown_sell_defer: signal)
    - TD Sell Countdown (self.countdown_sell: price, self.l.countdown_sell: signal)
    - TD Buy Countdown qualify bar (self.countdown_count_down_imp == self.p.countdown_qual_bar)
    - TD Buy Countdown deferred (self.countdown_buy_defer: price, self.l.countdown_buy_defer: signal)
    - TD Buy Countdown (self.countdown_buy: price, self.l.countdown_buy: signal)
    - TD Countdown Recycling (self.countdown_count_up_recycle: price, self.l.countdown_count_up_recycle: signal,
                             self.countdown_count_down_recycle: price, self.l.countdown_count_down_recycle: signal)
        Note: Only one aspect of recycling is implemented where,
            if Setup Up/Down Count == 2 * 'Setup: Bars', then the
            present Countdown is cancelled.
            Trend momentum has intensified.
    - TD Risk Level (self.risk_level)
    '''

    DATA_CANDLES = 200  # use up to 200 candles for analysis

    '''
    setupIsPerfected = 2
    setupIsDeferred = 1
    '''
    SETUP_IS_PERFECTED = 2
    SETUP_IS_DEFERRED = 1
    '''
    cntdwnIsQualified = 2
    cntdwnIsDeferred = 1
    '''
    COUNTDOWN_IS_QUALIFIED = 2
    COUNTDOWN_IS_DEFERRED = 1

    plotinfo = dict(subplot=True)

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

    params = dict(
        # data source to use, either close, hgih or low (Default: close)
        data_source='close',
        # TV:PriceSource = input(title="Price: Source", type=source, defval=close)
        # the last Setup count (traditionally 9).
        setup_bars=9,   
        # TV:SetupBars = input(title="Setup: Bars", type=integer, defval=9, minval=4, maxval=31)
        # defines the previous bar to compare for counting (traditionally 4).
        setup_lookback_bars=4,  
        # TV:SetupLookback = input(title="Setup: Lookback Bars", type=integer, defval=4, minval=1, maxval=14)
        # defines the previous count to evaluate for a perfected setup
        # (this count and the next). Traditionally 3, i.e compare
        # count 6 and 7 to count 8 or count 9.
        setup_perf_lookback=3,
        # TV:SetupPerfLookback = input(title="Setup: Perfected Lookback", type=integer, defval=3, minval=1, maxval=14)
        # If enabled, allow >= or <= in price comparisons.
        setup_equal_enable=False,
        # TV:SetupEqualEnable = input(title="Setup: Include Equal Price", type=bool, defval=false)
        # If disabled, only look back to the beginning of
        # this Buy/Sell Setup event
        # to find trends, low(support for Sell) or high(resistance for Buy)
        # If enabled, look back beyond this Buy/Sell Setup event to
        # the previous Setup event of the same kind.
        setup_trend_extend=False,
        # TV:SetupTrendExtend = input(title="Setup Trend: Extend", type=bool, defval=false)
        # the last Countdown count (traditionally 13).
        # Called the Buy/Sell Countdown event in this code, i.e. the
        # last up/down count becomes the Buy/Sell Countdown event.
        countdown_bars=13,
        # TV:CntdwnBars = input(title="Countdown: Bars", type=integer, defval=13, minval=3, maxval=31)
        # define previous bar to compare for counting (traditionally 2).
        countdown_lookback_bars=2,
        # TV:CntdwnLookback = input(title="Countdown: Lookback Bars", type=integer, defval=2, minval=1, maxval=30)
        # the bar in the Countdown sequence used to qualifiy the price
        # of the Buy/Sell Countdown event(traditionally 8).
        # If a countdown event doesn't qualify, counting continues.
        # Note: If the Qualifier Bar is set >= "countdown_lookback_bars",
        # qualification is disabled. Countdown events are still
        # determined, just not qualified.
        countdown_qual_bar=8,
        # CntdwnQualBar = input(title="Countdown: Qualifier Bar", type=integer, defval=8, minval=3, maxval=30)
        # Use aggressive comparison. E.g. for Sell Countdown,
        # instead of "Price: Source" >= high of "countdown_lookback_bars",
        # use high >= high of "countdown_lookback_bars". Disabled by default.
        countdown_aggressive=False,
    )

    def __init__(self):
        super().__init__()
        self.addminperiod(self.p.setup_lookback_bars + 1)

        # data source to use
        if self.p.data_source == 'high':
            self.source = self.data_high
        elif self.p.data_source == 'low':
            self.source = self.data_low
        else:
            self.source = self.data_close

        # setup prices
        self.setup_price_up = (
            self.source(0) > self.source(-self.p.setup_lookback_bars))
        self.setup_price_down = (
            self.source(0) < self.source(-self.p.setup_lookback_bars))
        self.setup_price_equal = (
            self.source(0) == self.source(-self.p.setup_lookback_bars))

        # countdown prices
        if self.p.countdown_aggressive:
            self.countdown_price_up = (
                self.data_high(0)
                >= self.data_high(-self.p.countdown_lookback_bars))
            self.countdown_price_down = (
                self.data_low(0)
                <= self.data_low(-self.p.countdown_lookback_bars))
        else:
            self.countdown_price_up = (
                self.source(0)
                >= self.data_high(-self.p.countdown_lookback_bars))
            self.countdown_price_down = (
                self.source(0)
                <= self.data_low(-self.p.countdown_lookback_bars))

        # indicators
        self.tr = bt.ind.TrueRange()

        # values
        self.setup_sell = bt.LineNum(float('nan'))
        self.setup_buy = bt.LineNum(float('nan'))
        self.setup_count_up = bt.LineNum(float('nan'))
        self.setup_count_down = bt.LineNum(float('nan'))
        self.setup_sell_perf_price = bt.LineNum(float('nan'))
        self.setup_sell_perf_mask = bt.LineNum(float('nan'))
        self.setup_sell_perf = bt.LineNum(float('nan'))
        self.setup_buy_perf_price = bt.LineNum(float('nan'))
        self.setup_buy_perf_mask = bt.LineNum(float('nan'))
        self.setup_buy_perf = bt.LineNum(float('nan'))
        self.setup_sell_count = bt.LineNum(float('nan'))
        self.setup_buy_count = bt.LineNum(float('nan'))
        self.setup_trend_support = bt.LineNum(float('nan'))
        self.setup_trend_resistance = bt.LineNum(float('nan'))
        self.countdown_count_up = bt.LineNum(float('nan'))
        self.countdown_count_down = bt.LineNum(float('nan'))
        self.countdown_count_up_imp = bt.LineNum(float('nan'))
        self.countdown_count_down_imp = bt.LineNum(float('nan'))
        self.countdown_count_up_recycle = bt.LineNum(float('nan'))
        self.countdown_count_down_recycle = bt.LineNum(float('nan'))
        self.countdown_sell = bt.LineNum(float('nan'))
        self.countdown_sell_defer = bt.LineNum(float('nan'))
        self.countdown_sell_qual_price = bt.LineNum(float('nan'))
        self.countdown_sell_qual_mask = bt.LineNum(float('nan'))
        self.countdown_sell_qual_mask_imp = bt.LineNum(float('nan'))
        self.countdown_buy = bt.LineNum(float('nan'))
        self.countdown_buy_defer = bt.LineNum(float('nan'))
        self.countdown_buy_qual_price = bt.LineNum(float('nan'))
        self.countdown_buy_qual_mask = bt.LineNum(float('nan'))
        self.countdown_buy_qual_mask_imp = bt.LineNum(float('nan'))
        self.risk_level = bt.LineNum(float('nan'))

    def next(self):

        #
        # ---- TD Setups ----------------------------
        #

        if self.p.setup_equal_enable:
            if (self.setup_price_up[0]
                or (self.setup_count_up[-1]
                    and self.setup_price_equal[0])):
                self.setup_count_up[0] = nz(self.setup_count_up[-1]) + 1
            if (self.setup_price_down[0]
                or (self.setup_count_down[-1]
                    and self.setup_price_equal[0])):
                self.setup_count_down[0] = nz(self.setup_count_down[-1]) + 1
        else:
            if self.setup_price_up[0]:
                self.setup_count_up[0] = nz(self.setup_count_up[-1]) + 1
            if self.setup_price_down[0]:
                self.setup_count_down[0] = nz(self.setup_count_down[-1]) + 1

        if self.setup_count_up[0] == self.p.setup_bars:
            setupCountUp = line2arr(self.setup_count_up, self.DATA_CANDLES)
            priceSource = line2arr(self.source, self.DATA_CANDLES)
            self.setup_sell[0] = valuewhen(
                setupCountUp == self.p.setup_bars,
                priceSource,
                0)

        if self.setup_count_down[0] == self.p.setup_bars:
            setupCountDown = line2arr(self.setup_count_down, self.DATA_CANDLES)
            priceSource = line2arr(self.source, self.DATA_CANDLES)
            self.setup_buy[0] = valuewhen(
                setupCountDown == self.p.setup_bars,
                priceSource,
                0)

        self.setup_sell_count[0] = barssince(
            line2arr(self.setup_sell, self.DATA_CANDLES))
        self.setup_buy_count[0] = barssince(
            line2arr(self.setup_buy, self.DATA_CANDLES))
        if self.setup_count_up[0] == self.p.setup_bars:
            val = None
            setupCountUp = line2arr(self.setup_count_up, self.DATA_CANDLES)
            high = line2arr(self.data.high, self.DATA_CANDLES)
            cond1 = valuewhen(
                setupCountUp == (self.p.setup_bars
                                 - self.p.setup_perf_lookback),
                high, 0)
            cond2 = valuewhen(
                setupCountUp == (self.p.setup_bars
                                 - self.p.setup_perf_lookback + 1),
                high, 0)
            if (cond1 >= cond2):
                val = cond1
            else:
                val = cond2
            self.setup_sell_perf_price[0] = val
        else:
            self.setup_sell_perf_price[0] = nz(self.setup_sell_perf_price[-1])

        if self.setup_count_down[0] == self.p.setup_bars:
            val = None
            setupCountDown = line2arr(self.setup_count_down, self.DATA_CANDLES)
            low = line2arr(self.data.high, self.DATA_CANDLES)
            cond1 = valuewhen(
                setupCountDown == (self.p.setup_bars
                                   - self.p.setup_perf_lookback),
                low, 0)
            cond2 = valuewhen(
                setupCountDown == (self.p.setup_bars
                                   - self.p.setup_perf_lookback + 1),
                low, 0)
            if cond1 >= cond2:
                val = cond1
            else:
                val = cond2
            self.setup_buy_perf_price[0] = val
        else:
            self.setup_buy_perf_price[0] = nz(self.setup_buy_perf_price[-1])

        if not (nz(self.setup_sell_perf_mask[-1])
                >= self.SETUP_IS_PERFECTED or (not na(self.setup_buy[0]))):
            val = None
            if self.setup_count_up[0] == self.p.setup_bars:
                high = line2arr(self.data_high, self.DATA_CANDLES)
                setupCountUp = line2arr(
                    self.setup_count_up, self.DATA_CANDLES)
                if (
                    (valuewhen(setupCountUp == (self.p.setup_bars-1), high, 0)
                        >= self.setup_sell_perf_price[0])
                    or (valuewhen(setupCountUp == self.p.setup_bars, high, 0)
                        >= self.setup_sell_perf_price[0])):
                    val = self.SETUP_IS_PERFECTED
                else:
                    val = self.SETUP_IS_DEFERRED
            elif not na(self.setup_sell_perf_mask[-1]):
                if self.data_high[0] >= self.setup_sell_perf_price[0]:
                    val = self.SETUP_IS_PERFECTED
                else:
                    val = self.setup_sell_perf_mask[-1]
            if val is not None:
                self.setup_sell_perf_mask[0] = val

        if not (nz(self.setup_buy_perf_mask[-1])
                >= self.SETUP_IS_PERFECTED or (not na(self.setup_sell[0]))):
            val = None
            if self.setup_count_down[0] == self.p.setup_bars:
                low = line2arr(self.data_low, self.DATA_CANDLES)
                setupCountDown = line2arr(
                    self.setup_count_down, self.DATA_CANDLES)
                if (
                    (valuewhen(setupCountDown == (self.p.setup_bars-1), low, 0)
                        <= self.setup_buy_perf_price[0]) or
                    (valuewhen(setupCountDown == self.p.setup_bars, low, 0)
                        <= self.setup_buy_perf_price[0])):
                    val = self.SETUP_IS_PERFECTED
                else:
                    val = self.SETUP_IS_DEFERRED
            elif not na(self.setup_sell_perf_mask[-1]):
                if self.data_low[0] >= self.setup_sell_perf_price[0]:
                    val = self.SETUP_IS_PERFECTED
                else:
                    val = self.setup_buy_perf_mask[-1]
            if val is not None:
                self.setup_buy_perf_mask[0] = val

        if self.setup_sell_perf_mask[0] == self.SETUP_IS_PERFECTED:
            self.setup_sell_perf[0] = self.source[0]
        if self.setup_buy_perf_mask[0] == self.SETUP_IS_PERFECTED:
            self.setup_buy_perf[0] = self.source[0]
        if self.setup_sell[0]:
            if self.p.setup_trend_extend and self.setup_sell_count[-1] > 0:
                extend = int((
                    ((self.setup_sell_count[-1]
                      - (self.setup_sell_count[-1] % self.p.setup_bars))
                     / self.p.setup_bars)
                    + 1) * self.p.setup_bars)
                self.setup_trend_support[0] = min(
                    self.data_low.get(size=extend))
            else:
                self.setup_trend_support[0] = min(
                    self.data_low.get(size=self.p.setup_bars))
        else:
            self.setup_trend_support[0] = nz(self.setup_trend_support[-1])

        if self.setup_buy[0]:
            if self.p.setup_trend_extend and self.setup_buy_count[-1] > 0:
                extend = int((
                    ((self.setup_buy_count[-1]
                      - (self.setup_buy_count[-1] % self.p.setup_bars))
                     / self.p.setup_bars)
                    + 1) * self.p.setup_bars)
                self.setup_trend_resistance[0] = max(
                    self.data_high.get(size=extend))
            else:
                self.setup_trend_resistance[0] = max(
                    self.data_high.get(size=self.p.setup_bars))
        else:
            self.setup_trend_resistance[0] = nz(self.setup_trend_resistance[-1])

        if self.setup_count_up[0] == (2 * self.p.setup_bars):
            setupCountUp = line2arr(self.setup_count_up, self.DATA_CANDLES)
            priceSource = line2arr(self.source, self.DATA_CANDLES)
            self.countdown_count_up_recycle[0] = (
                valuewhen(
                    (setupCountUp == (2 * self.p.setup_bars)),
                    priceSource,
                    0)
            )
        if self.setup_count_down[0] == (2 * self.p.setup_bars):
            setupCountDown = line2arr(self.setup_count_down, self.DATA_CANDLES)
            priceSource = line2arr(self.source, self.DATA_CANDLES)
            self.countdown_count_down_recycle[0] = (
                valuewhen(
                    (setupCountDown == (2 * self.p.setup_bars)),
                    priceSource,
                    0)
            )

        if na(self.countdown_price_up[0]):
            self.countdown_count_up[0] = self.countdown_count_up[-1]
        else:
            val = None
            if not (
                    (not na(self.setup_buy[0])
                        or (self.source[0] < self.setup_trend_support[0]))
                    or (not na(self.countdown_count_up_recycle[0]))):
                if not na(self.setup_sell[0]):
                    if self.countdown_price_up[0]:
                        val = 1
                    else:
                        val = 0
                elif not na(self.countdown_count_up[-1]):
                    if self.countdown_price_up[0]:
                        val = self.countdown_count_up[-1] + 1
                    else:
                        val = self.countdown_count_up[-1]
            if val is not None:
                self.countdown_count_up[0] = val
        if na(self.countdown_price_down[0]):
            self.countdown_count_down[0] = self.countdown_count_down[-1]
        else:
            val = None
            if not (
                    (not na(self.setup_sell[0])
                        or (self.source[0] > self.setup_trend_resistance[0]))
                    or (not na(self.countdown_count_down_recycle[0]))):
                if not na(self.setup_buy[0]):
                    if self.countdown_price_down[0]:
                        val = 1
                    else:
                        val = 0
                elif not na(self.countdown_count_down[-1]):
                    if self.countdown_price_down[0]:
                        val = self.countdown_count_down[-1] + 1
                    else:
                        val = self.countdown_count_down[-1]
            if val is not None:
                self.countdown_count_down[0] = val

        if self.countdown_price_up[0]:
            self.countdown_count_up_imp[0] = self.countdown_count_up[0]
        if self.countdown_price_down[0]:
            self.countdown_count_down_imp[0] = self.countdown_count_down[0]
    
        if self.p.countdown_qual_bar < self.p.countdown_bars:

            if self.countdown_count_up_imp[0] == self.p.countdown_qual_bar:
                cntdwnCountUpImp = line2arr(
                    self.countdown_count_up_imp,
                    self.DATA_CANDLES)
                priceSource = line2arr(
                    self.source,
                    self.DATA_CANDLES)
                self.countdown_sell_qual_price[0] = valuewhen(
                    cntdwnCountUpImp == self.p.countdown_qual_bar,
                    priceSource,
                    0)
            else:
                self.countdown_sell_qual_price[0] = self.countdown_sell_qual_price[-1]

            if self.countdown_count_down_imp[0] == self.p.countdown_qual_bar:
                cntdwnCountDownImp = line2arr(
                    self.countdown_count_down_imp,
                    self.DATA_CANDLES)
                priceSource = line2arr(
                    self.source,
                    self.DATA_CANDLES)
                self.countdown_buy_qual_price[0] = valuewhen(
                    cntdwnCountDownImp == self.p.countdown_qual_bar,
                    priceSource,
                    0)
            else:
                self.countdown_buy_qual_price[0] = self.countdown_buy_qual_price[-1]

            if not ((nz(self.countdown_sell_qual_mask[-1])
                     >= self.COUNTDOWN_IS_QUALIFIED)
                    or na(self.countdown_count_up[-1])):
                val = None
                cntdwnCountUpImp = line2arr(
                    self.countdown_count_up_imp, self.DATA_CANDLES)
                high = line2arr(self.data_high, self.DATA_CANDLES)
                if self.countdown_count_up_imp[0] == self.p.countdown_bars:
                    if (valuewhen(
                            cntdwnCountUpImp == self.p.countdown_bars,
                            high,
                            0)) >= self.countdown_sell_qual_price[0]:
                        val = self.COUNTDOWN_IS_QUALIFIED
                    else:
                        val = self.COUNTDOWN_IS_DEFERRED
                elif not na(self.countdown_sell_qual_mask[-1]):
                    if self.countdown_count_up_imp[0] > self.p.countdown_bars:
                        if (valuewhen(
                                cntdwnCountUpImp > self.p.countdown_bars,
                                high,
                                0)) >= self.countdown_sell_qual_price[0]:
                            val = self.COUNTDOWN_IS_QUALIFIED
                        else:
                            val = self.countdown_sell_qual_mask[-1]
                    else:
                        val = self.countdown_sell_qual_mask[-1]
                if val is not None:
                    self.countdown_sell_qual_mask[0] = val

            if not ((nz(self.countdown_buy_qual_mask[-1])
                     >= self.COUNTDOWN_IS_QUALIFIED)
                    or na(self.countdown_count_down[-1])):
                val = None
                cntdwnCountDownImp = line2arr(
                    self.countdown_count_down_imp, self.DATA_CANDLES)
                low = line2arr(self.data_low, self.DATA_CANDLES)
                if self.countdown_count_down_imp[0] == self.p.countdown_bars:
                    if (valuewhen(
                            cntdwnCountDownImp == self.p.countdown_bars,
                            low,
                            0)) <= self.countdown_buy_qual_price[0]:
                        val = self.COUNTDOWN_IS_QUALIFIED
                    else:
                        val = self.COUNTDOWN_IS_DEFERRED
                elif not na(self.countdown_buy_qual_mask[-1]):
                    if self.countdown_count_down_imp[0] > self.p.countdown_bars:
                        if (valuewhen(
                                cntdwnCountDownImp > self.p.countdown_bars,
                                low,
                                0)) <= self.countdown_buy_qual_price[0]:
                            val = self.COUNTDOWN_IS_QUALIFIED
                        else:
                            val = self.countdown_buy_qual_mask[-1]
                    else:
                        val = self.countdown_buy_qual_mask[-1]
                if val is not None:
                    self.countdown_buy_qual_mask[0] = val
        else:
            if self.countdown_count_up[0] == self.p.countdown_bars:
                self.countdown_sell_qual_mask[0] = self.COUNTDOWN_IS_QUALIFIED
            if self.countdown_count_down[0] == self.p.countdown_bars:
                self.countdown_buy_qual_mask[0] = self.COUNTDOWN_IS_QUALIFED

        if self.countdown_count_up_imp[0]:
            self.countdown_sell_qual_mask_imp[0] = self.countdown_sell_qual_mask[0]
        if self.countdown_count_down_imp[0]:
            self.countdown_buy_qual_mask_imp[0] = self.countdown_buy_qual_mask[0]
        if self.countdown_sell_qual_mask_imp[0] == self.COUNTDOWN_IS_QUALIFIED:
            cntdwnSellQualMaskImp = line2arr(
                self.countdown_sell_qual_mask_imp, self.DATA_CANDLES)
            priceSource = line2arr(
                self.source, self.DATA_CANDLES)
            self.countdown_sell[0] = valuewhen(
                cntdwnSellQualMaskImp == self.COUNTDOWN_IS_QUALIFIED,
                priceSource,
                0)
        if self.countdown_sell_qual_mask_imp[0] == self.COUNTDOWN_IS_DEFERRED:
            cntdwnSellQualMaskImp = line2arr(
                self.countdown_sell_qual_mask_imp, self.DATA_CANDLES)
            priceSource = line2arr(
                self.source, self.DATA_CANDLES)
            self.countdown_sell_defer[0] = valuewhen(
                cntdwnSellQualMaskImp == self.COUNTDOWN_IS_DEFERRED,
                priceSource,
                0)
    
        if self.countdown_buy_qual_mask_imp[0] == self.COUNTDOWN_IS_QUALIFIED:
            cntdwnBuyQualMaskImp = line2arr(
                self.countdown_buy_qual_mask_imp, self.DATA_CANDLES)
            priceSource = line2arr(
                self.source, self.DATA_CANDLES)
            self.countdown_buy[0] = valuewhen(
                cntdwnBuyQualMaskImp == self.COUNTDOWN_IS_QUALIFIED,
                priceSource,
                0)
        if self.countdown_buy_qual_mask_imp[0] == self.COUNTDOWN_IS_DEFERRED:
            cntdwnBuyQualMaskImp = line2arr(
                self.countdown_buy_qual_mask_imp, self.DATA_CANDLES)
            priceSource = line2arr(
                self.source, self.DATA_CANDLES)
            self.countdown_buy_defer[0] = valuewhen(
                cntdwnBuyQualMaskImp == self.COUNTDOWN_IS_DEFERRED,
                priceSource,
                0)

        if self.setup_sell[0] or self.countdown_count_up_recycle[0]:
            high = line2arr(self.data_high, self.p.setup_bars)
            tr = line2arr(self.tr, self.p.setup_bars)
            highest = max(high)
            self.risk_level[0] = highest + valuewhen(high == highest, tr, 0)
        elif self.setup_buy[0] or self.countdown_count_down_recycle[0]:
            low = line2arr(self.data_low, self.p.setup_bars)
            tr = line2arr(self.tr, self.p.setup_bars)
            lowest = min(low)
            self.risk_level[0] = lowest - valuewhen(low == lowest, tr, 0)
        elif self.countdown_sell[0]:
            high = line2arr(self.data_high, self.p.countdown_bars)
            tr = line2arr(self.tr, self.p.countdown_bars)
            highest = max(high)
            self.risk_level[0] = highest + valuewhen(high == highest, tr, 0)
        elif self.countdown_buy[0]:
            low = line2arr(self.data_low, self.p.countdown_bars)
            tr = line2arr(self.tr, self.p.countdown_bars)
            lowest = min(low)
            self.risk_level[0] = lowest - valuewhen(low == lowest, tr, 0)
        else:
            self.risk_level[0] = nz(self.risk_level[-1], self.data_low[0])


        # setup_sell
        self.l.setup_sell[0] = 0
        if not na(self.setup_sell[0]):
            self.l.setup_sell[0] = 1
        # setup_buy
        self.l.setup_buy[0] = 0
        if not na(self.setup_buy[0]):
            self.l.setup_buy[0] = 1
        # setup_sell_perf
        self.l.setup_sell_perf[0] = 0
        if not na(self.setup_sell_perf[0]):
            self.l.setup_sell_perf[0] = 1
        # setup_buy_perf
        self.l.setup_buy_perf[0] = 0
        if not na(self.setup_buy_perf[0]):
            self.l.setup_buy_perf[0] = 1
        # countdown_sell
        self.l.countdown_sell[0] = 0
        if not na(self.countdown_sell[0]):
            self.l.countdown_sell[0] = 1
        # countdown_buy
        self.l.countdown_buy[0] = 0
        if not na(self.countdown_buy[0]):
            self.l.countdown_buy[0] = 1
        # countdown_sell_defer
        self.l.countdown_sell_defer[0] = 0
        if not na(self.countdown_sell_defer[0]):
            self.l.countdown_sell_defer[0] = 1
        # countdown_buy_defer
        self.l.countdown_buy_defer[0] = 0
        if not na(self.countdown_buy_defer[0]):
            self.l.countdown_buy_defer[0] = 1
        # countdown_count_up_recycle
        self.l.countdown_count_up_recycle[0] = 0
        if not na(self.countdown_count_up_recycle[0]):
            self.l.countdown_count_up_recycle[0] = 1
        # countdown_count_down_recycle
        self.l.countdown_count_down_recycle[0] = 0
        if not na(self.countdown_count_down_recycle[0]):
            self.l.countdown_count_down_recycle[0] = 1