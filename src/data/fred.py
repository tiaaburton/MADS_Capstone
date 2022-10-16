from fredapi import Fred
import pandas as pd
import configparser
import mongo

METRICS = {"GDP": "Gross Domestic Product", "FEDFUNDS": "Federal Funds Effective Rate", "CPIAUCSL": "Consumer Price Index", "UNRATE": "Unemployment Rate", "DGS10": "Market Yield on U.S. Treasury Securities at 10-Year Constant Maturity, Quoted on an Investment Basis"}

def get_fred_connection():
    config = configparser.ConfigParser()
    config.read('src\data\config.ini')
    fred_config = config['FRED']
    fred_con = Fred(api_key=fred_config['API_Key'])
    return(fred_con)

def retrieve_metric_from_fred(metric, description):
    # Gross Domestic Product
    fred_con = get_fred_connection()
    metric_series = fred_con.get_series_latest_release(metric)
    metric_series.name = metric
    metric_df = metric_series.to_frame()
    metric_df.reset_index(inplace=True)
    insert_into_mongo(metric_df, metric, description)

def insert_into_mongo(df, name, description):
    remove_from_mongo(name)
    mydb = mongo.get_mongo_connection()
    fred_col = mydb["fred"]
    data_dict = df.to_dict("records")
    fred_col.insert_one({"metric": name, "description": description, 'values': data_dict})

def retrieve_metric_from_mongo(name):
    mydb = mongo.get_mongo_connection()
    fred_col = mydb["fred"]
    metric_data = fred_col.find_one({"metric": name})
    df = pd.DataFrame(metric_data['values'])
    return df

def retrieve_all_metrics_from_mongo():
    df = pd.DataFrame()
    first = True
    for metric in METRICS.keys():
        metric_df = retrieve_metric_from_mongo(metric)
        if first:
            df = metric_df
            first = False
        else:
            df = df.merge(metric_df, left_on='index', right_on='index', how='outer')
    return df

def remove_from_mongo(name):
    mydb = mongo.get_mongo_connection()
    fred_col = mydb["fred"]
    fred_col.delete_one({"metric": name})

def initialize_fred_dataset():
    for metric in METRICS.keys():
        retrieve_metric_from_fred(metric, METRICS[metric]) 

df = retrieve_all_metrics_from_mongo()
print(df)

# initialize_fred_dataset()