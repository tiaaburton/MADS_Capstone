import ftplib
import pandas as pd

### Not used today - Retrieves all tickers listed in the United States.  Currently retrieved through SEC instead ###

def retrieve_nasdaq_tickers():
    ftp = ftplib.FTP("ftp.nasdaqtrader.com")
    ftp.login()

    handle = open("nasdaqlisted.txt", 'wb')
    filename = '/Symboldirectory/nasdaqlisted.txt'
    ftp.retrbinary('RETR ' + filename, handle.write)
    nasdaq_df = pd.read_csv('nasdaqlisted.txt', sep='|')

    handle = open("otherlisted.txt", 'wb')
    filename = '/Symboldirectory/otherlisted.txt'
    ftp.retrbinary('RETR ' + filename, handle.write)    
    other_df = pd.read_csv('otherlisted.txt', sep='|')

    tickers = list(nasdaq_df['Symbol'])
    tickers = tickers + list(other_df['ACT Symbol'])
    print(len(tickers))
    return tickers