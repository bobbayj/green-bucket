# green-bucket
Catch everything you need to know to stay informed of your investments.
For ASX equities only.

Purpose: To improve tracking of historical investment performance and simplify CGT

## How-to Use
- Run gui.py and follow on-screen prompts
- Alternatively, run asx.py individually and call functions manually via a python shell

## Functionality
1. Web scrape ASX and append to SQL database
    - How to web scrape ASX for data (use requests?) - DONE
    - How to save web scraped data - DONE
    - How to Setup SQL database - DONE
    - How to store data into SQL programmatically - DONE
    - Read from SQL database and graph candlestick chart - DONE

2. Create and store a portfolio of stocks
    - Digest Commsec transaction CSV
        - Convert CSV to portfolio summary from beginning of time - DONE
        - Does not capture dividends (cash or scrip)
    - Digest user-created dividend CSV

3. Update portfolio performance automatically
    - Create GUI - DONE (basic - create proper Vue.js front-end?)
    - Overlay purchases on graph
    - Track if capital gains discount is achieved
    - Calculate portfolio value

4. Equity analysis and automatic flagging
    - Build additional TA charting subplots (see https://plot.ly/python/subplots/)
        - RSI with EWMA (DONE)
        - Add buttons to toggle graphs on/off
    - Send notification if:
        - TA: Stock crosses upper/lower bound of BollingerBand (1)
        - TA: (1) and stock crosses RSI to overbought/oversold (2)

## Requirements
- Python 3.x
- Pipenv (install using `pip install pipenv`)

## Caveats
- Web-scraping is based off what is output by the ASX. Any changes by them will require web-scraping code to be rebased