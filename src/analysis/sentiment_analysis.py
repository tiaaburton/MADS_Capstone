import os
import math
from pathlib import Path

from flask import url_for, redirect, session, request
from flask.blueprints import Blueprint
import requests
import praw
import json
import configparser
import pandas as pd
import datetime as dt
from typing import Union, Optional
from expertai.nlapi.cloud.client import ExpertAiClient

# Data visualization libraries
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.io as pio

dir_path = str(Path(__file__).parents[1])
config = configparser.ConfigParser(interpolation=None)
config_path = dir_path + "/config.ini"
config.read(config_path)

# Credentials and fields for twitter are set before request function execution
bearer_token = config["TWITTER"]["BEARER_TOKEN"]
headers = {"Authorization": "Bearer {}".format(bearer_token)}

# Set credentials for the Expert AI model. Users get 10 million
# per month. This model will be useful to quantify tweets and reddit posts.
os.environ.setdefault("EAI_USERNAME", config["EAI"]["USERNAME"])
os.environ.setdefault("EAI_PASSWORD", config["EAI"]["PASSWORD"])

bp = Blueprint("sentiment", __name__, url_prefix="/sentiment")

# Initialize reddit client for the remaining data extraction for sentiment analysis
reddit = praw.Reddit(
    client_id=config["REDDIT"]["CLIENT_ID"],
    client_secret=config["REDDIT"]["CLIENT_SECRET"],
    user_agent="Reddit sentiment analysis (u/tiaaburton)",
)


@bp.route("/store_twitter_credentials", methods=["POST"])
def update_twitter():
    config["TWITTER"]["BEARER_TOKEN"] = request.form["twitter_bearer_token"]
    session["twitter_bearer_token"] = request.form["twitter_bearer_token"]
    return redirect(url_for("/dash/"))


@bp.route("/store_reddit_credentials", methods=["POST"])
def update_reddit():
    config["REDDIT"]["CLIENT_ID"] = request.form["reddit_client"]
    config["REDDIT"]["CLIENT_SECRET"] = request.form["reddit_secret"]
    session["reddit_client_id"] = request.form["reddit_client"]
    session["reddit_client_secret"] = request.form["reddit_secret"]
    return redirect(url_for("/dash/"))


def get_time_elements():
    start_date = dt.datetime.utcnow() + dt.timedelta(days=-7, seconds=-8)
    end_date = dt.datetime.utcnow() - dt.timedelta(seconds=30)
    start_date = start_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
    return start_date, end_date


def perform_sentiment_analysis(text):
    client = ExpertAiClient()
    language = "en"

    output = client.specific_resource_analysis(
        body={"document": {"text": text}},
        params={"language": language, "resource": "sentiment"},
    )

    return output.sentiment.overall


