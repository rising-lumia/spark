import os
import numpy as np
import pandas as pd
import datetime as dt
import time
import sqlalchemy
from settings import *

def startup_home(PGUSER=PGUSER, PGPASSWORD=PGPASSWORD, PGDATABASE=PGDATABASE, PGHOST=PGHOST, PGPORT=PGPORT):
    engine = sqlalchemy.create_engine('postgresql://'+PGUSER+':'+PGPASSWORD+'@'+PGHOST+':'+PGPORT+'/'+PGDATABASE)
    con = engine.connect()

    future_decision_table = pd.read_sql_table('rising_spark_future_decision', con = engine, schema = 'spark')
    fd_table_stk_open = pd.read_sql_table('rising_spark_fd_open', con = engine, schema = 'spark')
    fd_table_stk_close = pd.read_sql_table('rising_spark_fd_close', con = engine, schema = 'spark')
    fd_table_stk_hold = pd.read_sql_table('rising_spark_fd_hold', con = engine, schema = 'spark')
    decision_count = pd.read_sql_table('rising_spark_decision_count', con = engine, schema = 'spark')
    spy_df = pd.read_sql_table('rising_spark_spy_ta_chart', con = engine, schema = 'spark')
    range_breaks = pd.read_sql_table('rising_spark_range_breaks', con = engine, schema = 'spark')
    
    return future_decision_table, fd_table_stk_open, fd_table_stk_close, fd_table_stk_hold, decision_count, spy_df, range_breaks
