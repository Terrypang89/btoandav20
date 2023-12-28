import backtrader as bt
import backtrader.indicators as btind
# import backtrader.indicators.MovAv as MovAv
from backtradermql5.mt5store import MTraderStore
from backtradermql5.mt5indicator import getMTraderIndicator
from backtradermql5.mt5chart import MTraderChart, ChartIndicator
from backtradermql5.mt5broker import MTraderBroker
from backtradermql5.mt5data import MTraderData
from datetime import datetime, timedelta, timezone
import time
import json
import pprint as pprint
# from bson import json_util
import pandas as pd
import re
import json
import time
import os
from flask import Flask, request
from threading import Timer
import btoandav20

# import config
from handler import *

from src import api_server_start
from src import event_subscribe, event_unsubscribe, event_post
from src import StoppableThread
from src import log , create_logger

StoreCls = btoandav20.stores.OandaV20Store
DataCls = btoandav20.feeds.OandaV20Data
BrokerCls = btoandav20.brokers.OandaV20Broker

TIMECALL = 60
API_PORT = "api-port"
API_REV = "api-rev"

class SmaCross(bt.SignalStrategy):

    params = dict(
        smaperiod=5,
        trade=True,
        stake=0.01,
        exectype=bt.Order.Market,
        stopafter=0,
        valid=True,
        cancel=0,
        donotcounter=False,
        sell=True,
        usebracket=False,
    )

    def get_timestamp(self):
        timestamp = time.strftime("%Y-%m-%d %X")
        return timestamp

    def process_data_received(self, data:dict):
        print(f"on_data_received data = {data}\n")
        if not isinstance(data, dict):
            print(f"Incorrect data({data}) format received, SKIP.")
            return None
        try:
            # check if data ticker is 5m, 30m, 1 day
            self._new_data_received = True
            self._api_data = data
            
            if data["Period"] == "1":
                self._new_data_received_1m = True
                self._api_data_1m = data
                print(f"Detected new data {data['Symbol']} - {data['Period']}\n")
            elif data["Period"] == "5":
                self._new_data_received_5m = True
                self._api_data_5m = data
                print(f"Detected new data {data['Symbol']} - {data['Period']}\n")
            elif data["Period"] == "15":
                self._new_data_received_15m = True
                self._api_data_15m = data
                print(f"Detected new data {data['Symbol']} - {data['Period']}\n")
            elif data["Period"] == "30":
                self._new_data_received_30m = True
                self._api_data_30m = data
                print(f"Detected new data {data['Symbol']} - {data['Period']}\n")
            elif data["Period"] == "60":
                self._new_data_received_1h = True
                self._api_data_1h = data
                print(f"Detected new data {data['Symbol']} - {data['Period']}\n")
            if data["Period"] == "D":
                self._new_data_received_1d = True
                self._api_data_1d = data
                print(f"Detected new data {data['Symbol']} - {data['Period']}\n")
            # return data
        except Exception as err:
            log.error(f"Sent webhook failed, reason: {err}")
        
    def retrieve_data_received(self):
        if self._new_data_received_15m is True:
            self._new_data_received_15m = False
            return self._api_data_15m
        # elif 
        return None

    def __init__(self):
        self.orderid = list()
        self.order = None

        self.counttostop = 0
        self.datastatus = 0

        self._new_data_received = False
        self._api_data = ""
        # self._prev_api_data = ""
        event_subscribe(API_REV, self.process_data_received)
    
        self.buy_order = []
        self.sell_order = []
        self.live_data = False
        self.buy_one = False
        self.sell_one = False

    def next(self):

        updated_data = self.retrieve_data_received()
        log.info(f"UPDATED data = {updated_data}")

        # extract the data, check is there any opentrade, check buy/sell if yes, 
        txt = list()
        if self.live_data:
            txt.append('LIVE :')
            cash = self.broker.getcash()
        else:
            txt.append('NOT LIVE :')
            cash = "NA"
        
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
        print(', '.join(txt))

        # if self.counttostop:  # stop after x live lines
        #     self.counttostop -= 1
        #     if not self.counttostop:
        #         self.env.runstop()
        #         return

        if not self.p.trade:
            return
        
        if not self.live_data:
            return
        
        if self.updated_data is None:
            return

        if self.datastatus and not self.position and len(self.orderid) < 1:
            if not self.p.usebracket:
                if updated_data["Alert"] == "SUPER_BUY":
                    # price = round(self.data0.close[0] * 0.90, 2)
                    price = self.data0.close[0]
                    self.order = self.buy(size=self.p.stake,
                                          exectype=self.p.exectype,
                                          price=price,
                                          valid=self.p.valid)
                elif updated_data["Alert"] == "SUPER_SELL":
                    # price = round(self.data0.close[0] * 1.10, 4)
                    price = self.data0.close[0]
                    self.order = self.sell(size=self.p.stake,
                                           exectype=self.p.exectype,
                                           price=price,
                                           valid=self.p.valid)

            else:
                if updated_data["Alert"] == "SUPER_BUY":
                    print('USING BRACKET')
                    price = self.data0.close[0]
                    self.order, _, _ = self.buy_bracket(size=self.p.stake,
                                                        exectype=bt.Order.Market,
                                                        price=price,
                                                        stopprice=price - 0.10,
                                                        limitprice=price + 0.10,
                                                        valid=self.p.valid)
                elif updated_data["Alert"] == "SUPER_SELL":
                    print('USING BRACKET')
                    price = self.data0.close[0]
                    self.order, _, _ = self.sell_bracket(size=self.p.stake,
                                                        exectype=bt.Order.Market,
                                                        price=price,
                                                        stopprice=price - 0.10,
                                                        limitprice=price + 0.10,
                                                        valid=self.p.valid)

            self.orderid.append(self.order)
        # elif self.position and not self.p.donotcounter:
        #     if self.order is None:
        #         if updated_data["Alert"] == "SUPER_SELL":
        #             self.order = self.sell(size=self.p.stake // 2,
        #                                    exectype=bt.Order.Market,
        #                                    price=self.data0.close[0])
        #         elif updated_data["Alert"] == "SUPER_BUY":
        #             self.order = self.buy(size=self.p.stake // 2,
        #                                   exectype=bt.Order.Market,
        #                                   price=self.data0.close[0])

        #     self.orderid.append(self.order)

        elif self.order is not None:
            if updated_data["Alert"] == "SUPER_BUY" or updated_data["Alert"] == "SUPER_SELL":
                self.cancel(self.order)

        if self.datastatus:
            self.datastatus += 1

        # for data in self.datas:
        #     str_data = str(vars(data))
        #     json_data = json.dumps(str_data, indent=12)
            # print(f'id:{data._id} | tf:{data._timeframe} | com:{data._compression} | {data.datetime.datetime() - timedelta(hours=8)} - {data._name} | Cash {cash} | O: {data.open[0]} H: {data.high[0]} L: {data.low[0]} C: {data.close[0]} V:{data.volume[0]}')

    def notify_store(self, msg, *args, **kwargs):
        print('*' * 5, 'STORE NOTIF notify_store:', msg)

    def notify_order(self, order):
        if order.status in [order.Completed, order.Cancelled, order.Rejected]:
            self.order = None

        print('-' * 50, 'ORDER BEGIN notify_order', datetime.now())
        print(order)
        print('-' * 50, 'ORDER END')

    def notify_trade(self, trade):
        print('-' * 50, 'TRADE BEGIN notify_trade', datetime.now())
        print(trade)
        print('-' * 50, 'TRADE END')

    def notify_data(self, data, status, *args, **kwargs):
        dn = data._name
        dt = datetime.now()
        msg = f'Data Status: {data._getstatusname(status)}'
        print(str(dt) + dn + msg)
        if data._getstatusname(status) == 'LIVE':
            self.live_data = True
            # self.counttostop = self.p.stopafter
            self.datastatus = 1
        else:
            self.live_data = False

