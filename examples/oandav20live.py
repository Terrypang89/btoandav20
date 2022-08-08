#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import json
from pprint import pprint

import backtrader as bt
from backtrader.utils import flushfile  # win32 quick stdout flushing
import btoandav20

StoreCls = btoandav20.stores.OandaV20Store
DataCls = btoandav20.feeds.OandaV20Data
# BrokerCls = btoandav20.brokers.OandaV20Broker

# available timeframes for oanda
TIMEFRAMES = [bt.TimeFrame.Names[bt.TimeFrame.Seconds],
         bt.TimeFrame.Names[bt.TimeFrame.Minutes],
         bt.TimeFrame.Names[bt.TimeFrame.Days],
         bt.TimeFrame.Names[bt.TimeFrame.Weeks],
         bt.TimeFrame.Names[bt.TimeFrame.Months]]


class TestStrategy(bt.Strategy):

    params = dict(
        smaperiod=5,
        trade=False,
        stake=10,
        exectype=bt.Order.Market,
        stopafter=0,
        valid=None,
        cancel=0,
        donotcounter=False,
        sell=False,
        usebracket=False,
    )

    def __init__(self):
        # To control operation entries
        self.orderid = list()
        self.order = None

        self.counttostop = 0
        self.datastatus = 0

        print("smaperiod = %s" %(self.p.smaperiod))
        # Create SMA on 2nd data
        self.sma = bt.indicators.MovAv.SMA(self.data, period=self.p.smaperiod)

        print('--------------------------------------------------')
        print('Strategy Created')
        print('--------------------------------------------------')

    def notify_data(self, data, status, *args, **kwargs):
        print('*' * 5, 'DATA NOTIF notify_data:', data._getstatusname(status), *args)
        if status == data.LIVE:
            self.counttostop = self.p.stopafter
            self.datastatus = 1

    def notify_store(self, msg, *args, **kwargs):
        print('*' * 5, 'STORE NOTIF notify_store:', msg)

    def notify_order(self, order):
        if order.status in [order.Completed, order.Cancelled, order.Rejected]:
            self.order = None

        print('-' * 50, 'ORDER BEGIN notify_order', datetime.datetime.now())
        print(order)
        print('-' * 50, 'ORDER END')

    def notify_trade(self, trade):
        print('-' * 50, 'TRADE BEGIN notify_trade', datetime.datetime.now())
        print(trade)
        print('-' * 50, 'TRADE END')

    def prenext(self):
        self.next(frompre=True)

    def next(self, frompre=False):

        txt = list()
        txt.append('Data0')
        txt.append('%04d' % len(self.data0))
        dtfmt = '%Y-%m-%dT%H:%M:%S.%f'
        txt.append('{:f}'.format(self.data.datetime[0]))
        txt.append('%s' % self.data.datetime.datetime(0).strftime(dtfmt))
        txt.append('{:f}'.format(self.data.open[0]))
        txt.append('{:f}'.format(self.data.high[0]))
        txt.append('{:f}'.format(self.data.low[0]))
        txt.append('{:f}'.format(self.data.close[0]))
        txt.append('{:6d}'.format(int(self.data.volume[0])))
        txt.append('{:d}'.format(int(self.data.openinterest[0])))
        txt.append('{:f}'.format(self.sma[0]))
        print(', '.join(txt))

        if len(self.datas) > 1 and len(self.data1):
            txt = list()
            txt.append('Data1')
            txt.append('%04d' % len(self.data1))
            dtfmt = '%Y-%m-%dT%H:%M:%S.%f'
            txt.append('{}'.format(self.data1.datetime[0]))
            txt.append('%s' % self.data1.datetime.datetime(0).strftime(dtfmt))
            txt.append('{}'.format(self.data1.open[0]))
            txt.append('{}'.format(self.data1.high[0]))
            txt.append('{}'.format(self.data1.low[0]))
            txt.append('{}'.format(self.data1.close[0]))
            txt.append('{}'.format(self.data1.volume[0]))
            txt.append('{}'.format(self.data1.openinterest[0]))
            txt.append('{}'.format(float('NaN')))
            print(', '.join(txt))

        if self.counttostop:  # stop after x live lines
            self.counttostop -= 1
            if not self.counttostop:
                self.env.runstop()
                return

        if not self.p.trade:
            return

        if self.datastatus and not self.position and len(self.orderid) < 1:
            if not self.p.usebracket:
                if not self.p.sell:
                    # price = round(self.data0.close[0] * 0.90, 2)
                    price = self.data0.close[0] - 0.005
                    self.order = self.buy(size=self.p.stake,
                                          exectype=self.p.exectype,
                                          price=price,
                                          valid=self.p.valid)
                else:
                    # price = round(self.data0.close[0] * 1.10, 4)
                    price = self.data0.close[0] - 0.05
                    self.order = self.sell(size=self.p.stake,
                                           exectype=self.p.exectype,
                                           price=price,
                                           valid=self.p.valid)

            else:
                print('USING BRACKET')
                price = self.data0.close[0] - 0.05
                self.order, _, _ = self.buy_bracket(size=self.p.stake,
                                                    exectype=bt.Order.Market,
                                                    price=price,
                                                    stopprice=price - 0.10,
                                                    limitprice=price + 0.10,
                                                    valid=self.p.valid)

            self.orderid.append(self.order)
        elif self.position and not self.p.donotcounter:
            if self.order is None:
                if not self.p.sell:
                    self.order = self.sell(size=self.p.stake // 2,
                                           exectype=bt.Order.Market,
                                           price=self.data0.close[0])
                else:
                    self.order = self.buy(size=self.p.stake // 2,
                                          exectype=bt.Order.Market,
                                          price=self.data0.close[0])

            self.orderid.append(self.order)

        elif self.order is not None and self.p.cancel:
            if self.datastatus > self.p.cancel:
                self.cancel(self.order)

        if self.datastatus:
            self.datastatus += 1

    def start(self):
        if self.data0.contractdetails is not None:
            print('-- Contract Details:')
            print(self.data0.contractdetails)

        header = ['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume',
                  'OpenInterest', 'SMA']
        print(', '.join(header))

        self.done = False

