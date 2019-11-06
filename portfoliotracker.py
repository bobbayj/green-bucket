#%%
import csv
import os
import numpy as np
import pandas as pd
import asxdata
import mydatabase
import datetime

# Global vars
tx_filename = 'private_bob_asx.csv'
tx_folder = 'portfolio'
tx_path = os.path.join(tx_folder,tx_filename)
dbms = mydatabase.MyDatabase(mydatabase.SQLITE,dbname='mydb.sqlite')

def txCsvToDf(txType='Contract'):
    '''Note that this currently only works for CSVs exported from Commsec
    Commsec does not inlcude dividends in transactions. The user will
    need to manually integrate dividends into the transactions CSV
    --------------
    txType: Contract, Payment, Receipt, or Dividend (default = 'Contract')
            Type of transaction to read and return in Dataframe
    '''
    df = pd.read_csv(tx_path, parse_dates=True ,index_col=['Date'], dayfirst=True)
    df[['Trade','Qty','Code','drop','Price']] = df['Detail'].str.split(' ',expand=True)
    df['Debit ($)'] = -df['Debit ($)']
    df['Cashflow'] = df['Debit ($)'].combine_first(df['Credit ($)'])
    df.drop(columns=['Reference','Detail','drop','Balance ($)', 'Credit ($)', 'Debit ($)'],inplace=True)
    
    df.Qty = pd.to_numeric(df.Qty)
    df.Price = pd.to_numeric(df.Price)
    df = df[df.Type == txType].sort_index(ascending=True)  # Record date of first portfolio transaction as portfolio inception

    return df

def get_portfolio_holdings():
    '''Creates the portfolio's holdings from transactions df
    '''
    dfTrades = txCsvToDf()
        
    # Give signage to qty on/off based on buy or sell trade
    dfTrades.loc[dfTrades.Trade == 'B','Trade'] = 1
    dfTrades.loc[dfTrades.Trade == 'S','Trade'] = -1
    dfTrades.Qty = dfTrades.Qty.mul(dfTrades.Trade)
    dfTrades.drop(columns=['Type','Price','Trade'],inplace=True)
    portInception = dfTrades.index[0]
    print(portInception)

    # Create df of dates since portfolio inception
    dateRange = pd.bdate_range(portInception,pd.datetime.today()).tolist()
    dfHoldings = pd.DataFrame({'Date': dateRange}).set_index('Date')

    for code in dfTrades.Code.unique():
        dfHoldings = dfHoldings.join(dfTrades[dfTrades.Code==code])
        dfHoldings.Qty.fillna(0,inplace=True)
        dfHoldings.Code.ffill(inplace=True)
        dfHoldings[f'{code}'] = dfHoldings.Qty.cumsum()
        dfHoldings.drop(columns=['Qty','Cashflow','Code'],inplace=True)

    return dfHoldings

def get_portfolio_value(holdings, plot):
    value = pd.DataFrame(index=holdings.index, columns=holdings.columns)
    for code in holdings.columns:
        query = 'SELECT * from "historical" WHERE code = "' + code + '"'
        df_raw = pd.read_sql(sql=query,con=dbms.db_engine,parse_dates='date')
        df = df_raw[df_raw.code==code].set_index('date')
        df = df.sort_index(ascending=True)

        value[code] = holdings[code].mul(df.close)
    print('Portfolio value calculated')

    if plot:
        # Graph portfolio value over time as stacked area plot
        value = value.loc[value.index > '2018-07-01']
        ax = value.plot.area(figsize=[15,10], title="Bob's ASX Equity Portfolio Value")
        ax.set(ylabel="Value (A$)")

    return value, ax

