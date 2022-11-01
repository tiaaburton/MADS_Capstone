from flask import url_for, redirect, session, request
from flask.blueprints import Blueprint
import requests
import praw
import json

bp = Blueprint("sentiment", __name__, url_prefix="/sentiment")



@bp.route('/social_credentials', methods=["POST"])
def store_social_credentials():
    session['reddit_client_id'] = request.form['reddit_client']
    session['reddit_secret_key'] = request.form['reddit_secret']
    session['twitter_bearer_token'] = request.form['twitter_bearer_token']
    return redirect(url_for('/dash/'))


def initialize_reddit():
    reddit = praw.Reddit(
        client_id=session["reddit_client_id"],
        client_secret=session["reddit_secret_key"],
        user_agent="Sentiment Analysis by Market Shopper (u/tiaaburton)",
    )


def search_twitter(query, tweet_fields):
    bearer_token = request.form['twitter_bearer_token']

    headers = {"Authorization": "Bearer {}".format(bearer_token)}

    url = "https://api.twitter.com/2/tweets/search/recent?query={}&{}".format(
        query, tweet_fields
    )
    response = requests.request("GET", url, headers=headers)

    print(response.status_code)

    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()


if __name__ == '__main__':
    # Test search term
    query = "TSLA"
    # twitter fields to be returned by api call
    tweet_fields = "tweet.fields=text,author_id,created_at"

    # twitter api call
    json_response = search_twitter(query=query, tweet_fields=tweet_fields)
    # pretty printing
    print(json.dumps(json_response, indent=4, sort_keys=True))

