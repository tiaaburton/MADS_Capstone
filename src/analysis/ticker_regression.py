import src.data.sec as sec
import src.data.yahoo as yahoo
import src.data.fred as fred
import src.data.mongo as mongo

# import sec
# import yahoo
# import fred
# import mongo

import pandas as pd
import numpy as np

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.neural_network import MLPRegressor

# from statsmodels.tsa.arima.model import ARIMA
from sklearn.cross_decomposition import CCA
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import r2_score
from datetime import timedelta
from datetime import datetime
import numpy as np

cca = CCA(n_components=1)


def create_combined_dataframe(ticker, start_date, end_date):
    # Create empty dataframe with dates to combine the results
    date_index = pd.to_datetime(pd.date_range(start_date, end_date), format="%Y-%m-%d")
    combined_df = pd.DataFrame(index=date_index)
    combined_df.index.names = ["Date"]

    # Retrieve from Yahoo
    # print("Retrieving Yahoo data...")
    yahoo_df = yahoo.retrieve_company_stock_price_from_mongo(ticker)
    yahoo_df["Date"] = pd.to_datetime(yahoo_df["Date"])
    yahoo_df.drop(labels=["_id"], axis=1, inplace=True)
    yahoo_df.set_index("Date", inplace=True)
    yahoo_df.drop(
        [
            "targetLowPrice",
            "targetMeanPrice",
            "targetMedianPrice",
            "targetHighPrice",
            "numberOfAnalystOpinions",
            "bookValue",
            "targetMedianGrowth",
        ],
        axis=1,
        inplace=True,
    )
    # print(yahoo_df)

    fill_values = {
        "close_pct_1d": 0,
        "close_pct_30d": 0,
        "close_pct_60d": 0,
        "close_pct_120d": 0,
        "close_pct_1yr": 0,
    }
    combined_df = combined_df.join(yahoo_df, on="Date")
    combined_df.ffill(inplace=True)
    combined_df.fillna(fill_values, inplace=True)
    # print(combined_df)

    # Retrieve from FRED
    # print("Retrieving FRED data...")
    fred_df = fred.retrieve_all_metrics_from_mongo()
    fred_df.drop(labels=["_id"], axis=1, inplace=True)
    fred_df.rename(columns={"index": "Date"}, inplace=True)
    fred_df["Date"] = pd.to_datetime(fred_df["Date"])
    fred_df.set_index("Date", inplace=True)
    fred_df.ffill(inplace=True)
    fred_df.bfill(inplace=True)
    combined_df = combined_df.join(fred_df, on="Date")

    # Retrieve from SEC
    # print("Retrieving SEC data...")
    sec_df = sec.retrieve_company_facts_from_mongo_using_ticker(ticker)
    if sec_df is not None:
        sec_index = sec_df["filed"].unique()
        sec_df.set_index("filed", inplace=True)

        columns = sec_df["measure"].unique()
        new_df = pd.DataFrame(index=sec_index, columns=columns)
        for index, row in sec_df.iterrows():
            new_df.at[index, row["measure"]] = row["val"]
        new_df.ffill(limit=3, inplace=True)
        new_df.index = pd.to_datetime(new_df.index)
        new_df.index.names = ["Date"]
        # combined_df = combined_df.join(new_df, on='Date')
        combined_df = combined_df.merge(
            new_df, how="left", left_index=True, right_index=True
        )
    prefill_df = combined_df.copy()
    # prefill_df.to_excel('prefill_v2.xlsx')
    combined_df.ffill(limit=100, inplace=True)
    combined_df.bfill(limit=100, inplace=True)
    # combined_df.to_excel('postfill_v2.xlsx')
    combined_df.dropna(axis=1, how="any", inplace=True)
    # combined_df.to_excel('postdrop_v2.xlsx')

    return combined_df


