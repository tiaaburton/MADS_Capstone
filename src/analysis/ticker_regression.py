# import sys
# sys.path.insert(0, 'D:\Documents\MarketShoppers\MADS_Capstone\src')

# import data.sec as sec
# import data.yahoo as yahoo
# import data.fred as fred
# import data.mongo as mongo

import src.data.sec as sec
import src.data.yahoo as yahoo
import src.data.fred as fred
import src.data.mongo as mongo

import pandas as pd
import numpy as np
import warnings

from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.dummy import DummyRegressor

from statsmodels.tsa.arima.model import ARIMA

from sklearn.cross_decomposition import CCA
from sklearn.cross_decomposition import PLSRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import r2_score
from datetime import timedelta
from datetime import datetime
import numpy as np

cca = CCA(n_components=1)
# cca = PLSRegression(n_components=1)


def create_combined_dataframe(ticker, start_date, end_date):
    # Create empty dataframe with dates to combine the results
    date_index = pd.to_datetime(pd.date_range(start_date, end_date), format="%Y-%m-%d")
    combined_df = pd.DataFrame(index=date_index)
    combined_df.index.names = ["Date"]

    # Retrieve from Yahoo
    # print("Retrieving Yahoo data...")
    yahoo_df = yahoo.retrieve_company_stock_price_from_mongo(ticker)
    # yahoo_df["Date"] = pd.to_datetime(yahoo_df["Date"]).apply(lambda x: pd.Timestamp(x).replace(hour=0, minute=0, second=0))
    yahoo_df["Date"] = pd.to_datetime(yahoo_df["Date"]).dt.floor('D')
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
    # prefill_df.to_excel('prefill_v3.xlsx')
    combined_df.ffill(limit=100, inplace=True)
    combined_df.bfill(limit=100, inplace=True)
    # combined_df.to_excel('postfill_v3.xlsx')
    combined_df.dropna(axis=1, how="any", inplace=True)
    # combined_df.to_excel('postdrop_v3.xlsx')
    # print("Returning combined_df")
    return combined_df


def prep_df_for_regression(df):
    ticker = df["ticker"].unique()[0]
    sector = df["sector"].unique()[0]
    industry = df["industry"].unique()[0]

    # df.drop(['ticker', 'sector', 'industry', 'Open', 'High', 'Low', 'Volume', 'Dividends', 'Stock Splits', 'wma_7', 'wma_30', 'wma_60', 'wma_120', 'close_pct_1d', 'close_pct_30d', 'close_pct_60d', 'close_pct_120d', 'close_pct_1yr', 'targetLowPrice', 'targetMeanPrice', 'targetMedianPrice', 'targetHighPrice'], axis=1, inplace=True)
    # df.drop(['ticker', 'sector', 'industry', 'Open', 'High', 'Low', 'Volume', 'Stock Splits', 'wma_7', 'wma_30', 'wma_60', 'wma_120', 'close_pct_1d', 'close_pct_30d', 'close_pct_60d', 'close_pct_120d', 'close_pct_1yr'], axis=1, inplace=True)
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
    y = df["Close_1yr"]
    X = df.drop(["Close_1yr"], axis=1)
    X.reset_index(inplace=True)
    dates = X["Date"]
    X.drop(["Date"], axis=1, inplace=True)
    X = X
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
        X_train, X_test = X.iloc[train_index], X.iloc[test_index]
        y_train, y_test = y.iloc[train_index], y.iloc[test_index]
        dates_train, dates_test = dates.iloc[train_index], dates.iloc[test_index]

    ### The below cross decomposition and standard scalar was used in Milestone II with contributions by Egor Kopylov and Henry C Wong. ###
    ### After testing other approaches, we decided to reuse the cross decomposition and standard scalar approach here as it produced the best results ###
    # Perform dimensionality reduction on the features, taking into account the relationship with y
    X_train, y_train = perform_cross_decomposition(X_train, y_train)
    X_test, y_test = perform_cross_decomposition(X_test, y_test)

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

