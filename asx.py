#%% Data request
# Initialise libraries
import os
import numpy as np
import csv
import requests
import pandas as pd
from datetime import datetime
import dateutil.parser
import mydatabase
from sqlalchemy.orm import sessionmaker
import plotly
import plotly.graph_objs as go
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

# Global vars
dbms = mydatabase.MyDatabase(mydatabase.SQLITE,dbname='mydb.sqlite')
plotly.tools.set_credentials_file(username='jindustries', api_key='xljIkZ8GGLX85zLfUpKQ')
# plotly.tools.set_config_file(world_readable=True,sharing='public')
historical_t_name = 'historical'

# Functions
def asx_query(asx_code):
    # Create url required for http request
    url_price_prefix = 'https://www.asx.com.au/asx/1/share/'
    url_price_suffix = '/prices?interval=daily&count=999' #Change count for days. Note; limited by ASX
    url_price = url_price_prefix + asx_code + url_price_suffix

    price_response = requests.get(url_price)

    # print(f'Status code: {price_response.status_code} \nContent type: {price_response.headers["content-type"]}\n')

    if 'json' in price_response.headers['content-type']:
        price_dict = price_response.json()['data']
    else:
        print("Response not JSON")

    url_chart_prefix = 'https://www.asx.com.au/asx/1/chart/highcharts?asx_code='
    url_chart_suffix = '&complete=true'
    url_chart = url_chart_prefix + asx_code + url_chart_suffix

    chart_response = requests.get(url_chart)

    # print(f'Status code: {chart_response.status_code} \nContent type: {chart_response.headers["content-type"]}\n')

    if 'json' in chart_response.headers['content-type']:
        chart_dict = chart_response.json()
    else:
        print("Response not JSON")

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

    df_merge = pd.merge(df_price,df_chart, on='date')
    #df_merge = df_merge.set_index('date')
    df_final = df_merge[['date','code','open','high','low','close','volume']]
    # df_final.head(10)
    return df_final
def update_csv_database(existingTable=True):
    # Initialisation
    stocks = []

    # Stock list
    with open('stocks_list.csv', encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        stocks = list(reader)
        stocks = [item for sublist in stocks for item in sublist]

    # Create table if needed
    if not existingTable:
        dbms.create_db_table(historical_t_name)

    # For each stock, get historical data and store
    # https://www.pythonsheets.com/notes/python-sqlalchemy.html
    for counter, asx_code in enumerate(stocks):
        df_final = asx_query(asx_code)
        if existingTable:
            df_final = clean_df_db_dups(df_final,historical_t_name,dbms.db_engine,dup_cols='date',filter_categorical_col=asx_code)
        df_final.to_sql(historical_t_name,con=dbms.db_engine, if_exists='append', index=False)
        print(f'Historicals updated with {asx_code}')
    
    print('End of Stocks CSV')
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
    # https://www.ryanbaumann.com/blog/2016/4/30/python-pandas-tosql-only-insert-new-rows
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
def plot_candlestick(df,asx_code):
    # Initial candlestick chart
    INCREASING_COLOR = '#32CD32'
    DECREASING_COLOR = '#B22222'
    data = [ dict(
            type = 'candlestick',
            x = df.index,
            open = df.open,
            high = df.high,
            low = df.low,
            close = df.close,
            yaxis = 'y2',
            name = asx_code,
            increasing = dict( line = dict( color = INCREASING_COLOR ) ),
            decreasing = dict( line = dict( color = DECREASING_COLOR ) ),
        )]
    layout = dict()
    fig = dict(data = data, layout = layout)
    
    # Create layout object
    fig['layout'] = dict()
    fig['layout']['plot_bgcolor'] = 'rgb(250, 250, 250)'
    fig['layout']['xaxis'] = dict( rangeselector = dict( visible = True ) )
    fig['layout']['yaxis'] = dict( domain = [0, 0.2], showticklabels = False )
    fig['layout']['yaxis2'] = dict( domain = [0.2, 0.8] )
    fig['layout']['legend'] = dict( orientation = 'h', y=0.9, x=0.3, yanchor='bottom' )
    fig['layout']['margin'] = dict( t=40, b=40, r=40, l=40 )

    # Add range buttons
    rangeselector=dict(
        visible = True,
        x = 0, y = 0.9,
        bgcolor = 'rgba(150, 200, 250, 0.4)',
        font = dict( size = 13 ),
        buttons=list([
            dict(count=1,
                label='reset',
                step='all'),
            dict(count=1,
                label='1yr',
                step='year',
                stepmode='backward'),
            dict(count=3,
                label='3 mo',
                step='month',
                stepmode='backward'),
            dict(count=1,
                label='1 mo',
                step='month',
                stepmode='backward'),
            dict(step='all')
        ]))
        
    fig['layout']['xaxis']['rangeselector'] = rangeselector

    # Add moving average
    def movingaverage(interval, window_size=10):
        window = np.ones(int(window_size))/float(window_size)
        return np.convolve(interval, window, 'same')
    mv_y = movingaverage(df.close)
    mv_x = list(df.index)

    # Clip the ends
    mv_x = mv_x[5:-5]
    mv_y = mv_y[5:-5]

    fig['data'].append( dict( x=mv_x, y=mv_y, type='scatter', mode='lines', 
                            line = dict( width = 1 ),
                            marker = dict( color = '#917400' ),
                            yaxis = 'y2', name='Moving Average' ) )

    # Set volume bar chart colours
    colors = []

    for i in range(len(df.close)):
        if i != 0:
            if df.close[i] > df.close[i-1]:
                colors.append(INCREASING_COLOR)
            else:
                colors.append(DECREASING_COLOR)
        else:
            colors.append(DECREASING_COLOR)
    
    # Add volume bar chart
    fig['data'].append( dict( x=df.index, y=df.volume,                         
                         marker=dict( color=colors ),
                         type='bar', yaxis='y', name='Volume' ) )

    # Add bollinger bands
    def bbands(price, window_size=20, num_of_std=2):
        rolling_mean = price.rolling(window=window_size).mean()
        rolling_std  = price.rolling(window=window_size).std()
        upper_band = rolling_mean + (rolling_std*num_of_std)
        lower_band = rolling_mean - (rolling_std*num_of_std)
        return rolling_mean, upper_band, lower_band

    bb_avg, bb_upper, bb_lower = bbands(df.close)

    fig['data'].append( dict( x=df.index, y=bb_upper, type='scatter', yaxis='y2', 
                            line = dict( width = 1 ),
                            marker=dict(color='#ccc'), hoverinfo='none', 
                            legendgroup='Bollinger Bands', name='Bollinger Bands') )

    fig['data'].append( dict( x=df.index, y=bb_lower, type='scatter', yaxis='y2',
                            line = dict( width = 1 ),
                            marker=dict(color='#ccc'), hoverinfo='none',
                            legendgroup='Bollinger Bands', showlegend=False ) )
    
    # Plot
    return plot(fig, filename='candlestick-'+asx_code+'.html')
def plotting_tool(asx_code):
    query = 'SELECT * from "' + historical_t_name + '" WHERE code = "' + asx_code + '"'
    df_raw = pd.read_sql(sql=query,con=dbms.db_engine,parse_dates='date')
    df = df_raw[df_raw.code==asx_code].set_index('date')
    df = df.sort_index(ascending=True)
    plot_candlestick(df,asx_code)

# ------ Main ------

# update_csv_database(existingTable=False)
print('''
Welcome Bob's Equity Tracker Tool. Database is currently scraped from the ASX website.
What would you like to do?
    1. Update ASX ticker database
    2. Graph a ticker
    ''')



#%%
