from fredapi import Fred
import pandas as pd
import configparser
import src.data.mongo as mongo
# import data.mongo as mongo
import os


def get_fred_connection():
    config = configparser.ConfigParser()
    config.read('D:\Documents\MarketShoppers\MADS_Capstone\src\config.ini')
    # script_dir = os.path.dirname(__file__)
    # config.read(os.path.join(script_dir, 'config.ini'))
    # config.read("../config.ini")
    fred_config = config["FRED"]
    fred_con = Fred(api_key=fred_config["API_Key"])
    return fred_con


def insert_into_mongo(df):
    mydb = mongo.get_mongo_connection()
    fred_col = mydb["fred"]
    fred_col.drop()
    fred_col.insert_many(df.to_dict("records"))


def retrieve_all_metrics_from_mongo():
    mydb = mongo.get_mongo_connection()
    fred_col = mydb["fred"]
    df = pd.DataFrame(list(fred_col.find({})))
    return df


def initialize_fred():
    fred_con = get_fred_connection()
    fred_df = pd.DataFrame()

    # Inflation breakevens
    fred_df["5yILBE"] = fred_con.get_series("T5YIE")
    fred_df["5y5yILBE"] = fred_con.get_series("T5YIFR")
    fred_df["10yILBE"] = fred_con.get_series("T10YIE")

    # Treasury rates
    fred_df["TedSpread"] = fred_con.get_series("TEDRATE")
    fred_df["FedFunds"] = fred_con.get_series("DFF")
    fred_df["2yTreas"] = fred_con.get_series("DGS2")
    fred_df["5yTreas"] = fred_con.get_series("DGS5")
    fred_df["10yTreas"] = fred_con.get_series("DGS10")
    fred_df["30yTreas"] = fred_con.get_series("DGS30")
    fred_df["5yrReal"] = fred_df["5yTreas"] - fred_df["5yILBE"]
    fred_df["10yrReal"] = fred_df["10yTreas"] - fred_df["5yILBE"]
    fred_df["Repo"] = fred_con.get_series("RRPONTSYD")

    # Other
    fred_df["WTI"] = fred_con.get_series("DCOILWTICO")
    fred_df["USDGBP"] = fred_con.get_series("DEXUSUK")
    fred_df["EURUSD"] = fred_con.get_series("DEXUSEU")
    fred_df["USDYUAN"] = fred_con.get_series("DEXCHUS")
    fred_df["USDYEN"] = fred_con.get_series("DEXJPUS")
    fred_df["NFCI"] = fred_con.get_series("NFCI")
    fred_df["NatGas"] = fred_con.get_series("DHHNGSP")
    fred_df["Mortgage"] = fred_con.get_series("MORTGAGE30US")
    fred_df["M1"] = fred_con.get_series("WM1NS")
    fred_df["M2"] = fred_con.get_series("WM2NS")
    fred_df["Desposits"] = fred_con.get_series("DPSACBW027SBOG")
    fred_df["Demand Deposits"] = fred_con.get_series("WDDNS")
    fred_df["C&I Loans"] = fred_con.get_series("TOTCI")
    fred_df["UMICH Sentiment"] = fred_con.get_series("UMCSENT")
    fred_df["UMICH Inflation"] = fred_con.get_series("MICH")
    fred_df["JOLTS"] = fred_con.get_series("JTSJOL")
    fred_df["Quits"] = fred_con.get_series("JTSQUR")

    # Curve feature engineering
    fred_df["2s10s"] = fred_df["10yTreas"] - fred_df["2yTreas"]
    fred_df["2s30s"] = fred_df["30yTreas"] - fred_df["2yTreas"]
    fred_df["5s10s"] = fred_df["10yTreas"] - fred_df["5yTreas"]
    fred_df["10s30s"] = fred_df["30yTreas"] - fred_df["10yTreas"]
    fred_df["5s30s"] = fred_df["30yTreas"] - fred_df["5yTreas"]

    # Econ indicators
    fred_df["Labor_Force_Rate"] = fred_con.get_series("CIVPART")
    fred_df["Unemployment"] = fred_con.get_series("UNRATE")
    fred_df["Non-Farm Payrolls"] = fred_con.get_series("PAYEMS")
    fred_df = fred_df.fillna(method="ffill")
    fred_df.reset_index(inplace=True)

    insert_into_mongo(fred_df)


# initialize_fred_dataset()

# df = retrieve_all_metrics_from_mongo()
# print(df)