def create_combined_results_df_with_uncertainty(
    df,
    dates_test,
    y_hat,
    y_hat_lower,
    y_hat_upper,
    dates_pred,
    y_pred,
    y_pred_lower,
    y_pred_upper,
    ticker,
    sector,
    industry,
    train_score,
    test_score,
):
    y_hat = np.reshape(y_hat, (1,-1))[0]
    y_hat_lower = np.reshape(y_hat_lower, (1,-1))[0]
    y_hat_upper = np.reshape(y_hat_upper, (1,-1))[0]
    y_pred = np.reshape(y_pred, (1,-1))[0]
    y_pred_lower = np.reshape(y_pred_lower, (1,-1))[0]
    y_pred_upper = np.reshape(y_pred_upper, (1,-1))[0]

    # Create test results dataframe
    data = {"prediction": y_hat, "prediction_lower": y_hat_lower, "prediction_upper": y_hat_upper}
    test_df = pd.DataFrame(index=dates_test, data=data)
    test_df.index = test_df.index + timedelta(days=365)

    # Create prediction results dataframe
    data = {"prediction": y_pred, "prediction_lower": y_pred_lower, "prediction_upper": y_pred_upper}
    pred_df = pd.DataFrame(index=dates_pred, data=data)
    pred_df.index = pred_df.index + timedelta(days=365)

    # Combine test and future values
    combined_df = pd.concat([test_df, pred_df])
    combined_df.index.names = ["Date"]

    results_df = combined_df.merge(df, how="left", left_index=True, right_index=True)
    results_df["predicted_1yr_growth"] = (
        results_df["prediction"] - results_df["Close"].shift(365)
    ) / results_df["Close"].shift(365)
    results_df["predicted_1yr_growth_upper"] = (
        results_df["prediction_upper"] - results_df["Close"].shift(365)
    ) / results_df["Close"].shift(365)
    results_df["predicted_1yr_growth_lower"] = (
        results_df["prediction_lower"] - results_df["Close"].shift(365)
    ) / results_df["Close"].shift(365)
    
    results_df = results_df[["prediction", "prediction_lower", "prediction_upper", "predicted_1yr_growth", "predicted_1yr_growth_lower", "predicted_1yr_growth_upper", "Close"]]
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
    X_pred = df_pred.drop(["Close_1yr"], axis=1)
    dates_pred = df_pred.index
    X_pred = transform_cross_decomposition(X_pred)
    y_pred = regr.predict(X_pred)

    # Convert back to normal values
    X_test, y_hat = inverse_transform_cross_decompisition(X_test, y_hat)
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
    ### Followed guide on how to show uncertainty in gradient boosted regressor from Will Koerhsen's Towards Data Science article here: https://towardsdatascience.com/how-to-generate-prediction-intervals-with-scikit-learn-and-python-ab3899f992ed
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore")
        regr = GradientBoostingRegressor(
            n_estimators=750,
            max_depth=5,
            random_state=42,
            min_samples_split=5,
            learning_rate=0.02,
            loss="ls",
        )
        regr_lower = GradientBoostingRegressor(
            n_estimators=750,
            max_depth=5,
            random_state=42,
            min_samples_split=5,
            learning_rate=0.02,
            loss="quantile",
            alpha=0.05
        )
        regr_upper = GradientBoostingRegressor(
            n_estimators=750,
            max_depth=5,
            random_state=42,
            min_samples_split=5,
            learning_rate=0.02,
            loss="quantile",
            alpha=0.95
        )
        regr.fit(X_train, y_train)
        regr_lower.fit(X_train, y_train)
        regr_upper.fit(X_train, y_train)
    train_score = regr.score(X_train, y_train)

    # Test the fit
    y_hat = regr.predict(X_test)
    y_hat_lower = regr_lower.predict(X_test)
    y_hat_upper = regr_upper.predict(X_test)
    test_score = r2_score(y_test, y_hat)

    # Predict future values
    X_pred = df_pred.drop(["Close_1yr"], axis=1)
    dates_pred = df_pred.index
    X_pred = transform_cross_decomposition(X_pred)
    y_pred = regr.predict(X_pred)
    y_pred_lower = regr_lower.predict(X_pred)
    y_pred_upper = regr_upper.predict(X_pred)

    # Convert back to normal values
    X_test_lower, y_hat_lower = inverse_transform_cross_decompisition(X_test, y_hat_lower)
    X_test_upper, y_hat_upper = inverse_transform_cross_decompisition(X_test, y_hat_upper)
    X_test, y_hat = inverse_transform_cross_decompisition(X_test, y_hat)
    X_pred_lower, y_pred_lower = inverse_transform_cross_decompisition(X_pred, y_pred_lower)
    X_pred_upper, y_pred_upper = inverse_transform_cross_decompisition(X_pred, y_pred_upper)
    X_pred, y_pred = inverse_transform_cross_decompisition(X_pred, y_pred)

    # Create dataframe with results
    results_df = create_combined_results_df_with_uncertainty(
        df,
        dates_test,
        y_hat,
        y_hat_lower,
        y_hat_upper,
        dates_pred,
        y_pred,
        y_pred_lower,
        y_pred_upper,
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
    X_pred = df_pred.drop(["Close_1yr"], axis=1)
    dates_pred = df_pred.index
    X_pred = transform_cross_decomposition(X_pred)
    y_pred = regr.predict(X_pred)

    # Convert back to normal values
    X_test, y_hat = inverse_transform_cross_decompisition(X_test, y_hat)
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
    X_pred = df_pred.drop(["Close_1yr"], axis=1)
    dates_pred = df_pred.index
    X_pred = transform_cross_decomposition(X_pred)
    y_pred = regr.predict(X_pred)

    # Convert back to normal values
    X_test, y_hat = inverse_transform_cross_decompisition(X_test, y_hat)
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

def create_dummy_mean_model(df):
    # Prepare the dataframe for regression
    df_train_test, df_pred, ticker, sector, industry = prep_df_for_regression(df.copy())

    # Train/Test split
    X_train, y_train, dates_train, X_test, y_test, dates_test = train_test_split(
        df_train_test
    )

    # Fit the model
    regr = DummyRegressor(
        strategy='mean'
    )
    regr.fit(X_train, y_train)
    train_score = regr.score(X_train, y_train)

    # Test the fit
    y_hat = regr.predict(X_test)
    test_score = r2_score(y_test, y_hat)

    # Predict future values
    X_pred = df_pred.drop(["Close_1yr"], axis=1)
    dates_pred = df_pred.index
    X_pred = transform_cross_decomposition(X_pred)
    y_pred = regr.predict(X_pred)

    # Convert back to normal values
    X_test, y_hat = inverse_transform_cross_decompisition(X_test, y_hat)
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

def create_arima_model(df):
    ticker = df['ticker'].unique()[0]
    sector = df['sector'].unique()[0]
    industry = df['industry'].unique()[0]
    df_train_test, df_pred, ticker, sector, industry = prep_df_for_regression(df.copy())

    y = df_train_test['Close_1yr'].values
    X = df_train_test.drop(['Close_1yr'], axis=1)
    X.reset_index(inplace=True)
    dates = X['Date'].values
    X.drop(['Date'], axis=1, inplace=True)
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

    regr = ARIMA(df_train_test['Close'], order=(365,0,90)).fit()

    # Fit the model
    forecasts = regr.forecast(365)

    train_score = r2_score(df_pred['Close'].values, forecasts.tail(365).values)

    # Test the fit
    y_hat = regr.forecast(len(y_test))
    test_df = pd.DataFrame(index=dates_test, columns=['prediction'], data=y_hat)
    test_df.index = test_df.index + timedelta(days=365)
    test_score = r2_score(y_test, y_hat)

    # Predict future values
    X_pred = df_pred.drop(['Close_1yr'], axis=1).values
    y_pred = regr.predict(len(X_pred))
    pred_df = pd.DataFrame(index=df_pred.index, columns=['prediction'], data=y_pred)
    pred_df.index = pred_df.index + timedelta(days=365)

    # Combine test and future values
    combined_df = pd.concat([test_df, pred_df])
    combined_df.index.names = ['Date']
    results_df = combined_df.merge(df, how='left', left_index=True, right_index=True)
    results_df['predicted_1yr_growth'] = (results_df['prediction'] - results_df['Close'].shift(365))/results_df['Close'].shift(365)
    results_df = results_df[['prediction', 'Close', 'predicted_1yr_growth']]
    results_df['ticker'] = ticker
    results_df['sector'] = sector
    results_df['industry'] = industry
    results_df['train_score'] = train_score
    results_df['test_score'] = test_score

    return results_df, train_score, test_score

def perform_cross_decomposition(X, y):
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

def initialize_stock_predictions(start_date, end_date):
    mydb = mongo.get_mongo_connection()
    regr_col = mydb["regr_model_results"]
    regr_col.drop()
    yahoo_col = mydb["yahoo"]
    companies_df = sec.retrieve_companies_from_sec()
    tickers = list(companies_df["ticker"])
    # tickers = ['MSFT', 'GOOG', 'AAPL', 'META', 'GE', 'GS']
    start_date_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    for ticker in tickers:
        print("Training model for ticker: " + ticker)
        results = list(yahoo_col.find({"ticker": ticker}).sort("Date", 1).limit(1))
        # print(start_date_datetime, results[0]["Date"])
        min_date = datetime.combine(results[0]["Date"], datetime.min.time())
        if len(results) > 0 and start_date_datetime >= min_date:
            df = create_combined_dataframe(ticker, start_date, end_date)
            pred_df, train_score, test_score = create_gradient_boosted_tree_model(df)
            store_results_in_mongo(pred_df, regr_col)
        else:
            print("Training aborted for ticker: " + ticker + " (not enough data)")

def resume_stock_predictions(start_date, end_date):
    mydb = mongo.get_mongo_connection()
    regr_col = mydb["regr_model_results"]
    regr_tickers = list(regr_col.distinct("ticker"))
    yahoo_col = mydb["yahoo"]
    companies_df = sec.retrieve_companies_from_sec()
    all_tickers = list(companies_df["ticker"])
    tickers = list(set(all_tickers) - set(regr_tickers))
    start_date_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    for ticker in tickers:
        print("Training model for ticker: " + ticker)
        results = list(yahoo_col.find({"ticker": ticker}).sort("Date", 1).limit(1))
        min_date = datetime.combine(results[0]["Date"], datetime.min.time())
        if len(results) > 0 and start_date_datetime >= min_date:
            df = create_combined_dataframe(ticker, start_date, end_date)
            pred_df, train_score, test_score = create_neural_network_model(df)
            store_results_in_mongo(pred_df, regr_col)
        else:
            print("Training aborted for ticker: " + ticker + " (not enough data)")

def compare_model_results(start_date, end_date):
    tickers = ['MSFT', 'GOOG', 'AAPL', 'META', 'GE', 'GS']
    rows = tickers
    mydb = mongo.get_mongo_connection()
    yahoo_col = mydb["yahoo"]
    columns = ['random_forest', 'grad_boost_tree', 'decision_tree', 'neural_network', 'arima', 'dummy']
    compare_train_df = pd.DataFrame(index=rows, columns=columns)
    compare_test_df = pd.DataFrame(index=rows, columns=columns)
    start_date_datetime = datetime.strptime(start_date, "%Y-%m-%d")
    for ticker in tickers:
        print("Training models for ticker: " + ticker)
        results = list(yahoo_col.find({"ticker": ticker}).sort("Date", 1).limit(1))
        min_date = datetime.combine(results[0]["Date"], datetime.min.time())
        # if len(results) > 0 and start_date_datetime >= results[0]["Date"]:
        if len(results) > 0 and start_date_datetime >= min_date:
        # if len(results) > 0:
            df = create_combined_dataframe(ticker, start_date, end_date)
            pred_df, train_score, test_score = create_random_forest_model(df)
            compare_train_df.at[ticker, 'random_forest'] = train_score
            compare_test_df.at[ticker, 'random_forest'] = test_score
            pred_df, train_score, test_score = create_gradient_boosted_tree_model(df)
            compare_train_df.at[ticker, 'grad_boost_tree'] = train_score
            compare_test_df.at[ticker, 'grad_boost_tree'] = test_score
            pred_df, train_score, test_score = create_decision_tree_model(df)
            compare_train_df.at[ticker, 'decision_tree'] = train_score
            compare_test_df.at[ticker, 'decision_tree'] = test_score
            pred_df, train_score, test_score = create_neural_network_model(df)
            compare_train_df.at[ticker, 'neural_network'] = train_score
            compare_test_df.at[ticker, 'neural_network'] = test_score
            # pred_df, train_score, test_score = create_arima_model(df)
            # compare_train_df.at[ticker, 'arima'] = train_score
            # compare_test_df.at[ticker, 'arima'] = test_score
            pred_df, train_score, test_score = create_dummy_mean_model(df)
            compare_train_df.at[ticker, 'dummy'] = train_score
            compare_test_df.at[ticker, 'dummy'] = test_score
        else:
            print("Training aborted for ticker: " + ticker + " (not enough data)")
    compare_train_df.loc['Avg Train Score'] = compare_train_df.mean(axis=0)
    compare_test_df.loc['Avg Test Score'] = compare_test_df.mean(axis=0)
    return compare_train_df, compare_test_df

def retrieve_model_results_from_mongo():
    mydb = mongo.get_mongo_connection()
    regr_col = mydb["regr_model_results"]
    results_df = pd.DataFrame()
    last_date = list(regr_col.find().sort("Date", -1).limit(1))[0]["Date"]
    results_df = pd.DataFrame(list(regr_col.find({"Date": last_date})))
    results_df.dropna(subset=["predicted_1yr_growth"], inplace=True)
    results_df.sort_values(by=["predicted_1yr_growth"], ascending=False, inplace=True)
    return results_df

def retrieve_single_ticker_model_results_from_mongo(ticker):
    mydb = mongo.get_mongo_connection()
    regr_col = mydb["regr_model_results"]
    results_df = pd.DataFrame()
    results_df = pd.DataFrame(list(regr_col.find({"ticker": ticker})))
    results_df.drop(labels=["_id"], axis=1, inplace=True)
    results_df["Date"] = pd.to_datetime(model_df["Date"])
    results_df.sort_values(["Date"], ascending=True, inplace=True)
    return results_df

def store_results_in_mongo(df, regr_col):
    df.reset_index(inplace=True)
    regr_col.insert_many(df.to_dict("records"))