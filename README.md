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

2. Portfolio Analysis
    - Digest Commsec transaction CSV - DONE
        - Does not capture dividends (cash or scrip)
    - Digest user-created dividend CSV
    - Calculate portfolio holdings and value over time - DONE
    - Calculate capital gains, recording the holding period via LIFO
        - In addition, track total cash that has been put into investing (need to distinguish between reinvested vs new equity somehow)

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