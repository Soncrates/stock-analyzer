#!/usr/bin/env python

import logging as log
import pandas as pd
from libCommon import INI_WRITE
from libCommon import load_config, iterate_config, find_subset
from libUtils import mkdir
from libBackground import main as EXTRACT_BACKGROUND, load as TICKER, TRANSFORM_TICKER
from libDecorators import singleton, exit_on_exception, log_on_exception
from libDebug import trace, debug_object

def get_globals(*largs) :
    ret = {}
    for name in largs :
        value = globals().get(name,None)
        if value is None :
           continue
        ret[name] = value
    return ret

def _get_config(*config_list) :
    for i, path in enumerate(sorted(config_list)) :
        for j,k, section, key, value in iterate_config(load_config(path)):
            yield path, section, key, value

def get_benchmarks(config,benchmarks,omit_list) :
    ret = {}
    for path, section, key, stock in _get_config(config) :
        if section not in benchmarks :
           continue
        log.info((section,key,stock))
        ret[key] = stock
    for omit in omit_list :
        ret.pop(omit,None)
    log.info(ret)
    return ret

@singleton
class VARIABLES() :
    var_names = ['env','data_store','output_file','config_file','benchmarks','omit_list']
    def __init__(self) :
        self.__dict__.update(**find_subset(globals(),*VARIABLES.var_names))
        debug_object(self)

        mkdir(self.data_store)
        if len(self.env.argv) > 1 :
           self.config_file = [self.env.argv[1]]
        if len(self.env.argv) > 2 :
           self.output_file = [self.env.argv[2]]

        data = get_benchmarks(self.config_file, self.benchmarks, self.omit_list)
        self.data = data
        self.stock_names = data.values()

def prep(data_store,stock_list) : 
    TICKER(data_store=data_store, ticker_list=stock_list)
    ret = EXTRACT_BACKGROUND(data_store=data_store, ticker_list=stock_list)
    log.debug(ret)
    return ret

def business_logic(ret) : 
    data = VARIABLES().data
    ret = ret.T
    names = TRANSFORM_TICKER.data(data)
    names = pd.DataFrame([names]).T
    ret['NAME'] = names
    #ret = ret.dropna(thresh=2)
    ret = ret.fillna(-1)
    ret = ret.to_dict()
    log.debug(type(ret))
    return ret

@exit_on_exception
@trace
def main() : 

    ret = prep(VARIABLES().data_store,VARIABLES().stock_names)
    ret = business_logic(ret)

    save_file = VARIABLES().output_file
    INI_WRITE.write(save_file,**ret)
    log.info("results saved to {}".format(save_file))

if __name__ == '__main__' :
   #import sys
   from libUtils import ENVIRONMENT

   env = ENVIRONMENT.instance()
   log_filename = '{pwd_parent}/log/{name}.log'.format(**vars(env))
   log_msg = '%(module)s.%(funcName)s(%(lineno)s) %(levelname)s - %(message)s'
   log.basicConfig(filename=log_filename, filemode='w', format=log_msg, level=log.DEBUG)
   #logging.basicConfig(stream=sys.stdout, format=log_msg, level=logging.INFO)

   data_store = '{}/local/historical_prices'.format(env.pwd_parent)
   output_file = "{}/local/benchmark_background.ini".format(env.pwd_parent)

   ini_list = env.list_filenames('local/*.ini')
   config_file = filter(lambda x : 'benchmark' in x, ini_list)
   config_file = [ filename for filename in ini_list if 'benchmark' in filename ]
   benchmarks = ['Index','MOTLEYFOOL','PERSONAL']
   benchmarks = ['Index']
   omit_list = ['ACT Symbol', 'CQS Symbol', 'alias', 'unknown']

   main()
