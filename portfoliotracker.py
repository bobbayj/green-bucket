#%%
import csv
import os
import pandas as pd

# Global vars
tx_filename = 'private_bob_asx.csv'
tx_folder = 'portfolio'
tx_path = os.path.join(tx_folder,tx_filename)

def txFun_csvToDf():
    '''Note that this currently only works for CSVs exported from Commsec
    '''
    df = pd.read_csv(tx_path, parse_dates=True ,index_col=['Date'], dayfirst=True)
    df[['Trade','Qty','Code','drop','Price']] = df['Detail'].str.split(' ',expand=True)
    df['Debit ($)'] = -df['Debit ($)']
    df['Cashflow'] = df['Debit ($)'].combine_first(df['Credit ($)'])
    df.drop(columns=['Reference','Detail','drop','Balance ($)', 'Credit ($)', 'Debit ($)'],inplace=True)
    return df

def portFun_create():
    '''Creates the portfolio from transactions df
    '''
    df = txFun_csvToDf()
    dfContracts = df[df.Type == 'Contract'].sort_index(ascending=True)
    # Record date of first portfolio transaction as portfolio inception
    portInception = dfContracts.index[0]
    print(portInception)

    # Create df of dates since portfolio inception
    dateRange = pd.bdate_range(portInception,pd.datetime.today()).tolist()
    dfPort = pd.DataFrame({'Date': dateRange}).set_index('Date')

    # # Merge stocks to dates in portfolio
    # for code in dfContracts.Code.unique():
    #     rightdf = dfContracts[dfContracts.Code==code]
    #     break

    # dfPort = dfPort.join(rightdf).ffill()

    # return dfPort, dfContracts

    '''
    1. For each date, check for a transaction
        - BUY: Is stock in portfolio? If not, add stock to portfolio
            - Increase stock holding by X qty
        - SELL: Decrease stock holding by X qty
            - Is qty now 0? remove stock from portfolio
    2. Calculate closing portfolio value for each date
        - Look up close price in SQL table on Code
        - If close price exists for day, multiply stock by close price
        - Else, use value of previous day
    '''


# ------ Main ------

dfPort, dfContracts = portFun_create()


#%% Testbed
