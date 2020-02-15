# System imports
import csv
import pandas as pd
import numpy as np
from pathlib import Path


# Structure as Class object
class Commsec:
    '''
    Reads and prepares Commsec transactions.csv files

    Note that transactions only show on the T+2 date
    '''
    def __init__(self):
        dirname = Path(__file__).parents[1] / 'data'
        csvfiles = sorted(list(dirname.glob('*commsec*')))
        latest_csv = csvfiles[-1]

        df = pd.read_csv(latest_csv)
        df = self.digest_txs(df)

        self.df = df

    def digest_txs(self, df):
        """Digest raw transactions.csv dataframe
        
        EffectivePrice includes brokerage

        Arguments:
            df {Dataframe} -- Raw transactions.csv loaded into a dataframe
        """
        details = df['Details'].tolist()
        trades = []

        # Split details data
        for detail in details:
            if detail[0] in ['B','S']:  # Trades start with B or S
                detail = detail.split()
                for i,txt in enumerate(detail):
                    if txt == '@':
                        detail.pop(i)
            else:
                detail = np.nan  # Mark non-trade details as NaN
            trades.append(detail)

        # Keep only trade transactions
        df['Trades'] = trades
        df = df[df.Trades.notnull()]

        # Flatten list of trade data to columns
        temp_df = df.Trades.apply(pd.Series)
        temp_df.columns = ['TradeType','Volume','Ticker','TradePrice']
        df = df.join(temp_df)

        # Convert string dates to datetime.date
        df.Date = pd.to_datetime(df.Date, dayfirst=True).dt.date

        # Change str to float
        df['Volume'] = pd.to_numeric(df['Volume'], downcast='float')
        df['TradePrice'] = pd.to_numeric(df['TradePrice'], downcast='float')

        # Calculate effective price inclusive of brokerage
        df['Debit($)'].fillna(df['Credit($)'], inplace=True)
        df['EffectivePrice'] = df['Debit($)'] / df['Volume']

        # Calculate brokerage
        df['Brokerage'] = df['Volume']*(df['EffectivePrice'] - df['TradePrice'])
        df['Brokerage'] = round(np.abs(df['Brokerage']),0)

        # Add market for all trades
        df['Market'] = 'ASX'

        # Clean df for export
        cols = ['Date','Ticker','Market','TradeType','Volume','TradePrice','EffectivePrice','Brokerage']
        df = df[cols]
        df = df.set_index(['Date','Ticker'])

        return df
    
    @property
    def all(self):
        '''
        Returns:
            Dataframe -- all transactions
        '''        
        return self.df
    
    @property
    def buys(self):
        '''
        Returns:
            Dataframe -- only buy transactions
        '''        
        df = self.df[self.df.TradeType == 'B']
        return df

    @property
    def sells(self):
        '''
        Returns:
            Dataframe -- only sell transactions
        '''        
        df = self.df[self.df.TradeType == 'S']
        return df

    @property
    def cashflow(self):
        '''Returns a series for the change in cash balance
        
        Returns:
            Series -- cash per trade, indexed by portfolio dates
        '''
        df = pd.DataFrame(index=self.df.index)
        df['Type'] = np.where(self.df.TradeType == 'B', -1, 1)
        df['Value'] = self.df.Volume * self.df.EffectivePrice * df.Type
        df = df.drop(columns = 'Type')
        return df

class DivScrip:
    '''
    Reads and prepares manually created div_scrip.csv files

    Note that transactions show the payment date
    '''
    def __init__(self):
        dirname = Path(__file__).parents[1] / 'data'
        csvfiles = sorted(list(dirname.glob('*manual*')))
        latest_csv = csvfiles[-1]

        df = pd.read_csv(latest_csv)
        df = self.clean_csv(df)

        self.df = df
    
    def clean_csv(self,df):
        # Convert string dates to datetime.date
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True).dt.date
        
        df = df.set_index(['Date','Ticker'])

        return df