def runstrategy():
    args = parse_args()

    # Create a cerebro
    cerebro = bt.Cerebro()

    with open("config.json", "r") as file:
        config = json.load(file)

    for attr, value in config.items():
        if value is None or value == "None" or value == "":
            config[f"{attr}"] = None
        print(attr, '=', value)

    # select demo or live
    trade_status = "oanda_demo" if config["practice"] else "oanda_live"

    print("trade_status = %s" %(trade_status))
    storekwargs = dict(
        token=config[f"{trade_status}"]["token"],
        account=config[f"{trade_status}"]["account"],
        practice=config["practice"],
        notif_transactions=True,
        stream_timeout=10,
    )

    # get the store from oanda
    if not config["no_store"]:
        store = StoreCls(**storekwargs)

    # setting broker based on storekwargs if no store, else use the broker
    if config["broker"]:
        if config["no_store"]:
            broker = BrokerCls(**storekwargs)
        else:
            broker = store.getbroker()

        cerebro.setbroker(broker)

    if config["timeframe"] is None:
        config["timeframe"] = "Minutes"

    timeframe = bt.TimeFrame.TFrame(config["timeframe"])

    tf1 = config["timeframe1"]
    tf1 = bt.TimeFrame.TFrame(tf1) if tf1 is not None else timeframe

    cp1 = config["compression1"]
    cp1 = cp1 if cp1 is not None else config["compression"]

    if config["resample"] or config["replay"]:
        datatf = datatf1 = bt.TimeFrame.Ticks
        datacomp = datacomp1 = 1
    else:
        datatf = timeframe
        datacomp = config["compression"]
        datatf1 = tf1
        datacomp1 = cp1

    fromdate = None
    if config["fromdate"] and not config["fromdate"] is None:
        dtformat = '%Y-%m-%d' + ('T%H:%M:%S' * ('T' in config["fromdate"]))
        fromdate = datetime.datetime.strptime(config["fromdate"], dtformat)

    if config["todate"] is None:
        yesterday = datetime.datetime.now() - datetime.timedelta(3)
        dtformat = '%Y-%m-%d' + ('T%H:%M:%S' * ('T' in yesterday))
        todate = datetime.datetime.strptime(yesterday, dtformat)
    else:
        dtformat = '%Y-%m-%d' + ('T%H:%M:%S' * ('T' in config["todate"]))
        todate = datetime.datetime.strptime(config["todate"], dtformat)

    print("fromdate = %s to todate = %s" %(fromdate, todate))

    # request data from the oanda if no store else direct get from store
    DataFactory = DataCls if config["no_store"] else store.getdata

    datakwargs = dict(
        timeframe=datatf, 
        compression=datacomp,
        qcheck=config["qcheck"],
        historical=config["historical"],
        fromdate=fromdate,
        todate=todate,
        bidask=config["bidask"],
        useask=config["useask"],
        backfill_start=not config["no_backfill_start"],
        backfill=not config["no_backfill"],
        tz=config["tz"],
        data0=config["pairlists"][0],
        exactbars=config["exactbars"]
    )

    if config["no_store"] and not config["broker"]:   # neither store nor broker
        datakwargs.update(storekwargs)  # pass the store args over the data

    print(datakwargs)

    data0 = DataFactory(dataname=datakwargs["data0"], **datakwargs)

    data1 = None
    if config["data1"] is not None:
        if config["data1"] != config["data0"]:
            datakwargs['timeframe'] = datatf1
            datakwargs['compression'] = datacomp1
            data1 = DataFactory(dataname=config["data1"], **datakwargs)
        else:
            data1 = data0

    rekwargs = dict(
        timeframe=timeframe, 
        compression=config["compression"],
        bar2edge=not config["no_bar2edge"],
        adjbartime=not config["no_adjbartime"],
        rightedge=not config["no_rightedge"],
        takelate=not config["no_takelate"],
    )

    if config["replay"]:
        cerebro.replaydata(data0, **rekwargs)
        if data1 is not None:
            rekwargs['timeframe'] = tf1
            rekwargs['compression'] = cp1
            cerebro.replaydata(data1, **rekwargs)

    elif config["resample"]:
        cerebro.resampledata(data0, **rekwargs)
        if data1 is not None:
            rekwargs['timeframe'] = tf1
            rekwargs['compression'] = cp1
            cerebro.resampledata(data1, **rekwargs)

    else:
        cerebro.adddata(data0)
        if data1 is not None:
            cerebro.adddata(data1)

    
    valid = None
    if config["valid"]:
        valid = datetime.timedelta(seconds=config["valid"])

    # Add the strategy
    cerebro.addstrategy(TestStrategy,
                        smaperiod=config["smaperiod"],
                        trade=config["trade"],
                        exectype=bt.Order.ExecType(config["exectype"]),
                        stake=config["stake"],
                        stopafter=config["stopafter"],
                        valid=valid,
                        cancel=config["cancel"],
                        donotcounter=config["donotcounter"],
                        sell=config["sell"],
                        usebracket=config["usebracket"])

    # Live data ... avoid long data accumulation by switching to "exactbars"
    cerebro.run(exactbars=datakwargs["exactbars"])
    if datakwargs["exactbars"] < 1:  # plotting is possible
        if config["plot"]:
            pkwargs = dict(style='line')
            if config["plot"] is not True:  # evals to True but is not True
                npkwargs = eval('dict(' + config["plot"] + ')')  # args were passed
                pkwargs.update(npkwargs)

            print("***** ploting in progress ***** ")
            cerebro.plot(**pkwargs)
    elif config["plot"] and datakwargs["exactbars"] < 1:
        print("WARNING: please set exactbars lower than 1 for plotting")


