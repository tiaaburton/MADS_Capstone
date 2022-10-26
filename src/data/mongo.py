import pymongo
import configparser
from pathlib import Path


def get_mongo_connection():
    """
    Uses config parser to find config.ini file. If running with a Docker image,
    :return: MongoDB Atlas database ready to query for collections and
             non-relational records.
    """
    config = configparser.ConfigParser()
    config_path = str(Path(__file__).parents[1]) + "/config.ini"
    config.read(config_path)
    mongo_config = config["MONGO"]
    mongo_connection = (
        "mongodb+srv://"
        + mongo_config["User"]
        + ":"
        + mongo_config["Password"]
        + "@"
        + mongo_config["Address"]
    )
    mongo_client = pymongo.MongoClient(mongo_connection)
    atlas_db = mongo_client["market_shopper"]
    return atlas_db


def close_mongo_connection(myclient):
    """
    Helper function to help quickly close the client MongoDB client.
    :param myclient: Mongo DB object created by get_mongo_connection
    :return:
    """
    myclient.close()
    return