class twitter_searches:
    def __init__(self, query: str):
        self.query = query
        self.chart = None
        self.data = None

    def create_chart(self,
                     force_new_data: bool = False,
                     n_tweets: Optional[int] = None,
                     file_name: Optional[str] = "_sentiment.csv"
    ):
        """
        Creates a plotly indicator to share the average
        sentiment given a particular query.
        :param file_name: location to save the
        :param force_new_data: enables searching for new tweets; requires n_tweets param as well
        :param n_tweets: number of tweets to search

        :return self.chart: plotly/dash chart figure
        """
        if force_new_data:
            if n_tweets > 1:
                self.search_n_times(n_iter=n_tweets)

            else:
                self.search_n_times(n_iter=1)
        else:
            self.data = pd.read_csv(dir_path + "/data/twitter_sentiment/" + self.query + file_name)
        chart_value = int(math.ceil(self.data.sentiment.mean()))

        sent = "neutral"
        if chart_value <= 0:
            sent = "slightly bearish"
        elif -35 < chart_value < 0:
            sent = "bearish"
        elif chart_value < -65:
            sent = "very bearish"
        elif 0 < chart_value <= 35:
            sent = "slightly bullish"
        elif 35 < chart_value <= 65:
            sent = "bullish"
        elif chart_value > 65:
            sent = "very bullish"

        fig = go.Figure()
        fig.add_trace(
            go.Indicator(
                mode="delta",
                value=chart_value,
                title={
                    "text": f"<span style='font-size:0.8em;color:gray'>Measure created by averaging</span><br><span style='font-size:0.8em;color:gray'>the sentiment of {self.data.sentiment.count()} tweets last month.</span><br>Twitter is...<br>{sent} on {self.query}"
                },
                delta={"reference": 0},
            )
        )

        fig.update_traces(
            delta_increasing_symbol="🐂 ",
            delta_decreasing_symbol="🐻 ",
            selector=dict(type="indicator"),
        )

        fig.update_layout(
            width=300, height=300, paper_bgcolor="Black", font={"color": "White"}
        )

        self.chart = fig
        return self.chart

    def search_twitter(self):
        """
        Search twitter for the latest 100 tweets
        :param query: Substituting query until the dashboard page is created.
        :return:
        """
        twitter_fields = "tweet.fields=text,author_id,created_at"
        url = "https://api.twitter.com/2/tweets/search/recent?query={}&max_results=100&{}".format(
            self.query, twitter_fields
        )
        response = requests.request("GET", url, headers=headers)

        if response.status_code != 200:
            raise Exception(response.status_code, response.text)
        return response.json()

    def search_n_times(self, n_iter: int = 1):
        """
        Recommended to use this function as it returns a dataframe.
        Searches Twitter n times and returns a dataframe with tweets
        analyzed for their sentiment.

        :param n_iter: Number of calls iterations that should be sent
        to twitter. This should be used sparsely as it does have a rate
        limit.
        :return self.data: pd.DataFrame with sentiment
        """
        if n_iter < 1:
            return pd.DataFrame()

        # Twitter api call with given query
        json_response = self.search_twitter()["data"]
        tweets_df = pd.DataFrame(json_response)

        # search multiple times if requested to have a higher volume
        if n_iter > 1:
            for n in range(2, n_iter + 1):
                search = self.search_twitter()["data"]
                additional_tweets = pd.DataFrame(search)
                tweets_df = tweets_df.append(additional_tweets)

        tweets_df = tweets_df[["created_at", "author_id", "text"]]
        tweets_df['sentiment'] = tweets_df.text.apply(lambda tweet: perform_sentiment_analysis(tweet))
        tweets_df.to_csv(dir_path + "/data/twitter_sentiment/" + self.query + '_sentiment.csv')
        self.data = tweets_df
        return self.data


class twitter_counts:
    def __init__(self, query: str):
        self.query = query
        self.chart = None
        self.data = None
        self.total_tweets = 0

    def count_tweets(self):
        """
        Calls Twitter API with initialized query for the volume of
        tweets over the last 7 days.
        :return:
        """

        # Retrieve the latest 7-day window to retrieve the tweet counts
        start_date, end_date = get_time_elements()

        # Send a request to the Twitter API for the count of tweets
        # for a given query, at a daily granularity, between the
        # start and end date.
        url = "https://api.twitter.com/2/tweets/counts/recent?query={}&granularity=day&start_time={}&end_time={}".format(
            self.query, start_date, end_date
        )
        response = requests.request("GET", url, headers=headers)

        if response.status_code != 200:
            raise Exception(response.status_code, response.text)

        json_response = response.json()

        # After receiving the response, parse the json strong for the data
        self.data = pd.DataFrame(json_response["data"])
        self.data = self.data.drop("end", axis=1).rename(
            columns={"start": "Date", "tweet_count": "Number of Tweets per Day"}
        )
        self.data["Date"] = pd.to_datetime(self.data["Date"]).dt.date
        self.total_tweets = json_response["meta"]["total_tweet_count"]
        return self

    def create_chart(self):
        """
        Creates a line chart to display the volume of tweets
        over the last 7 days.

        :return self.chart: plotly/dash chart figure
        """
        if not self.data:
            self.count_tweets()
        fig = px.line(self.data, x="Date", y="Number of Tweets per Day")
        fig.update_layout(
            {
                "title": {
                    "text": f"Tweet Count for Query<br><sup>The total tweets over the last 7 days is {self.total_tweets}.</sup>"
                }
            },
            paper_bgcolor="Black",
            font={"color": "White"},
        )
        self.chart = fig
        return self.chart


