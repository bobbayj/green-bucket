#%%
import csv
import os
import pandas as pd
import asxdata
import mydatabase

# Global vars
tx_filename = 'private_bob_asx.csv'
tx_folder = 'portfolio'
tx_path = os.path.join(tx_folder,tx_filename)
dbms = mydatabase.MyDatabase(mydatabase.SQLITE,dbname='mydb.sqlite')

def txFun_csvToDf():
    '''Note that this currently only works for CSVs exported from Commsec
    Commsec does not inlcude dividends in transactions. The user will
    need to manually integrate dividends into the transactions CSV
    '''
    df = pd.read_csv(tx_path, parse_dates=True ,index_col=['Date'], dayfirst=True)
    df[['Trade','Qty','Code','drop','Price']] = df['Detail'].str.split(' ',expand=True)
    df['Debit ($)'] = -df['Debit ($)']
    df['Cashflow'] = df['Debit ($)'].combine_first(df['Credit ($)'])
    df.drop(columns=['Reference','Detail','drop','Balance ($)', 'Credit ($)', 'Debit ($)'],inplace=True)
    
    df.Qty = pd.to_numeric(df.Qty)
    df.Price = pd.to_numeric(df.Price)

    return df

def get_portfolio_holdings():
    '''Creates the portfolio from transactions df
    '''
    df = txFun_csvToDf()
    dfTrades = df[df.Type == 'Contract'].sort_index(ascending=True)  # Record date of first portfolio transaction as portfolio inception
    
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

def get_portfolio_value(holdings):
    value = pd.DataFrame(index=holdings.index, columns=holdings.columns)
    for code in holdings.columns:
        query = 'SELECT * from "historical" WHERE code = "' + code + '"'
        df_raw = pd.read_sql(sql=query,con=dbms.db_engine,parse_dates='date')
        df = df_raw[df_raw.code==code].set_index('date')
        df = df.sort_index(ascending=True)

        value[code] = holdings[code].mul(df.close)
        print('Portfolio value calculated')

    return value
# ------ Main ------

dfHoldings = get_portfolio_holdings()
value = get_portfolio_value(dfHoldings)

#%% Testbed
value = value.loc[value.index > '2018-01-01']
ax = value.plot.area(figsize=[15,10], title="Bob's ASX Equity Portfolio Value")
ax.set(ylabel="Value (A$)")