def parse_args(pargs=None):
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description='Test Oanda v20 integration')

    parser.add_argument('--exactbars', default=1, type=int,
                        required=False, action='store',
                        help='exactbars level, use 0/-1/-2 to enable plotting')

    parser.add_argument('--stopafter', default=0, type=int,
                        required=False, action='store',
                        help='Stop after x lines of LIVE data')

    parser.add_argument('--no-store',
                        required=False, action='store_true',
                        help='Do not use the store pattern')

    parser.add_argument('--debug',
                        required=False, action='store_true',
                        help='Display all info received from source')

    parser.add_argument('--token', default=None,
                        required=False, action='store',
                        help='Access token to use')

    parser.add_argument('--account', default=None,
                        required=False, action='store',
                        help='Account identifier to use')

    parser.add_argument('--live', default=None,
                        required=False, action='store',
                        help='Go to live server rather than practice')

    parser.add_argument('--qcheck', default=0.5, type=float,
                        required=False, action='store',
                        help=('Timeout for periodic '
                              'notification/resampling/replaying check'))

    parser.add_argument('--data0', default=None,
                        required=False, action='store',
                        help='data 0 into the system')

    parser.add_argument('--data1', default=None,
                        required=False, action='store',
                        help='data 1 into the system')

    parser.add_argument('--timezone', default=None,
                        required=False, action='store',
                        help='timezone to get time output into (pytz names)')

    parser.add_argument('--bidask', default=None,
                        required=False, action='store_true',
                        help='Use bidask ... if False use midpoint')

    parser.add_argument('--useask', default=None,
                        required=False, action='store_true',
                        help='Use the "ask" of bidask prices/streaming')

    parser.add_argument('--no-backfill_start',
                        required=False, action='store_true',
                        help='Disable backfilling at the start')

    parser.add_argument('--no-backfill',
                        required=False, action='store_true',
                        help='Disable backfilling after a disconnection')

    parser.add_argument('--historical',
                        required=False, action='store_true',
                        help='do only historical download')

    parser.add_argument('--fromdate',
                        required=False, action='store',
                        help=('Starting date for historical download '
                              'with format: YYYY-MM-DD[THH:MM:SS]'))

    parser.add_argument('--smaperiod', default=5, type=int,
                        required=False, action='store',
                        help='Period to apply to the Simple Moving Average')

    pgroup = parser.add_mutually_exclusive_group(required=False)

    pgroup.add_argument('--replay',
                        required=False, action='store_true',
                        help='replay to chosen timeframe')

    pgroup.add_argument('--resample',
                        required=False, action='store_true',
                        help='resample to chosen timeframe')

    parser.add_argument('--timeframe', default=TIMEFRAMES[0],
                        choices=TIMEFRAMES,
                        required=False, action='store',
                        help='TimeFrame for Resample/Replay')

    parser.add_argument('--compression', default=5, type=int,
                        required=False, action='store',
                        help='Compression for Resample/Replay')

    parser.add_argument('--timeframe1', default=None,
                        choices=TIMEFRAMES,
                        required=False, action='store',
                        help='TimeFrame for Resample/Replay - Data1')

    parser.add_argument('--compression1', default=None, type=int,
                        required=False, action='store',
                        help='Compression for Resample/Replay - Data1')

    parser.add_argument('--no-takelate',
                        required=False, action='store_true',
                        help=('resample/replay, do not accept late samples'))

    parser.add_argument('--no-bar2edge',
                        required=False, action='store_true',
                        help='no bar2edge for resample/replay')

    parser.add_argument('--no-adjbartime',
                        required=False, action='store_true',
                        help='no adjbartime for resample/replay')

    parser.add_argument('--no-rightedge',
                        required=False, action='store_true',
                        help='no rightedge for resample/replay')

    parser.add_argument('--broker',
                        required=False, action='store_true',
                        help='Use Oanda as broker')

    parser.add_argument('--trade',
                        required=False, action='store_true',
                        help='Do Sample Buy/Sell operations')

    parser.add_argument('--sell',
                        required=False, action='store_true',
                        help='Start by selling')

    parser.add_argument('--usebracket',
                        required=False, action='store_true',
                        help='Test buy_bracket')

    parser.add_argument('--donotcounter',
                        required=False, action='store_true',
                        help='Do not counter the 1st operation')

    parser.add_argument('--exectype', default=bt.Order.ExecTypes[0],
                        choices=bt.Order.ExecTypes,
                        required=False, action='store',
                        help='Execution to Use when opening position')

    parser.add_argument('--stake', default=10, type=int,
                        required=False, action='store',
                        help='Stake to use in buy operations')

    parser.add_argument('--valid', default=None, type=float,
                        required=False, action='store',
                        help='Seconds to keep the order alive (0 means DAY)')

    parser.add_argument('--cancel', default=0, type=int,
                        required=False, action='store',
                        help=('Cancel a buy order after n bars in operation,'
                              ' to be combined with orders like Limit'))

    # Plot options
    parser.add_argument('--plot', '-p', nargs='?', required=False,
                        metavar='kwargs', const=True,
                        help=('Plot the read data applying any kwargs passed\n'
                              '\n'
                              'For example (escape the quotes if needed):\n'
                              '\n'
                              '  --plot style="candle" (to plot candles)\n'))

    if pargs is not None:
        return parser.parse_args(pargs)

    return parser.parse_args()


if __name__ == '__main__':
    runstrategy()
