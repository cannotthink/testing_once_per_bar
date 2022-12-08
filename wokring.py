from locale import currency
from operator import index
from tkinter import Frame
from turtle import position
from more_itertools import last
import pandas as pd
from binance import BinanceSocketManager
from binance.client import Client
import numpy as np
import pprint
import matplotlib as plt
import ta 
import time
from datetime import timedelta
import time, schedule
from yea import buy


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

def getdata(symbol):
    frame = pd.DataFrame(client.get_historical_klines(symbol, '1m', '600 minutes UTC'))
    frame = frame.iloc[:,:6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Price']
    frame.set_index('Time', inplace=True)
    frame.index = pd.to_datetime(frame.index, unit='ms')
    frame.Price = frame.Price.astype(float)
    frame = frame.astype(float)
    return frame

df = getdata('BTCBUSD')

def applytechnicals1(df):
    df['FASTSMA'] = df.Close.rolling(9).mean()
    df['SLOWSMA'] = df.Close.rolling(50).mean()
    df['SMA20'] = ta.trend.sma_indicator(df.Close, window=20)
    df['stddev'] = df.Close.rolling(20).std()
    df['Upper'] = df.SMA20 + 2 * df.stddev
    df['Lower'] = df.SMA20 - 2 * df.stddev
    df['lag1'] = df.Close.shift(1)
    df.dropna(inplace=True)

applytechnicals1(df)
#symbols = client.get_all_tickers()
last_entry_time = None

def trader(curr):
        schedule.every(1).minutes.do(trader, 'curr')
        qty = posframe[posframe.currency == curr].quantity.values[0]
        df = getdata(curr)
        applytechnicals1(df)
        global buyprice
        global order
        global last_entry_time
        last_bar_time = df.index[-1]
        lastrow = df.iloc[-1]
        entry1 = lastrow.FASTSMA > lastrow.SLOWSMA
        # Check if the last entry time is the same as the last bar time
        if last_entry_time == last_bar_time:
        # Skip the entry logic and move on to the next bar
            return
        if not posframe[posframe.currency == curr].position.values[0]:
            if (lastrow.Close > lastrow.Lower): 
                order = client.create_margin_order(symbol=curr,
                side = "BUY", type="MARKET", quantity=qty)
                print(order)
                buyprice = float(order['fills'][0]['price'])
                changepos(curr, buy=True)   
            else:
                print(f'NOT IN POSITION {curr} BUT CONDITION NOT FULFILLED')
        else:
            print('cur Close: ' + str(lastrow.Close))
            if lastrow.Close > buyprice:
                buyprice = lastrow.Close # tp 1.0003 is 0.03%  # sl 0.9998 is 0.02%
                print('cur buypr: ' + str(buyprice))
            TSL = buyprice * 0.9999
            if lastrow.Close < TSL:
                order = client.create_margin_order(symbol=curr,
                side = "SELL", type="MARKET", quantity=qty)
                print(order)
                changepos(curr, buy=False)
                last_entry_time = last_bar_time 
            print('cur TSL: ' + str(TSL))


for coin in posframe.currency:
    trader(coin)

while True:
    trader(coin)
    schedule.every(1).minutes.do(trader, 'curr')
    time.sleep(1)