def prep_df_for_regression(df):
    ticker = df["ticker"].unique()[0]
    sector = df["sector"].unique()[0]
    industry = df["industry"].unique()[0]

    # df.drop(['ticker', 'sector', 'industry', 'Open', 'High', 'Low', 'Volume', 'Dividends', 'Stock Splits', 'wma_7', 'wma_30', 'wma_60', 'wma_120', 'close_pct_1d', 'close_pct_30d', 'close_pct_60d', 'close_pct_120d', 'close_pct_1yr', 'targetLowPrice', 'targetMeanPrice', 'targetMedianPrice', 'targetHighPrice'], axis=1, inplace=True)
    df.drop(["ticker", "sector", "industry"], axis=1, inplace=True)

    df["returns"] = np.log(df["Close"] / df["Close"].shift(1))
    df.dropna(inplace=True)
    df["direction"] = np.sign(df["returns"]).astype(int)
    df["lag_1"] = df["returns"].shift(1)
    df["lag_2"] = df["returns"].shift(2)
    df["Close_1yr"] = df["Close"].shift(-365)
    df_current = df.tail(365)
    df.dropna(inplace=True)

    return df, df_current, ticker, sector, industry


def train_test_split(df):
    y = df["Close_1yr"].values
    X = df.drop(["Close_1yr"], axis=1)
    X.reset_index(inplace=True)
    dates = X["Date"].values
    X.drop(["Date"], axis=1, inplace=True)
    X = X.values
    tscv = TimeSeriesSplit(n_splits=2)
    X_train, X_test, y_train, y_test, dates_train, dates_test = (
        None,
        None,
        None,
        None,
        None,
        None,
    )
    for train_index, test_index in tscv.split(X):
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        dates_train, dates_test = dates[train_index], dates[test_index]

    # Perform dimensionality reduction on the features, taking into account the relationship with y
    X_train, y_train = perform_cross_decomposition(X_train, y_train)
    X_test, y_test = perform_cross_decomposition(X_test, y_test)
    # X_test = transform_cross_decomposition(X_test)

    # Center the data on the mean
    X_train = StandardScaler().fit_transform(X_train)
    X_test = StandardScaler().fit_transform(X_test)

    y_train = y_train.ravel()

    return X_train, y_train, dates_train, X_test, y_test, dates_test


def create_combined_results_df(
    df,
    dates_test,
    y_hat,
    dates_pred,
    y_pred,
    ticker,
    sector,
    industry,
    train_score,
    test_score,
):
    # Create test results dataframe
    test_df = pd.DataFrame(index=dates_test, columns=["prediction"], data=y_hat)
    test_df.index = test_df.index + timedelta(days=365)

    # Create prediction results dataframe
    pred_df = pd.DataFrame(index=dates_pred, columns=["prediction"], data=y_pred)
    pred_df.index = pred_df.index + timedelta(days=365)

    # Combine test and future values
    combined_df = pd.concat([test_df, pred_df])
    combined_df.index.names = ["Date"]

    # print(combined_df)
    results_df = combined_df.merge(df, how="left", left_index=True, right_index=True)
    results_df["predicted_1yr_growth"] = (
        results_df["prediction"] - results_df["Close"].shift(365)
    ) / results_df["Close"].shift(365)
    results_df = results_df[["prediction", "Close", "predicted_1yr_growth"]]
    results_df["ticker"] = ticker
    results_df["sector"] = sector
    results_df["industry"] = industry
    results_df["train_score"] = train_score
    results_df["test_score"] = test_score
    return results_df


def create_linear_ols_model(df):

    df, df_current = prep_df_for_regression(df)
    y = df["Close_1yr"].values
    X = df.drop(["Close_1yr"], axis=1)
    X.reset_index(inplace=True)
    dates = X["Date"].values
    X.drop(["Date"], axis=1, inplace=True)
    X = X.values
    tscv = TimeSeriesSplit(n_splits=2)
    X_train = None
    X_test = None
    y_train = None
    y_test = None
    dates_train = None
    dates_test = None
    for train_index, test_index in tscv.split(X):
        X_train, X_test = X[train_index], X[test_index]
        y_train, y_test = y[train_index], y[test_index]
        dates_train, dates_test = dates[train_index], dates[test_index]

    reg = LinearRegression().fit(X_train, y_train)
    print(reg.score(X_train, y_train))
    y_pred = reg.predict(X_test)
    pred_df = pd.DataFrame(index=dates_test, columns=["prediction"], data=y_pred)
    print(pred_df)
    print(r2_score(y_test, y_pred))


