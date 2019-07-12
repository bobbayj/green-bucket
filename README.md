# green-bucket
'Catch everything you need to know to stay informed of your investments in your green bucket'
For ASX equities only.

Purpose: To improve tracking of historical investment performance and simplify CGT

This is a little Python project I did to play around with:
- web-scraping
- database management
- Classes in Python (these are amazing)
- Tkinter (Python GUI tools)
- Python package management using Pipenv
- The beauty of GIT
Not perfect, but let me know what you think!

## Caveats
- Web-scraping is based off what is output by the ASX website. Any changes by them will likely break the database updating
- The sample portfolio only contains one sample transaction, mainly because I don't want to disclose my own (bad) purchases (haha...)!
- I used VSC and its in-built Jupyter Notebook capability to develop this project! I hoped that Pipenv would let me easily develop this project on any computer. Turns out, you still need to install some jupyter notebook items and pipenv is not as plug and play as you think...let me know if you figure out how.

## Requirements
- Python 3.x
- Pipenv
    1. Install Pipenv using `pip install pipenv`
    2. Install python package dependencies using `pipenv install`

## How-to Use
- Run gui.py and follow on-screen prompts
- Alternatively, run `asxdata.py` individually and call the functions manually via a python shell.

Main Functions in `asxdata.py` include:
- `update_csv_database(existingTable=True)`: Creates/updates a sqlite3 database with historical data, based off the ASX securities in the `stock_list.csv`. Call the function with `existingTable=False` if you are calling this function for the first time.
- `plotting_tool(asx_code)`: Plots the historical data using plot.ly. `asx_code` must be a 3-letter ASX code.

`portfoliotracker.py` contains a Class with the following Methods:
- `CGTaxable(self,FY=current year)`: Calculates CGTaxable for the given financial year (defaults to current calendar year)
- `holdings(self)`: Returns portfolio holdings as Dataframe
- `value(self, plot=False)`: Returns portfolio value as Dataframe. Able to plot (using matplotlib) total portfolio value over time

## Functionality
1. Web scrape ASX and append to SQL database
    - How to web scrape ASX for data (use requests?) - DONE
    - How to save web scraped data - DONE
    - How to Setup SQL database - DONE
    - How to store data into SQL programmatically - DONE
    - Read from SQL database and graph candlestick chart - DONE

2. Portfolio Analysis
    - Digest Commsec transaction CSV - DONE
        - Need to manually enter dividends (cash or scrip) as commsec does not capture this
        - Does not include brokerage costs
    - Digest user-created dividend CSV - DONE
    - Calculate portfolio holdings and value over time - DONE
    - Calculate capital gains, recording the holding period via LIFO - DONE
        - In addition, track total cash that has been put into investing (need to distinguish between reinvested vs new equity somehow)
    - Calculate brokerage costs
        - Commsec

3. User interface and viewing
    - Create GUI - DONE
        - basic tkinter - create proper Vue.js front-end?
    - Identify holdings and graph value over time - DONE
    - Overlay purchases on graph

4. News scraping (only good for web though)
    - ASX Announcements
    - Twitter view
    - Online smart search?

5. Equity technical analysis and automatic flagging
    - Build additional TA charting subplots (see https://plot.ly/python/subplots/)
        - RSI with EWMA (DONE)
        - Add buttons to toggle graphs on/off
    - Send notification if:
        - TA: Stock crosses upper/lower bound of BollingerBand (1)
        - TA: (1) and stock crosses RSI to overbought/oversold (2)

