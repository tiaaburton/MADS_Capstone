import pandas as pd
from stockstats import StockDataFrame

# Data visualization libraries
import plotly.graph_objects as go
import plotly.express as px

import src.data.mongo as mongo
from src.data.yahoo import retrieve_company_stock_price_from_mongo


def get_mongo_tickers():
    db = mongo.get_mongo_connection()
    yahoo_col = db["yahoo"]
    results = list(yahoo_col.find({}, {'ticker': 1, '_id': 0}))
    return [result['ticker'] for result in results]


def get_kdj_chart(ticker, start_date, end_date):
    stock_data = retrieve_company_stock_price_from_mongo(ticker)['stock_price'][0]
    stock_df = pd.DataFrame(stock_data)
    return


if __name__ == "__main__":
    print(get_kdj_chart('SPY', 1, 2))