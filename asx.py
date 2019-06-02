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

def convert_iso_date(isodate):
    return dateutil.parser.parse(isodate).date()

df_price['close_date'] = df_price['close_date'].apply(convert_iso_date)
df_price['close_date'] = pd.to_datetime(df_price['close_date'],format='%Y-%m-%d')
df_price = df_price.rename(columns={"close_date":"date"})

df_chart[0] = pd.to_datetime(df_chart[0],unit='ms')
df_chart = df_chart.sort_index(axis=0, ascending=False)
df_chart = df_chart.rename(columns={0:'date',1:'open',2:'high',3:'low',4:'close',5:'Volume'})


#%%
df_merge = pd.merge(df_price,df_chart, on='date')
df_merge = df_merge.set_index('date')
df_merge.head(10)

#%%
# Initialise and create sql database and tables
import mydatabase

dbms = mydatabase.MyDatabase(mydatabase.SQLITE,dbname='mydb.sqlite')

# Create table
#dbms.create_db_tables()
dbms.print_all_data(mydatabase.HISTORICALS)
#%% Other
# Insert only new rows:
# https://www.ryanbaumann.com/blog/2016/4/30/python-pandas-tosql-only-insert-new-rows
def clean_df_db_dups(df, tablename, engine, dup_cols=[],
                         filter_continuous_col=None, filter_categorical_col=None):
    """
    Remove rows from a dataframe that already exist in a database
    Required:
        df : dataframe to remove duplicate rows from
        engine: SQLAlchemy engine object
        tablename: tablename to check duplicates in
        dup_cols: list or tuple of column names to check for duplicate row values
    Optional:
        filter_continuous_col: the name of the continuous data column for BETWEEEN min/max filter
                               can be either a datetime, int, or float data type
                               useful for restricting the database table size to check
        filter_categorical_col : the name of the categorical data column for Where = value check
                                 Creates an "IN ()" check on the unique values in this column
    Returns
        Unique list of values from dataframe compared to database table
    """
    args = 'SELECT %s FROM %s' %(', '.join(['"{0}"'.format(col) for col in dup_cols]), tablename)
    args_contin_filter, args_cat_filter = None, None
    if filter_continuous_col is not None:
        if df[filter_continuous_col].dtype == 'datetime64[ns]':
            args_contin_filter = """ "%s" BETWEEN Convert(datetime, '%s')
                                          AND Convert(datetime, '%s')""" %(filter_continuous_col,
                              df[filter_continuous_col].min(), df[filter_continuous_col].max())


    if filter_categorical_col is not None:
        args_cat_filter = ' "%s" in(%s)' %(filter_categorical_col,
                          ', '.join(["'{0}'".format(value) for value in df[filter_categorical_col].unique()]))

    if args_contin_filter and args_cat_filter:
        args += ' Where ' + args_contin_filter + ' AND' + args_cat_filter
    elif args_contin_filter:
        args += ' Where ' + args_contin_filter
    elif args_cat_filter:
        args += ' Where ' + args_cat_filter

    df.drop_duplicates(dup_cols, keep='last', inplace=True)
    df = pd.merge(df, pd.read_sql(args, engine), how='left', on=dup_cols, indicator=True)
    df = df[df['_merge'] == 'left_only']
    df.drop(['_merge'], axis=1, inplace=True)
    return df
