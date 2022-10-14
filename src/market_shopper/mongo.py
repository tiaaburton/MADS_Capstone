import pandas as pd
import pymongo
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
mongo_config = config['MONGO']
# mongo_connection = "mongodb+srv://" + mongo_config['User'] + ":" + mongo_config['Password'] + "@" + mongo_config['Address'] + ":" + mongo_config['port'] + "/?authSource=admin"
mongo_connection = "mongodb+srv://" + mongo_config['User'] + ":" + mongo_config['Password'] + "@" + mongo_config['Address'] + "/test"
myclient = pymongo.MongoClient(mongo_connection)
mydb = myclient["market_shopper"]
sub_col = mydb["sec_sub"]
num_col = mydb["sec_num"]
tag_col = mydb["sec_tag"]
pre_col = mydb["sec_pre"]
# calc_col = mydb["sec_calc"]
sec_col = mydb["sec"]
yahoo_col = mydb["yahoo"]


tickers = []
ciks = []
ticker_cik = {}
cik_ticker = {}

def build_cik_ticker():
    companies_ciks = comp_col.distinct("cik")
    # Add ciks from manually defined ciks list
    for cik in ciks:
        if cik not in companies_ciks:
            companies_ciks.append(cik)
    for cik in companies_ciks:
        if cik not in ciks:
            ciks.append(cik)
        comp_data = comp_col.find_one({"cik": cik})
        ticker = comp_data['ticker']
        if isinstance(ticker, str):
            cik_ticker[cik] = ticker
        else:
            cik_ticker[cik] = "n/a"
    # print(cik_ticker)
    print(ciks)

def build_cik_ticker_sec():
    # ticker_data = sec_ticker_col.find()
    # print(ticker_data)
    df = pd.DataFrame(list(sec_ticker_col.find()))
    print(df.head())
    df['ticker'] = df['ticker'].str.upper()
    global cik_ticker
    global ticker_cik
    cik_ticker = dict(zip(df['cik'], df['ticker']))
    ticker_cik = dict(zip(df['ticker'], df['cik']))
    # print(cik_ticker)

def build_ticker_cik():
    """ Builds tickers and ticker_cik variables from database """
    companies_tickers = comp_col.distinct("ticker")
    for ticker in companies_tickers:
        if ticker not in tickers:
            tickers.append(ticker)
        comp_data = comp_col.find_one({"ticker": ticker})
        cik = comp_data['cik']
        if ticker not in ticker_cik:
            ticker_cik[ticker] = cik
    # print(tickers)
    # print(ticker_cik)

### Queries MongoDB and adds results to Dataframe ###
### query = MongoDB query
### dataset = MongoDB dataset to query
### df = Dataframe to add the results to
### value_column = Dataframe column to add the value to
### tag_column = Dataframe column to add the tag to
### returns modified dataframe
def find_and_add_to_df(query, dataset, df, value_column, tag_column):
    query_result = dataset.find(query)
    for result in query_result:
        df.loc[result['ddate']].at[value_column] = result['value']
        df.loc[result['ddate']].at[tag_column] = result['tag']
    return df


def find_and_add_to_df_if_nan(query, dataset, df, value_column, tag_column):
    df_copy = df.copy()
    df_copy.reset_index(inplace=True)
    # df_copy.rename(columns={"index": "statement_date"}, inplace=True)
    # print(df_copy)
    query_result = dataset.find(query)
    for result in query_result:
        # print(str(result['ddate']) + "  " + result['tag'] + "  " + str(result['value']))
        if pd.isna(df.loc[result['ddate']].at[value_column]):
            # print("Found null ddate: " + str(result['ddate']))
            index_num = df_copy[df_copy['index'] == result['ddate']].index.values.astype(int)[0]
            qtr_count = 0
            history = []
            if index_num > 3:
                while qtr_count < 4 and index_num > 3:
                    index_num = index_num - 1
                    # print("index_num: " + str(index_num) + "  value: " + str(df.iloc[index_num][value_column]))
                    if not pd.isna(df.iloc[index_num][value_column]):
                        try:
                            history.append(float(df.iloc[index_num][value_column]))
                        except:
                            history.append(0)
                            print("Issue appending to history: " + str(df.iloc[index_num][value_column]))
                        # print("APPENDED - index_num: " + str(index_num) + "  value: " + str(df.iloc[index_num][value_column]))
                        qtr_count = qtr_count + 1
                three_prev_qtrs_sum = sum(history)
                # print("Three quarter sum: " + str(three_prev_qtrs_sum))
                qtr_val = result['value'] - three_prev_qtrs_sum
                df.loc[result['ddate']].at[value_column] = qtr_val
                df.loc[result['ddate']].at[tag_column] = result['tag']
    return df

### Not used - Possible use in modularizing code more ###
def insert_company_record(cik, company):
    calc_col.insert_one({"cik": cik, "company": company})

### Not used - Possible use in modularizing code more ###
def upsert_array_object(cik, company, array, object_name, value):
    calc_col.update_one({"cik": cik, "company": company}, {"$push": {array: {object_name: value}}}, upsert=True)
