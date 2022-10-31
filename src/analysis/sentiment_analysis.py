from flask import url_for, redirect, session, request
from flask.blueprints import Blueprint
import requests
import praw

bp = Blueprint('sentiment', __name__, url_prefix='/sentiment')


@bp.route('/social_credentials', methods=["POST"])
def store_social_credentials():
    session['reddit_client_id'] = request.form['reddit_client']
    session['reddit_secret_key'] = request.form['reddit_secret']
    session['twitter_client_id'] = request.form['twitter_client']
    session['twitter_secret_key'] = request.form['twitter_secret']
    return redirect(url_for('/dash/'))


def initialize_reddit():
    reddit = praw.Reddit(
        client_id=session['reddit_client_id'],
        client_secret=session['reddit_secret_key'],
        user_agent="Sentiment Analysis by Market Shopper (u/tiaaburton)"
    )

