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
brokerage = {'<1': 10, '1-5':20, '>5':50}

def txCsvToDf(txType='Contract'):
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
    df = df[df.Type == txType].sort_index(ascending=True)  # Record date of first portfolio transaction as portfolio inception

    return df

def get_portfolio_holdings():
    '''Creates the portfolio from transactions df
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

def get_portfolio_value(holdings, plot=False):
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

def get_CGT(fincyr=None):
    '''
    fincyr: FY string as YYYY (default = None). Creates Australian FY range. Otherwises, computes all capital gains
    '''
    # Vars
    df = txCsvToDf()
    # dfCGT = pd.DataFrame(index = df.index, columns = df.columns)
    if fincyr:
        fincyrStart = f'{fincyr-1}-07-01'
        fincyrEnd = f'{fincyr}-06-30'

    # for code in df.Code.unique():
    #     dfTemp = df.loc[df['Code'] == code].sort_index(ascending=False)
    #     buys = dfTemp.loc[dfTemp.Trade =='B','Qty'].todict()
    #     sells = dfTemp.loc[dfTemp.Trade =='B','Qty'].todict()
    #     dfCGT = dfTemp
    #     break


    return df

# ------ Main ------

# dfHoldings = get_portfolio_holdings()
# value, ax = get_portfolio_value(dfHoldings)
FY = 2018
FYStart = f'{FY-1}-07-01' 
FYEnd = f'{FY}-06-30'

df = get_CGT()
code = 'NAN'

df = df.loc[df['Code'] == code]

# Convert all buys to a list of dicts (records) in reverse order (LIFO method)
dfTemp = df.sort_index(ascending=False).reset_index()
buys = dfTemp.loc[dfTemp.Trade=='B'].assign(
    **dfTemp.loc[dfTemp.Trade=='B'].select_dtypes(['datetime']).astype(str).to_dict('list')
).to_dict('records')

# Convert sells in selected FY to a list of dicts (records)
dfTemp = df[FYStart:FYEnd].reset_index()
sells = dfTemp.loc[dfTemp.Trade=='S'].assign(
    **dfTemp.loc[dfTemp.Trade=='S'].select_dtypes(['datetime']).astype(str).to_dict('list')
).to_dict('records')

#%%
capgains = []
buy_count = 0
for sell in sells:
    sell_qty = sell['Qty'] #Don't overwrite the data
    while sell_qty > 0:
        buy_qty = buys[buy_count]['Qty'] #Don't overwrite the data
        if sell_qty == buy_qty:
            capgain = sell_qty * (sell['Price'] - buys[buy_count]['Price'])
            timedelta = pd.to_datetime(sell['Date']) - pd.to_datetime(buys[buy_count]['Date'])
            if timedelta > pd.Timedelta('365 days'):
                CGTaxable = capgain/2
            else:
                CGTaxable = capgain
            capgains.append({
                'gain/loss': capgain,
                'sale_price': sell['Price'],
                'buy_price': buys[buy_count]['Price'],
                'sale_date': sell['Date'],
                'buy_date': buys[buy_count]['Date'],
                'timedelta': timedelta,
                'CGTaxable': CGTaxable
            })
            sell_qty = 0
        elif sell_qty < buy_qty:
            buy_qty = buy_qty - sell_qty
            capgain = sell_qty * (sell['Price'] - buys[buy_count]['Price'])
            timedelta = pd.to_datetime(sell['Date']) - pd.to_datetime(buys[buy_count]['Date'])
            if timedelta > pd.Timedelta('365 days'):
                CGTaxable = capgain/2
            else:
                CGTaxable = capgain
            capgains.append({
                'gain/loss': capgain,
                'sale_price': sell['Price'],
                'buy_price': buys[buy_count]['Price'],
                'sale_date': sell['Date'],
                'buy_date': buys[buy_count]['Date'],
                'timedelta': timedelta,
                'CGTaxable': CGTaxable
            })
            sell_qty = 0
        elif sell_qty > buy_qty:
            sell_qty = sell_qty - buy_qty
            capgain = buy_qty * (sell['Price'] - buys[buy_count]['Price'])
            timedelta = pd.to_datetime(sell['Date']) - pd.to_datetime(buys[buy_count]['Date'])
            if timedelta > pd.Timedelta('365 days'):
                CGTaxable = capgain/2
            else:
                CGTaxable = capgain
            capgains.append({
                'gain/loss': capgain,
                'sale_price': sell['Price'],
                'buy_price': buys[buy_count]['Price'],
                'sale_date': sell['Date'],
                'buy_date': buys[buy_count]['Date'],
                'timedelta': timedelta,
                'CGTaxable': CGTaxable
            })
        buy_count = buy_count + 1

#%%
buys

#%%
