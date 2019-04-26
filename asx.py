#%% Data request
# Initialise libraries
import os
import numpy as np
import csv
import requests
import pandas as pd
from datetime import datetime
import dateutil.parser

# Import securities csv and store in list
stocks = []

with open('stocks_list.csv', encoding='utf-8-sig') as file:
    reader = csv.reader(file)
    stocks = list(reader)
    
    # Collapse the list
    stocks = [item for sublist in stocks for item in sublist]

# For each stock, get historical data and store
asx_code = 'NAN'    # Test for NAN only at the moment

# Create url required for http request
url_price_prefix = 'https://www.asx.com.au/asx/1/share/'
url_price_suffix = '/prices?interval=daily&count=999' #Change count for days. Note; limited by ASX
url_price = url_price_prefix + asx_code + url_price_suffix

price_response = requests.get(url_price)

print(f'Status code: {price_response.status_code} \nContent type: {price_response.headers["content-type"]}\n')

if 'json' in price_response.headers['content-type']:
    price_dict = price_response.json()['data']
else:
    print("Response not JSON")

url_chart_prefix = 'https://www.asx.com.au/asx/1/chart/highcharts?asx_code='
url_chart_suffix = '&complete=true'
url_chart = url_chart_prefix + asx_code + url_chart_suffix

chart_response = requests.get(url_chart)

print(f'Status code: {chart_response.status_code} \nContent type: {chart_response.headers["content-type"]}\n')

if 'json' in chart_response.headers['content-type']:
    chart_dict = chart_response.json()
else:
    print("Response not JSON")


#%% Dataframe creation

df_price = pd.DataFrame.from_dict(price_dict)
df_chart = pd.DataFrame.from_dict(chart_dict)

df_chart[0] = pd.to_datetime(df_chart[0],unit='ms')


def convert_iso_date(isodate):
    return dateutil.parser.parse(isodate).date()

df_price['close_date'] = df_price['close_date'].apply(convert_iso_date)
df_chart = df_chart.sort_index(axis=0, ascending=False)
df_chart = df_chart.rename(columns={0:'date',1:'open',2:'high',3:'low',4:'close',5:'Volume'})

df_price = df_price.set_index('close_date')
df_chart = df_chart.set_index('date')

#%%
df_price.head(10)

#%%
df_chart.head(10)

#%%
