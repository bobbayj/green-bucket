# green-bucket
Catch everything you need to know to stay informed of your investments.
For ASX equities only.

Purpose: To improve tracking of historical investment performance and simplify CGT

1. Web scrape ASX and append to SQL database
    - How to web scrape ASX for data (use requests?)
    - How to save web scraped data
    - How to Setup SQL database
    - How to store data into SQL programmatically


2. Create and store a portfolio of stocks
    - Auto-retrieve from Commsec

3. Update portfolio performance automatically

## Requirements
- Python 3.x
- Pipenv (install using `pip install pipenv`)

## Caveats
- Web-scraping is based off what is output by the ASX. Any changes by them will require web-scraping code to be rebased