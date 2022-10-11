import pandas as pd
import numpy as np
import os


class GetData:
    def __init__(self):
        self.data = {}

    def from_yfinance(self, ticker):
        return None

    def from_SEC(self, ticker):
        return None

    def from_FRED(self, ticker):
        return None

    def from_reddit(self, ticker, sub):
        return None

    def from_twitter(self, ticker):
        return None


if __name__ == '__main__':
    ...
