#!/usr/bin/env python

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import argparse
import datetime
import json
from pprint import pprint
import sys
import numpy as np
 
import backtrader as bt
from backtrader.utils import flushfile  # win32 quick stdout flushing
import btoandav20
from btoandav20.observers.TDSequentialObs import *

StoreCls = btoandav20.stores.OandaV20Store
DataCls = btoandav20.feeds.OandaV20Data
BrokerCls = btoandav20.brokers.OandaV20Broker

# available timeframes for oanda
TIMEFRAMES = [bt.TimeFrame.Names[bt.TimeFrame.Seconds],
         bt.TimeFrame.Names[bt.TimeFrame.Minutes],
         bt.TimeFrame.Names[bt.TimeFrame.Days],
         bt.TimeFrame.Names[bt.TimeFrame.Weeks],
         bt.TimeFrame.Names[bt.TimeFrame.Months]]

def runstrategy():
    args = parse_args()

    # Create a cerebro
    cerebro = bt.Cerebro()

    datastore = {}

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
    pairlists = config["pairlists"]
    multi_timeframes = config["multi_timeframes"]
    multi_compressions = config["multi_compressions"]

    # check multi_timeframes, multi_compressions
    multiparameter = [ "pairlists", "multi_timeframes", "multi_compressions"]
    for i in range(0, len(multiparameter)):
        if config[f"{multiparameter[i]}"] is None:
            print(f"{i} is Null!!")
            exit()
    
    if len(eval(multiparameter[1])) != len(eval(multiparameter[2])):
        print(f"length of {multiparameter[1]} = %s is not matching {multiparameter[2]} = %s " %(len(eval(multiparameter[1])), len(eval(multiparameter[2]))))
        exit()

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
        exactbars=config["exactbars"]
    )

    data_num = 0
    for i in config[f"{multiparameter[0]}"]:
        for j, k in zip(config[f"{multiparameter[1]}"], config[f"{multiparameter[2]}"]):
            temp_datanum = "data"+ str(data_num)
            datakwargs["dataname"] = f"{i}"
            datakwargs["timeframe"] = bt.TimeFrame.TFrame(j)
            datakwargs["compression"] = int(f"{k}")
            datakwargs.update(storekwargs)

            exec(temp_datanum + " = DataFactory(**datakwargs)")
            exec("cerebro.adddata(" + temp_datanum + ")")
            print("temp_datanum = %s, dataname = %s, timeframe = %s, compression = %s" %(temp_datanum, datakwargs["dataname"], datakwargs["timeframe"], datakwargs["compression"]))
            data_num += 1

    if config["no_store"] and not config["broker"]:   # neither store nor broker
        datakwargs.update(storekwargs)  # pass the store args over the data

    print(datakwargs)

    rekwargs = dict(
        timeframe=timeframe, 
        compression=config["compression"],
        bar2edge=not config["no_bar2edge"],
        adjbartime=not config["no_adjbartime"],
        rightedge=not config["no_rightedge"],
        takelate=not config["no_takelate"],
    )
    
    valid = None
    if config["valid"]:
        valid = datetime.timedelta(seconds=config["valid"])

    cerebro.addstrategy(btoandav20.strategies.StrategyTDSequential)

    # Live data ... avoid long data accumulation by switching to "exactbars"
    cerebro.run(exactbars=datakwargs["exactbars"])
    if datakwargs["exactbars"] < 1:  # plotting is possible
        if config["plot"]:
            pkwargs = dict(style='candlestick')
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
    
    parser.add_argument('--occurrence', default=None,
                        required=False, action='store',
                        help='occurrence 0 into the system')

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

    parser.add_argument('--smavalue', default=5, type=int,
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