def main():
    # run flash server
    thread = StoppableThread(target=api_server_start, args=(API_PORT, API_REV))
    thread.start()
    thread.join()   

    
    with open("../config.json", "r") as file:
        config = json.load(file)

    for attr, value in config.items():
        if value is None or value == "None" or value == "":
            config[f"{attr}"] = None
        print(attr, '=', value)

    cerebro = bt.Cerebro()
    # comment next 2 lines to use backbroker for backtesting with MTraderStore
    
    # setup store
    trade_status = "oanda_demo" if config["practice"] else "oanda_live"

    print("trade_status = %s" %(trade_status))
    storekwargs = dict(
        token=config[f"{trade_status}"]["token"],
        account=config[f"{trade_status}"]["account"],
        practice=config["practice"],
        stream_timeout=10,
    )

    if not config["no_store"]:
        store = StoreCls(**storekwargs)

    # setup broker
    if config["broker"]:
        broker = BrokerCls(**storekwargs)
    else:
        if not config["no_store"]:
            broker = store.getbroker()

    cerebro.setbroker(broker)

    fromdate = None
    if config["fromdate"] and not config["fromdate"] is None:
        dtformat = '%Y-%m-%d' + ('T%H:%M:%S' * ('T' in config["fromdate"]))
        fromdate = datetime.strptime(config["fromdate"], dtformat)

    # setup datafeed
    DataFactory = DataCls if config["no_store"] else store.getdata

    data = DataFactory(
        dataname=config["pairlists"][0], 
        timeframe=bt.TimeFrame.TFrame(config["timeframe"]),
        compression=config["compression"],
        fromdate=fromdate, 
    )

    cerebro.adddata(data)

    cerebro.addstrategy(SmaCross)

    cerebro.run()

if __name__ == "__main__":
    main()