class reddit_chart:
    def __init__(self, query: str, subreddits: str):
        self.query = query
        self.subs = subreddits
        self.chart = None
        self.data = None

    def get_reddit_data(self, file_path: str):
        """
        Retrieves reddit data for the query and sub reddit.
        It requires the values initialized within the element.
        :return self:
        """
        df = pd.DataFrame(
            columns=["query", "date", "title", "post", "combined_text", "sentiment"]
        )
        reddit_results = reddit.subreddit(self.subs).search(
            self.query, sort="hot", time_filter="month"
        )

        for submission in reddit_results:
            combined_text = submission.title + " " + submission.selftext
            parsed_df = pd.DataFrame(
                [
                    [
                        self.query,
                        submission.created,
                        submission.title,
                        submission.selftext,
                        combined_text,
                        perform_sentiment_analysis(submission.title),
                    ]
                ],
                columns=[
                    "query",
                    "date",
                    "title",
                    "post",
                    "combined_text",
                    "sentiment",
                ],
            )
            df = df.append(parsed_df, ignore_index=True)
        df.to_csv(dir_path + "/data/reddit_sentiment/" + file_path)
        self.data = df
        return self

    def create_chart(
        self,
        force_new_data: bool = False,
        file_name: Optional[str] = "_sentiment.csv",
    ):
        """
        Create an indicator for the average sentiment for a query
        within given subreddits. If the average sentiment is above
        0, the indicator will be bullish.
        :param force_new_data:
        :param file_name:
        :return:
        """
        if force_new_data:
            self.get_reddit_data(self.query + file_name)
        else:
            self.data = pd.read_csv(dir_path + "/data/reddit_sentiment/" + self.query + file_name)
        chart_value = int(math.ceil(self.data.sentiment.mean()))

        sent = "neutral"
        if chart_value <= 0:
            sent = "slightly bearish"
        elif -35 < chart_value < 0:
            sent = "bearish"
        elif chart_value < -65:
            sent = "very bearish"
        elif 0 < chart_value <= 35:
            sent = "slightly bullish"
        elif 35 < chart_value <= 65:
            sent = "bullish"
        elif chart_value > 65:
            sent = "very bullish"

        fig = go.Figure()
        fig.add_trace(
            go.Indicator(
                mode="delta",
                value=chart_value,
                title={
                    "text": f"<span style='font-size:0.8em;color:gray'>Measure created by averaging</span><br><span style='font-size:0.8em;color:gray'>the sentiment of {self.data.sentiment.count()} hot posts.</span><br>Reddit is...<br>{sent} on {self.query}"
                },
                delta={"reference": 0},
                # domain={"x": [0.6, 1], "y": [0, 1]},
            )
        )

        fig.update_traces(
            delta_increasing_symbol="🐂 ",
            delta_decreasing_symbol="🐻 ",
            selector=dict(type="indicator"),
        )

        fig.update_layout(
            width=300, height=300, paper_bgcolor="Black", font={"color": "White"}
        )

        self.chart = fig
        return self.chart


if __name__ == "__main__":
    # Test search term
    query1 = "TSLA"
    # twitter fields to be returned by api call
    tweetFields = "tweet.fields=text,author_id,created_at"

    # pretty printing
    # print(json.dumps(json_response, indent=4, sort_keys=True))

    # Test 1: Count tweets for given query
    # counts = twitter_counts(query1)
    # counts.create_chart().show()

    # Test 2: Get sentiment Retrieve sentiment analysis for twitter query results
    # searches = twitter_searches()
    # searches.search_n_times(1, query1, tweetFields)
    # # print(searches.data)
    # searches.create_chart().show()

    # Test 3: Retrieve sentiment analysis for reddit query results
    sub1 = "wallstreetbets+stocks+investing"
    reddit_chart(query1, sub1).create_chart(False, "reddit_sentiment.csv").show()
