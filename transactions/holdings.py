# Standard imports
import pandas as pd
import numpy as np

# Third party imports
import yfinance as yf
import datetime

# Local imports
from transactions import etl

class Holdings:
    def __init__(self):
        # Instantiate data file classes
        self.trades = etl.Commsec().df
        self.div_scrip = etl.DivScrip().df

        self.history = self.build_transaction_history()

    def build_transaction_history(self):
        # Add scrip receipts to holdings
        xscrip_df = self.div_scrip[self.div_scrip.Scrip.isna() == False].drop(columns=['Cash_unfranked', 'Cash_franked'])
        holdings = pd.concat([self.trades, xscrip_df], sort=False)

        # Store list of unique tickers in transaction history
        tickers = sorted(set(holdings.index._levels[1].to_list()))

        # == START: IMPROVEMENT REQUEST ==
        # In future, check database for last transaction
        # Update database with only the new transactions
        # == END: IMPROVEMENT REQUEST ==

        # Loop through tickers to update holdings with stock splits
        for i, ticker in enumerate(tickers):
            # Print progress in terminal
            print(f'\r{ticker} | Progress: {i+1}/{len(tickers)}', end='', flush=True)
            
            # Refresh lookup masks
            mask_ticker = (holdings.index.get_level_values(1)==ticker)
            mask_scrip = (holdings['Brokerage'].isna()==True)

            # Store first date of holdings
            holding_start = holdings.loc[mask_ticker,'Market'].first_valid_index()[0]
            
            ## UPDATE SCRIP ##
            if len(holdings.loc[holdings['Brokerage'].isna()==True]) > 0:
                # Fill df with scrip data
                holdings.loc[mask_scrip,'TradeType'] = 'B'
                holdings.loc[mask_scrip,'Market'] = 'ASX'
                holdings.loc[mask_scrip,'Volume'] = holdings.loc[mask_scrip].pop('Scrip')
                holdings.loc[mask_scrip,'TradePrice'] = holdings.loc[mask_scrip].pop('Scrip_price')
                holdings.loc[mask_scrip,'EffectivePrice'] = holdings.loc[mask_scrip].pop('Scrip_price')
                holdings.loc[mask_scrip,'Brokerage'] = 0

                holdings = holdings.drop(columns=['Scrip','Scrip_price'])
            ## UPDATE STOCKSPLITS ##
            try:
                splits = yf.Ticker(f'{ticker}.AX').splits
            except:
                continue
            else:
                if len(splits) == 0:
                    continue
                
                if len(splits.loc[holding_start:]) > 0:
                    split_multiple = splits.loc[holding_start:].cumprod().values[-1]
                    holdings.loc[mask_ticker,'Volume'] = holdings.loc[mask_ticker].pop('Volume') * split_multiple
                    holdings.loc[mask_ticker,'TradePrice'] = holdings.loc[mask_ticker].pop('TradePrice') / split_multiple
                    holdings.loc[mask_ticker,'EffectivePrice'] = holdings.loc[mask_ticker].pop('EffectivePrice') / split_multiple

            # Re-order dataframe by date, descending
            holdings = holdings.sort_index(ascending=False)

            # Save as csv
            today = datetime.datetime.today().date()
            holdings_filename = f'data/{today}_transactions.csv'
            holdings.to_csv(holdings_filename)
            print(f'\n\tAll data saved in {holdings_filename}')

            # == START: IMPROVEMENT REQUEST ==
            # Save to a sql database using df.to_sql(name: str, con=engine, if_exists = 'append')
            # == END: IMPROVEMENT REQUEST ==

        return holdings