def create_random_forest_model(df):
    # Prepare the dataframe for regression
    df_train_test, df_pred, ticker, sector, industry = prep_df_for_regression(df.copy())

    # Train/Test split
    X_train, y_train, dates_train, X_test, y_test, dates_test = train_test_split(
        df_train_test
    )

    # Fit the model
    regr = RandomForestRegressor(
        n_estimators=200, max_depth=5, random_state=42, warm_start=False
    )
    regr.fit(X_train, y_train)
    train_score = regr.score(X_train, y_train)

    # Test the fit
    y_hat = regr.predict(X_test)
    test_score = r2_score(y_test, y_hat)

    # Predict future values
    X_pred = df_pred.drop(["Close_1yr"], axis=1).values
    dates_pred = df_pred.index
    X_pred = transform_cross_decomposition(X_pred)
    y_pred = regr.predict(X_pred)

    # Convert back to normal values
    X_pred, y_pred = inverse_transform_cross_decompisition(X_pred, y_pred)

    # Create dataframe with results
    results_df = create_combined_results_df(
        df,
        dates_test,
        y_hat,
        dates_pred,
        y_pred,
        ticker,
        sector,
        industry,
        train_score,
        test_score,
    )

    return results_df, train_score, test_score


def create_gradient_boosted_tree_model(df):
    # Prepare the dataframe for regression
    df_train_test, df_pred, ticker, sector, industry = prep_df_for_regression(df.copy())

    # Train/Test split
    X_train, y_train, dates_train, X_test, y_test, dates_test = train_test_split(
        df_train_test
    )

    # Fit the model
    regr = GradientBoostingRegressor(
        n_estimators=750,
        max_depth=5,
        random_state=42,
        min_samples_split=5,
        learning_rate=0.02,
        loss="ls",
    )
    regr.fit(X_train, y_train)
    train_score = regr.score(X_train, y_train)

    # Test the fit
    y_hat = regr.predict(X_test)
    test_score = r2_score(y_test, y_hat)

    # Predict future values
    X_pred = df_pred.drop(["Close_1yr"], axis=1).values
    dates_pred = df_pred.index
    X_pred = transform_cross_decomposition(X_pred)
    y_pred = regr.predict(X_pred)

    # Convert back to normal values
    X_pred, y_pred = inverse_transform_cross_decompisition(X_pred, y_pred)

    # Create dataframe with results
    results_df = create_combined_results_df(
        df,
        dates_test,
        y_hat,
        dates_pred,
        y_pred,
        ticker,
        sector,
        industry,
        train_score,
        test_score,
    )

    return results_df, train_score, test_score


def create_decision_tree_model(df):
    # Prepare the dataframe for regression
    df_train_test, df_pred, ticker, sector, industry = prep_df_for_regression(df.copy())

    # Train/Test split
    X_train, y_train, dates_train, X_test, y_test, dates_test = train_test_split(
        df_train_test
    )

    # Fit the model
    regr = DecisionTreeRegressor(random_state=42)
    regr.fit(X_train, y_train)
    train_score = regr.score(X_train, y_train)

    # Test the fit
    y_hat = regr.predict(X_test)
    test_score = r2_score(y_test, y_hat)

    # Predict future values
    X_pred = df_pred.drop(["Close_1yr"], axis=1).values
    dates_pred = df_pred.index
    X_pred = transform_cross_decomposition(X_pred)
    y_pred = regr.predict(X_pred)

    # Convert back to normal values
    X_pred, y_pred = inverse_transform_cross_decompisition(X_pred, y_pred)

    # Create dataframe with results
    results_df = create_combined_results_df(
        df,
        dates_test,
        y_hat,
        dates_pred,
        y_pred,
        ticker,
        sector,
        industry,
        train_score,
        test_score,
    )

    return results_df, train_score, test_score


