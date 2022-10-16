from fredapi import Fred
import pandas as pd
import configparser

def get_fred_connection():
    config = configparser.ConfigParser()
    config.read('src\market_shopper\config.ini')
    fred_config = config['FRED']
    fred_con = Fred(api_key=fred_config['API_Key'])
    return(fred_con)

def initialize_fred_dataset():
    fred_con = get_fred_connection()
    GDPC1 = fred_con.get_series_latest_release('GDPC1')