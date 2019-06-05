# green-bucket
Catch everything you need to know to stay informed of your investments.
For ASX equities only.

Purpose: To improve tracking of historical investment performance and simplify CGT

1. Web scrape ASX and append to SQL database
    - How to web scrape ASX for data (use requests?) - DONE
    - How to save web scraped data - DONE
    - How to Setup SQL database - DONE
    - How to store data into SQL programmatically - DONE
    - Read from SQL database and graph candlestick chart - DONE

2. Create and store a portfolio of stocks
    - Ingest transaction data to create view of portfolio at any point in time
    - Auto-retrieve from Commsec

3. Update portfolio performance automatically
    - Create GUI
    - Overlay purchases on graph
    - Track if capital gains discount is achieved
    - Calculate portfolio value

## Requirements
- Python 3.x
- Pipenv (install using `pip install pipenv`)

## Caveats
- Web-scraping is based off what is output by the ASX. Any changes by them will require web-scraping code to be rebased