def get_CGT(code, tradedf, FY):
    '''
    code: ASX code (required)
    tradedf: DataFrame of trades
    FY: FincYear string as YYYY (default = current calendar year).
    '''
    FYStart = f'{FY-1}-07-01' 
    FYEnd = f'{FY}-06-30'

    tradedf = tradedf.loc[tradedf['Code'] == code]

    # Convert sells in selected FY to a list of dicts (records)
    dfTemp = tradedf[FYStart:FYEnd].reset_index()
    sells = dfTemp.loc[dfTemp.Trade=='S'].assign(
        **dfTemp.loc[dfTemp.Trade=='S'].select_dtypes(['datetime']).astype(str).to_dict('list')
    ).to_dict('records')

    # Convert all buys to a list of dicts (records) in reverse order (for LIFO method)
    # Buys also up to last sale date
    if sells:
        lastSellDate = sells[-1]['Date']
        dfTemp = tradedf[:lastSellDate].sort_index(ascending=False).reset_index()
    else:
        dfTemp = tradedf.sort_index(ascending=False).reset_index()
    buys = dfTemp.loc[dfTemp.Trade=='B'].assign(
        **dfTemp.loc[dfTemp.Trade=='B'].select_dtypes(['datetime']).astype(str).to_dict('list')
    ).to_dict('records')

    capgains = []
    buy_count = 0
    for sell in sells:
        while sell['Qty'] > 0:
            if sell['Qty'] == buys[buy_count]['Qty']:
                capgain = sell['Qty'] * (sell['Price'] - buys[buy_count]['Price'])
                timedelta = pd.to_datetime(sell['Date']) - pd.to_datetime(buys[buy_count]['Date'])
                if timedelta > pd.Timedelta('365 days'):
                    CGTaxable = capgain/2
                else:
                    CGTaxable = capgain
                sell['Qty'] = 0

            elif sell['Qty'] < buys[buy_count]['Qty']:
                capgain = sell['Qty'] * (sell['Price'] - buys[buy_count]['Price'])
                timedelta = pd.to_datetime(sell['Date']) - pd.to_datetime(buys[buy_count]['Date'])
                if timedelta > pd.Timedelta('365 days'):
                    CGTaxable = capgain/2
                else:
                    CGTaxable = capgain
                buys[buy_count]['Qty'] = buys[buy_count]['Qty'] - sell['Qty']
                sell['Qty'] = 0

            elif sell['Qty'] > buys[buy_count]['Qty']:
                capgain = buys[buy_count]['Qty'] * (sell['Price'] - buys[buy_count]['Price'])
                timedelta = pd.to_datetime(sell['Date']) - pd.to_datetime(buys[buy_count]['Date'])
                if timedelta > pd.Timedelta('365 days'):
                    CGTaxable = capgain/2
                else:
                    CGTaxable = capgain
                sell['Qty'] = sell['Qty'] - buys[buy_count]['Qty']
                
            
            capgains.append({
                'profit': capgain,
                'sellPrice': sell['Price'],
                'buyPrice': buys[buy_count]['Price'],
                'sellDate': sell['Date'],
                'buyDate': buys[buy_count]['Date'],
                'timedelta': timedelta,
                'CGTaxable': CGTaxable,
            })

            if not sell['Qty'] < buys[buy_count]['Qty']:
                buy_count = buy_count + 1

    return capgains

def brokerageCalc(qty,price,broker='Commsec'):
    ''' Default is Commsec brokerage rates
    brokerage = {'0-1': 10, '1-10':19.95, '10-25':29.95, '>25': 0.12%}
    --------
    qty = Quantity of securities traded
    price = Price of securities traded
    '''
    value = qty*price
    if value < 1001:
        brokerage = 10
    elif value > 1001 and value < 10001:
        brokerage = 19.95
    elif value > 10001 and value < 25001:
        brokerage = 29.95
    elif value > 25001:
        brokerage = 0.0012 * value
    
    return brokerage

class portfolioAnalysis:
    def __init__(self):
        self.tradedf = txCsvToDf()
    
    def CGTaxable(self,FY=datetime.datetime.now().year):
        '''Calculates CGTaxable for the given financial year (defaults to current calendar year)
        '''
        codes = self.tradedf.Code.unique()
        CGTevents = {}
        for code in codes:
            CGTevents.update({code: get_CGT(code,self.tradedf,FY)})

        # Calculate total CGTaxable for FY
        totalCGTaxable = 0
        for key, events in CGTevents.items():
            if key != 'totalCGTaxable':
                if len(events) > 0:
                    for event in events:
                        totalCGTaxable = totalCGTaxable + event['CGTaxable']
        return totalCGTaxable

    def holdings(self):
        '''Returns portfolio holdings as Dataframe
        '''
        return get_portfolio_holdings()
    
    def value(self, plot=False):
        '''Returns portfolio value as Dataframe
        Able to plot total portfolio value
        '''
        return get_portfolio_value(self.holdings(),plot)

#%%