def create_neural_network_model(df):
    # Prepare the dataframe for regression
    df_train_test, df_pred, ticker, sector, industry = prep_df_for_regression(df.copy())

    # Train/Test split
    X_train, y_train, dates_train, X_test, y_test, dates_test = train_test_split(
        df_train_test
    )

    # Fit the model
    regr = MLPRegressor(
        random_state=42, max_iter=1000, early_stopping=True, learning_rate="adaptive"
    )
    regr.fit(X_train, y_train)
    train_score = regr.score(X_train, y_train)

    # Test the fit
    y_hat = regr.predict(X_test)
    test_score = r2_score(y_test, y_hat)

    # Predict future values
    X_pred = df_pred.drop(["Close_1yr"], axis=1).values
    dates_pred = df_pred.index
    X_pred = transform_cross_decomposition(X_pred)
    y_pred = regr.predict(X_pred)

    # Convert back to normal values
    X_pred, y_pred = inverse_transform_cross_decompisition(X_pred, y_pred)

    # Create dataframe with results
    results_df = create_combined_results_df(
        df,
        dates_test,
        y_hat,
        dates_pred,
        y_pred,
        ticker,
        sector,
        industry,
        train_score,
        test_score,
    )

    return results_df, train_score, test_score


# def create_arima_model(df):
#     # Prepare the dataframe for regression
#     df_train_test, df_pred, ticker, sector, industry = prep_df_for_regression(df.copy())

#     # Train/Test split
#     X_train, y_train, dates_train, X_test, y_test, dates_test = train_test_split(df_train_test)

#     # Fit the model
#     regr = ARIMA(df_train_test['Close'], order=(7,0,7)).fit()
#     forecasts = regr.forecast(365)
#     train_score = r2_score(df_pred['Close'].values, forecasts.tail(365).values)

#     # Test the fit
#     y_hat = regr.forecast(len(y_test))
#     test_score = r2_score(y_test, y_hat)

#     # Predict future values
#     X_pred = df_pred.drop(['Close_1yr'], axis=1).values
#     dates_pred = df_pred.index
#     X_pred = transform_cross_decomposition(X_pred)
#     y_pred = regr.predict(len(X_pred))

#     # Convert back to normal values
#     X_pred, y_pred = inverse_transform_cross_decompisition(X_pred, y_pred)

#     # Create dataframe with results
#     results_df = create_combined_results_df(df, dates_test, y_hat, dates_pred, y_pred, ticker, sector, industry, train_score, test_score)

#     return results_df, train_score, test_score

# def create_arima_model_OLD(df):
#     ticker = df['ticker'].unique()[0]
#     sector = df['sector'].unique()[0]
#     industry = df['industry'].unique()[0]
#     df_past, df_current = prep_df_for_regression(df.copy())

#     y = df_past['Close_1yr'].values
#     X = df_past.drop(['Close_1yr'], axis=1)
#     X.reset_index(inplace=True)
#     dates = X['Date'].values
#     X.drop(['Date'], axis=1, inplace=True)
#     X = X.values
#     tscv = TimeSeriesSplit(n_splits=2)
#     X_train = None
#     X_test = None
#     y_train = None
#     y_test = None
#     dates_train = None
#     dates_test = None
#     for train_index, test_index in tscv.split(X):
#         X_train, X_test = X[train_index], X[test_index]
#         y_train, y_test = y[train_index], y[test_index]
#         dates_train, dates_test = dates[train_index], dates[test_index]

#     regr = ARIMA(df_past['Close'], order=(7,0,7)).fit()

#     # Fit the model
#     forecasts = regr.forecast(365)
#     # print("Close this year")
#     # print(df_current['Close'])
#     # print("Forecasts")
#     # print(forecasts)

