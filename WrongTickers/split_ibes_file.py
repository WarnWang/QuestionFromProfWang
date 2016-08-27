#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Project: QuestionFromProfWang
# File name: split_ibes_file
# Author: Mark Wang
# Date: 18/8/2016

import os

import pandas as pd

df = pd.read_csv('Stock_data/IBES_detail_1970_2016.csv', usecols=['CUSIP', 'FPEDATS', 'ACTUAL', 'VALUE'],
                 dtype={'CUSIP': str, 'FPEDATS': str})

cusip_group = df.groupby('CUSIP')
for name, group in cusip_group:
    file_name = os.path.join('Stock_data', 'ibes_cusip', '{}_IBES.csv'.format(name))
    group.to_csv(file_name, encoding='utf8', index=False)
del df

df = pd.read_csv('Stock_data/IBES_detail_1970_2016.csv', usecols=['OFTIC', 'FPEDATS', 'ACTUAL', 'VALUE'],
                 dtype={'FPEDATS': str})
ticker_group = df.groupby('OFTIC')
for name, group in ticker_group:
    file_name = os.path.join('Stock_data', 'ibes', '{}_IBES.csv'.format(name))
    group.to_csv(file_name, encoding='utf8', index=False)
