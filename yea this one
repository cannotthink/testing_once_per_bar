from locale import currency
from operator import index
from telnetlib import BM
from tkinter import Frame
from turtle import back, position
from more_itertools import last
import pandas as pd
from binance import BinanceSocketManager
from binance.client import Client
import numpy as np
import pprint
import matplotlib as plt
import ta 
import time
from datetime import timedelta, datetime
import datetime
import time, schedule
from yea import buy
import pandas_ta as pa
import pandas_ta as ta
import statsmodels.api as sm
import tools
import numpy as np
import os

api_key = 
api_secret = 
client = Client(api_key, api_secret)

posframe = pd.read_csv('position.csv')

def changepos(curr, buy=True):
    if buy:
        posframe.loc[posframe.currency == curr, 'position'] = 1
    else:
        posframe.loc[posframe.currency == curr, 'position'] = 0

    posframe.to_csv('position', index=False)

tf='1m'
def getdata(symbol, tf='1m',start='100 minutes UTC'): 
    frame = pd.DataFrame(client.get_historical_klines(symbol,tf, start)) #original (symbol, '1m', '600 minutes UTC')), with the original df.index[-1] is always on current, with this its lagging 1m
    frame = frame.iloc[:,:6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame.set_index('Time', inplace=True)
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame = frame.astype(float)
    return frame

df = getdata('BTCBUSD')

def applytechnicals1(df):
    df['FASTSMA'] = df.Close.rolling(9).mean()
    df['SLOWSMA'] = df.Close.rolling(50).mean()
    df['SMA20'] = df.Close.rolling(20).mean()
    df['stddev'] = df.Close.rolling(20).std()
    df['Upper'] = df.SMA20 + 2 * df.stddev
    df['Lower'] = df.SMA20 - 2 * df.stddev
    #df['ATR'] = ta.atr(high = df.High, low = df.Low, close = df.Close, length=14)
    #df['Highest'] = df.Close.cummax()  #take the cumulative max
    #df['TSL'] = df['Highest'] * 0.995 #subtract 1% of the max
    #df['exit_signal'] = df['Close'] < df['TSL'] #generate exit signal
    #df['sl'] = df.Close - (df.ATR * 0.2)
    #df['tp'] = df.Close + (df.ATR * 0.2)
    df['lag1'] = df.Close.shift(1)
    df['Shifted_open'] = df.Open.shift(-1)

applytechnicals1(df)
df.dropna(inplace=True)

buytime2 = []
plzwork = []
buydatez = []
last_trades_time = dict()

def trader(curr):
        qty = posframe[posframe.currency == curr].quantity.values[0]
        df = getdata(curr)
        applytechnicals1(df)
        global buyprice, order, TSL, buytime1, buytime2, no, buydatez
        lastrow = df.iloc[-1]
        no = (list(df.index)[-1].to_pydatetime(lambda t: t.strftime('%Y-%m-%d %H:&M')))
        def PeriodSeconds(tf):
            period_seconds = 0
            period_dimension = tf[-1]
            period_qty = int(tf[:-1])
            
            if period_dimension == 'm':
                period_seconds = period_qty * 60
            elif period_dimension == 'h':
                period_seconds = period_qty * 60 * 60
            elif period_dimension == 'd':
                period_seconds = period_qty * 60 * 60 * 24
            elif period_dimension == 'w':
                period_seconds = period_qty * 60 * 60 * 24 * 7
            elif period_dimension == 'M':
                period_seconds = int(period_qty * 60 * 60 * 24 * 30.437)
            
            # print(period_seconds)
            return period_seconds

        def WasOpenTradeThisBar_1(checking_time):
            checking_time = checking_time.replace(second=0,microsecond=0)
            # print(checking_time)
            for timestamp in buydatez:
                if timestamp == checking_time:
                    return True
            return False
        
        def WasOpenTradeThisBar_2(bar_open_time):
            checking_time = 0
            
            for coin in last_trades_time:
                if coin == curr:
                    checking_time = last_trades_time[curr]
            
            if checking_time == 0:
                return False
            
            bar_open_time = datetime.datetime.timestamp(bar_open_time.to_pydatetime())
            next_trade_time = bar_open_time + PeriodSeconds(tf)
            if checking_time <= next_trade_time:
                return True
            return False
        if not posframe[posframe.currency == curr].position.values[0]:
            if (lastrow.Close > lastrow.Lower):   # & (lastrow.Close > df.lag1.iloc[-2]):
                order = client.create_margin_order(symbol=curr,
                side = "BUY", type="MARKET", quantity=qty)
                buyprice = float(order['fills'][0]['price'])
                #buytime1 = int(order['transactTime']) 
                #buytime2.append(pd.to_datetime(index,unit='s'))
                print(order)
                buydatez.append(pd.to_datetime(order['transactTime'],unit='ms'))
                last_trades_time[curr] = datetime.datetime.timestamp(df.index[-1].to_pydatetime())
                #buydatez.append(pd.to_datetime(current_time))
                changepos(curr, buy=True)
            else:
                print(f'NOT IN POSITION {curr} BUT CONDITION NOT FULFILLED')
        else:
            print('cur Close: ' + str(lastrow.Close))
            if lastrow.Close > buyprice:
                buyprice = lastrow.Close # tp 1.0003 is 0.03%  # sl 0.9998 is 0.02%
                print('cur buypr: ' + str(buyprice))
            TSL = buyprice * 0.99999
            if lastrow.Close < TSL:
                order = client.create_margin_order(symbol=curr,
                side = "SELL", type="MARKET", quantity=qty)
                print(order)
                changepos(curr, buy=False)
            print('cur TSL: ' + str(TSL))
            current_time = datetime.datetime.timestamp(df.index[-1].to_pydatetime()) #df.index[-1] lagging 1m behind current time
            current_time += 30.5
            current_time = datetime.datetime.fromtimestamp(current_time)   

            if not posframe[posframe.currency == curr].position.values[0] and (lastrow.Close > lastrow.Lower) and not WasOpenTradeThisBar_1(current_time):
                buyprice = float(order['fills'][0]['price']) #if create order here it starts spamming sell orders?
                buydatez.append(pd.to_datetime(current_time))
                changepos(curr, buy=True)
            
            if not posframe[posframe.currency == curr].position.values[0] and (lastrow.Close > lastrow.Lower) and not WasOpenTradeThisBar_2(df.index[-1]):
                buyprice = float(order['fills'][0]['price']) #if create order here it starts spamming sell orders?
                buydatez.append(pd.to_datetime(current_time))
                changepos(curr, buy=True)
                last_trades_time[curr] = datetime.datetime.timestamp(df.index[-1].to_pydatetime()) 

for coin in posframe.currency:
    trader(coin)

while True:
    trader(coin)
    time.sleep(1)

#error "account has insufficient funds and stops, it has enough funds"
#error "after a sell the tsl,close price keeps printing and doesnt matter if a new bar opens it does not open a new trade it keeps printing the old tsl and clsoe price"
