import pandas as pd
import pymongo
import configparser
import os

def get_mongo_connection():
    config = configparser.ConfigParser()
    # config.read('D:\Documents\MarketShoppers\MADS_Capstone\src\data\config.ini')
    # script_dir = os.path.dirname(__file__)
    # config.read(os.path.join(script_dir, 'config.ini'))
    config.read('config.ini')
    mongo_config = config['MONGO']
    # mongo_connection = "mongodb+srv://" + mongo_config['User'] + ":" + mongo_config['Password'] + "@" + mongo_config['Address'] + ":" + mongo_config['port'] + "/?authSource=admin"
    mongo_connection = "mongodb+srv://" + mongo_config['User'] + ":" + mongo_config['Password'] + "@" + mongo_config['Address'] + "/test"
    myclient = pymongo.MongoClient(mongo_connection)
    mydb = myclient["market_shopper"]
    return mydb

def close_mongo_connection(myclient):
    myclient.close()