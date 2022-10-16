import pandas as pd
import pymongo
import configparser

def get_mongo_connection():
    config = configparser.ConfigParser()
    config.read('src\market_shopper\config.ini')
    mongo_config = config['MONGO']
    # mongo_connection = "mongodb+srv://" + mongo_config['User'] + ":" + mongo_config['Password'] + "@" + mongo_config['Address'] + ":" + mongo_config['port'] + "/?authSource=admin"
    mongo_connection = "mongodb+srv://" + mongo_config['User'] + ":" + mongo_config['Password'] + "@" + mongo_config['Address'] + "/test"
    myclient = pymongo.MongoClient(mongo_connection)
    mydb = myclient["market_shopper"]
    return mydb

def close_mongo_connection(myclient):
    myclient.close()

my_con = get_mongo_connection()


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
