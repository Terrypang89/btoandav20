from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import backtrader as bt
from .. import Observer
import pprint
import datetime

class TDSequentialObs(Observer):

    plotinfo = dict(plot=True,
                    subplot=False,
                    plotlegend=False,
                    plotlinelegend=True,
                    plotlinelabels=True,
                    plotvaluetags=True,
                    plotlinevalues=True,
                    plotabove=True,
                    plotname="TD Sequential",)

    lines = (
        'seq_up',               # up count marker
        'seq_down',             # down count marker
        's_buy',                # setup buy marker
        's_sell',               # setup sell marker
        's_buy_perf',           # setup buy perf markerr
        's_sell_perf',          # setup sell perf marker
        's_buy_perf_price',
        's_sell_perf_price',
        's_trend_support',
        's_trend_resistance',
        'cd_seq_up',            # countdown up marker
        'cd_seq_down',          # countdown down marker
        'cd_buy',               # countdown buy marker
        'cd_sell',              # countdown sell marker
        'cd_buy_defer',         # countdown buy defer marker
        'cd_sell_defer',        # countdown sell defer marker
        'cd_cnt_up_recycle',    # countdown up recycle marker
        'cd_cnt_down_recycle',  # countdown down recycle marker
        'risk_level'
    )

    plotlines = dict(
        seq_up=dict(
            marker='*', markersize=4.0, color='black', ls='',),
        seq_down=dict(
            marker='*', markersize=4.0, color='black', ls='',),
        s_buy=dict(
            marker='2', markersize=5.0, color='green',),
        s_sell=dict(
            marker='1', markersize=5.0, color='maroon',),
        s_buy_perf=dict(
            marker='^', markersize=5.0, color='green',),
        s_sell_perf=dict(
            marker='v', markersize=5.0, color='maroon',),
        cd_seq_up=dict(
            marker='*', markersize=5.0, color='blue', ls='',),
        cd_seq_down=dict(
            marker='*', markersize=5.0, color='blue', ls='',),
        cd_buy=dict(
            marker='^', markersize=10.0, color='green',),
        cd_sell=dict(
            marker='v', markersize=10.0, color='maroon',),
        cd_buy_defer=dict(
            marker='$D$', markersize=5.0, color='red', ls='',),
        cd_sell_defer=dict(
            marker='$D$', markersize=5.0, color='red', ls='',),
        cd_count_up_recycle=dict(
            marker='$R$', markersize=5.0, color='blue', ls='',),
        cd_count_down_recycle=dict(
            marker='$R$', markersize=5.0, color='blue', ls='',),
        risk_level=dict(lw=2.0, ls='--',),
    )

    params = dict(
        td_seq=None,
        bardist=0.0006,
        plot_setup_count=True,
        plot_setup_signals=True,
        plot_setup_tdst=True,
        plot_countdown_count=True,
        plot_countdown_signals=True,
        plot_risk_level=True
    )

    def __init__(self):
        self.td_seq = self.p.td_seq
        self.countdown_up_prev = None
        self.countdown_down_prev = None

    def _plotlabel(self):
        return [None]

    def _get_line(self, name):
        line = getattr(self.lines, name, False)
        return line

    def next(self):
        # print(self.td_seq)


        for i in range(0, len(self.datas)):
            self_datanum = "self.data" + str(i)
            txt = list()
            txt.append(f"Data{i}")
            txt.append('{:s}'.format(eval(self_datanum)._name))
            txt.append('%04d' %(len(eval(self_datanum))))
            txt.append('{:f}'.format(self.data_datetime[0]))
            # txt.append('{:s}'.format(self.data[0].datetime.datetime[0].strftime('%Y-%m-%dT%H:%M:%S.%f')))
            # txt.append('%s' %(self.data.datetime.datetime[0].strftime('%Y-%m-%dT%H:%M:%S.%f')))
            txt.append('{:f}'.format(self.data_open[0]))
            # txt.append('{:f}'.format(eval(self_datanum).open[0]))
            txt.append('{:f}'.format(self.data_high[0]))
            # txt.append('{:f}'.format(eval(self_datanum).high[0]))
            txt.append('{:f}'.format(self.data_low[0]))
            # txt.append('{:f}'.format(eval(self_datanum).low[0]))
            txt.append('{:f}'.format(self.data_close[0]))
            # txt.append('{:f}'.format(eval(self_datanum).close[0]))
            # txt.append('{:6d}'.format(int(eval(self_datanum).volume[0])))
            # txt.append('{:d}'.format(int(eval(self_datanum).openinterest[0])))
            print(', '.join(txt))

        if self.p.plot_setup_signals:
            # setup buy / sell signal
            if self.td_seq.l.setup_buy[0]:
                self.l.s_buy[0] = self.data_low[0] - (3 * self.p.bardist)
            if self.td_seq.l.setup_sell[0]:
                self.l.s_sell[0] = self.data_high[0] + (3 * self.p.bardist)
            # setup perfected buy / sell signal
            if self.td_seq.l.setup_buy_perf[0]:
                self.l.s_buy_perf[0] = self.data_low[0] - (4 * self.p.bardist)
            if self.td_seq.l.setup_sell_perf[0]:
                self.l.s_sell_perf[0] = self.data_high[0] + (4 * self.p.bardist)

        # setup count
        if self.p.plot_setup_count:
            # setup count up sequence
            if self.td_seq.setup_count_up[0] > 0:
                self.l.seq_up[0] = self.data_low[0] + self.p.bardist
            # setup count down sequence
            if self.td_seq.setup_count_down[0] > 0:
                self.l.seq_down[0] = self.data_high[0] - self.p.bardist

        # setup trend support / resistance (TDST)
        if self.p.plot_setup_tdst:
            self.l.s_trend_support[0] = self.td_seq.setup_trend_support[0]
            self.l.s_trend_resistance[0] = self.td_seq.setup_trend_resistance[0]

        # countdown count
        if self.p.plot_countdown_count:
            # countdown count up sequence
            if self.td_seq.countdown_count_up_imp[0] >= 0:
                if self.td_seq.countdown_count_up_imp[0] != self.countdown_up_prev:
                    self.l.cd_seq_up[0] = self.data_low[0] + (2 * self.p.bardist)
                self.countdown_up_prev = self.td_seq.countdown_count_up_imp[0]
            # countdown count down sequence
            if self.td_seq.countdown_count_down_imp[0] >= 0:
                if self.td_seq.countdown_count_down_imp[0] != self.countdown_down_prev:
                    self.l.cd_seq_down[0] = self.data_high[0] - (2 * self.p.bardist)
                self.countdown_down_prev = self.td_seq.countdown_count_down_imp[0]

        # countdown signals
        if self.p.plot_countdown_signals:
            # countdown_buy/sell
            if self.td_seq.l.countdown_buy[0]:
                self.l.cd_buy[0] = self.data_low[0] - (4 * self.p.bardist)
            if self.td_seq.l.countdown_sell[0]:
                self.l.cd_sell[0] = self.data_high[0] + (4 * self.p.bardist)

            # countdown_buy_defer/sell_defer
            if self.td_seq.l.countdown_buy_defer[0]:
                self.l.cd_buy_defer[0] = self.data_low[0] - (3 * self.p.bardist)
            if self.td_seq.l.countdown_sell_defer[0]:
                self.l.cd_sell_defer[0] = self.data_high[0] + (3 * self.p.bardist)

            # countdown_up_recycle/down_recycle
            if self.td_seq.l.countdown_count_up_recycle[0]:
                self.l.cd_cnt_up_recycle[0] = self.data_low[0] + (3 * self.p.bardist)
            if self.td_seq.l.countdown_count_down_recycle[0]:
                self.l.cd_cnt_down_recycle[0] = self.data_high[0] - (3 * self.p.bardist)

        # risk level
        if self.p.plot_risk_level:
            self.l.risk_level[0] = self.td_seq.risk_level[0]