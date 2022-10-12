import pandas as pd
import urllib.request
import json

tickers = []
cik_ticker = {}
ticker_cik = {}

def retrieve_ticker_cik_mapping():
    global tickers
    global ticker_cik
    global cik_ticker
    with urllib.request.urlopen("https://www.sec.gov/files/company_tickers.json") as url:
        data = json.load(url)
    sec_df = pd.DataFrame.from_dict(data).T
    tickers = list(sec_df['ticker'])
    ticker_cik = dict(zip(list(sec_df['ticker']), list(sec_df['cik_str'])))
    cik_ticker = dict(zip(list(sec_df['ticker']), list(sec_df['cik_str'])))

retrieve_ticker_cik_mapping()