#     train_score = r2_score(df_current['Close'].values, forecasts.tail(365).values)

#     # Test the fit
#     y_hat = regr.forecast(len(y_test))
#     test_df = pd.DataFrame(index=dates_test, columns=['prediction'], data=y_hat)
#     test_df.index = test_df.index + timedelta(days=365)
#     test_score = r2_score(y_test, y_hat)

#     # Predict future values
#     X_pred = df_current.drop(['Close_1yr'], axis=1).values
#     y_pred = regr.predict(len(X_pred))
#     pred_df = pd.DataFrame(index=df_current.index, columns=['prediction'], data=y_pred)
#     pred_df.index = pred_df.index + timedelta(days=365)

#     # Combine test and future values
#     combined_df = pd.concat([test_df, pred_df])
#     combined_df.index.names = ['Date']
#     results_df = combined_df.merge(df, how='left', left_index=True, right_index=True)
#     results_df['predicted_1yr_growth'] = (results_df['prediction'] - results_df['Close'].shift(365))/results_df['Close'].shift(365)
#     results_df = results_df[['prediction', 'Close', 'predicted_1yr_growth']]
#     results_df['ticker'] = ticker
#     results_df['sector'] = sector
#     results_df['industry'] = industry
#     results_df['train_score'] = train_score
#     results_df['test_score'] = test_score

#     return results_df


def perform_cross_decomposition(X, y):
    # print(X.shape, y.shape)
    global cca
    cca.fit(X, y)
    X_cca, y_cca = cca.transform(X, y)
    return X_cca, y_cca


def transform_cross_decomposition(X):
    global cca
    X_cca = cca.transform(X)
    return X_cca


def inverse_transform_cross_decompisition(X, y):
    global cca
    y = np.reshape(y, (-1, 1))
    X_cca, y_cca = cca.inverse_transform(X, y)
    return X_cca, y_cca


def store_results_in_mongo(df, regr_col):
    # mydb = mongo.get_mongo_connection()
    # regr_col = mydb["regr_model_results"]
    df.reset_index(inplace=True)
    regr_col.insert_many(df.to_dict("records"))


def initialize_stock_predictions(start_date, end_date):
    mydb = mongo.get_mongo_connection()
    regr_col = mydb["regr_model_results"]
    regr_col.drop()
    yahoo_col = mydb["yahoo"]
    companies_df = sec.retrieve_companies_from_sec()
    tickers = list(companies_df["ticker"])
    start_date_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    for ticker in tickers:
        print("Training model for ticker: " + ticker)
        results = list(yahoo_col.find({"ticker": ticker}).sort("Date", 1).limit(1))
        # print(start_date_datetime, results[0]["Date"])
        if len(results) > 0 and start_date_datetime >= results[0]["Date"]:
            df = create_combined_dataframe(ticker, start_date, end_date)
            pred_df, train_score, test_score = create_random_forest_model(df)
            # pred_df, train_score, test_score = create_gradient_boosted_tree_model(df)
            # pred_df, train_score, test_score = create_decision_tree_model(df)
            # pred_df, train_score, test_score = create_neural_network_model(df)
            # pred_df, train_score, test_score = create_arima_model(df)
            store_results_in_mongo(pred_df, regr_col)
            # print(pred_df.tail(1))
        else:
            print("Training aborted for ticker: " + ticker + " (not enough data)")


def retrieve_model_results_from_mongo():
    mydb = mongo.get_mongo_connection()
    regr_col = mydb["regr_model_results"]
    results_df = pd.DataFrame()
    last_date = list(regr_col.find().sort("Date", -1).limit(1))[0]["Date"]
    results_df = pd.DataFrame(list(regr_col.find({"Date": last_date})))
    results_df.dropna(subset=["predicted_1yr_growth"], inplace=True)
    results_df.sort_values(by=["predicted_1yr_growth"], ascending=False, inplace=True)
    # print(results_df['close_pct_1yr'])
    return results_df
