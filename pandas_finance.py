#!/usr/bin/env python
""" pandas_finance.

Usage:
    pandas_finance.py STOCKS_AS_TEXT_FILE

Arguments:
    STOCKS_AS_TEXT_FILE comma separated stock ticker symbols, FB,TWTR
"""
import datetime
import os
import random
import sqlite3
import sys

import pandas.io.data as web
import pandas.io.sql as sql

from dshelpers import update_status

def get_stock(stock, start, end):
    """
    Return data frame of Yahoo! Finance data for stock.

    Takes stock name and start and end dates as datetimes.
    """
    return web.DataReader(stock, 'yahoo', start, end)


def scrape_stock(stock, start, end):
    """
    Write SQLite table of stock data from Yahoo! Finance

    Take a stock name and start and end dates as datetimes.
    """
    frame = (get_stock(stock, start, end))
    # make Date not an index so it appears in table
    frame = frame.reset_index()
    # force Date datetime to string
    frame[['Date']] = frame[['Date']].applymap(lambda x: x.isoformat())
    frame['Stock'] = stock
    write_frame_to_sql(frame)


def write_frame_to_sql(frame):
    """ Write Pandas dataframe to SQLite database. """
    sql.write_frame(frame, 'stocks', sqlite_db, if_exists='append')


def parse_wanted_stocks(stocks_string):
    """
    Take comma-separated string of stocks; return list of strings.
    >>> parse_wanted_stocks('TWTR,FB')
    ['TWTR', 'FB']
    >>> parse_wanted_stocks('TWTR')
    ['TWTR']
    """
    return stocks_string.split(',')


def get_required_tickers(textfile):
    """
    Open file containing a string like TWTR,FB; return as string.
    """
    with open(textfile, 'r') as f:
        return f.read().rstrip('\n')


def install_crontab():
    """
    Install crontab.

    Taken from Twitter followers tool.
    """
    if not os.path.isfile("crontab"):
        #logging.warn("Crontab not detected. Installing...")
        crontab = open("tool/crontab.template").read()
        # ... run at a random minute to distribute load
        crontab = crontab.replace("RANDMN", str(random.randint(0, 59)))
        crontab = crontab.replace("RANDHR", str(random.randint(0, 23)))
        open("crontab", "w").write(crontab)
    #else:
    #    logging.info("Crontab present. Activating...")
    os.system("crontab crontab")


def main():
    """
    Save stock ticker data from Yahoo! Finance to sqlite.
    """
    # Yahoo: "Historical prices typically do not go back further than 1970"
    start = datetime.datetime(1900, 1, 1, 0, 0)
    end = datetime.datetime.today()
    global sqlite_db
    sqlite_db = sqlite3.connect("scraperwiki.sqlite")
    sqlite_db.execute("drop table if exists {};".format('stocks'))

    tickers = get_required_tickers(sys.argv[1])
    for ticker in parse_wanted_stocks(tickers):
        scrape_stock(ticker, start, end)

    update_status('stocks')
    # if all looks well, schedule
    install_crontab()


if __name__ == '__main__':
    main()
