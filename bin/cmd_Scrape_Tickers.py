#!/usr/bin/env python

import logging as log
from libBusinessLogic import YAHOO_SCRAPER, BASE_PANDAS_FINANCE
from libCommon import find_subset, LOG_FORMAT_TEST
from libUtils import ENVIRONMENT, mkdir
from libNASDAQ import NASDAQ
from libDecorators import exit_on_exception, singleton
from libDebug import trace


"""
1) pull all stocks and funds (tickers) from NASDAQ
2) use pandas interface to scrape historical price data
3) save to local directories
"""

@singleton
class VARIABLES() :
    var_names = ['env','data_store_stock', 'data_store_fund','fund_list','stock_list', 'etf_list', 'alias','scraper']
    def __init__(self) :
        self.__dict__.update(**find_subset(globals(),*VARIABLES.var_names))

@trace
def refresh(**kwargs) :
    ticker_list = kwargs.pop('ticker_list',[])
    data_store = kwargs.pop('data_store',[])
    scraper = kwargs.pop('scraper',{})
    retry = BASE_PANDAS_FINANCE.SAVE(data_store, *ticker_list, **scraper)
    if len(retry) > 0 :
       log.warning((len(retry),sorted(retry)))
       retry = BASE_PANDAS_FINANCE.SAVE(data_store, *retry, **scraper)
    if len(retry) > 0 :
       log.error((len(retry), sorted(retry)))

@exit_on_exception
@trace
def get_tickers() :
    nasdaq = NASDAQ.init()
    stock_list, etf_list, alias_list = nasdaq.stock_list()
    fund_list = nasdaq.fund_list()
    stock_list = stock_list.index.values.tolist()
    etf_list = etf_list.index.values.tolist()
    fund_list = fund_list.index.values.tolist()
    alias = []
    for column in alias_list.columns.values.tolist() :
        alias.extend(alias_list[column].tolist())
    alias = sorted(list(set(alias)))
    log.info(alias)
    return fund_list,stock_list, etf_list, alias

@exit_on_exception
@trace
def main() : 
    mkdir(VARIABLES().data_store_stock)
    mkdir(VARIABLES().data_store_fund)

    args = find_subset(vars(VARIABLES()),*VARIABLES.var_names)
    args['ticker_list'] = VARIABLES().stock_list
    args['data_store'] = VARIABLES().data_store_stock
    refresh(**args)
    args['ticker_list'] = VARIABLES().etf_list
    #refresh(**args)
    args['ticker_list'] = VARIABLES().fund_list
    args['data_store'] = VARIABLES().data_store_fund
    #refresh(**args)

if __name__ == '__main__' :
   import sys
   import logging as log
   from libUtils import ENVIRONMENT

   env = ENVIRONMENT.instance()
   log_filename = '{pwd_parent}/log/{name}.log'.format(**vars(env))
   log.basicConfig(filename=log_filename, filemode='w', format=LOG_FORMAT_TEST, level=log.INFO)
   #log.basicConfig(stream=sys.stdout, format=log_msg, level=log.DEBUG)

   scraper = YAHOO_SCRAPER().pandas()
   fund_list,stock_list, etf_list, alias = get_tickers()

   data_store_stock = '{}/local/historical_prices'.format(env.pwd_parent)
   data_store_fund = '{}/local/historical_prices_fund'.format(env.pwd_parent)
   main()

