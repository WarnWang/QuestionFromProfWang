#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Filename: average_portfolio
# @Date: 2017-03-14
# @Author: Mark Wang
# @Email: wangyouan@gmial.com

import pandas as pd
import numpy as np

from constants import Constant
from util_function import load_stock_info

const = Constant


class Investment(Constant):
    """ This class is each investment account info """

    # end date use to mark the end date of one investment, if this variable is None means that current account is free.
    end_date = None

    # ticker of trade stock
    stock_ticker = None

    # 1 2 Shanghai A B, 4 8 Shenzhen A B, 16 GEM
    sell_stock_type = None
    buy_price = None

    def __init__(self, amount, root_path, stock_price_type=const.STOCK_ADJPRCWD, transaction_cost=0, price_path=None):
        self.init_path(root_path)
        self.amount = amount

        # stock price of previous day
        self.previous_price = None

        # this parameter are used to determine which price are used to calculate the final result
        self.stock_price_type = stock_price_type

        self.transaction_cost = transaction_cost
        self.price_path = price_path

    def is_free(self, current_date):
        """ Whether this investment account has free money """
        return self.end_date is None or current_date >= self.end_date

    def get_current_value(self, current_date):
        """ Given date info return the value of current date """

        # this means current investment is still in use
        if self.end_date is not None:
            if self.is_free(current_date):

                stock_info = load_stock_info(current_date, self.stock_ticker, price_path=self.price_path)
                sell_price = stock_info.ix[stock_info.first_valid_index(), self.sell_stock_type]

                # the final amount is calculated used return rate
                self.amount = self.amount * sell_price * (1 - self.transaction_cost) / self.buy_price

                # Clear unused data
                self.end_date = None

                amount = self.amount

            else:
                # based on the stock type to load target data
                stock_info = load_stock_info(current_date, self.stock_ticker, price_path=self.price_path)

                # this means no trading on target date, use previous data
                if stock_info.empty:
                    current_price = self.previous_price
                else:
                    current_price = stock_info.loc[stock_info.first_valid_index(), self.stock_price_type]
                    self.previous_price = current_price

                amount = self.amount * current_price / self.buy_price

        else:
            amount = self.amount

        return amount

    def short_stock(self, buy_date, end_date, stock_ticker, buy_stock_type, sell_stock_type):
        """ use this investment account to buy some stock """
        self.end_date = end_date
        stock_info = load_stock_info(buy_date, stock_ticker, price_path=self.price_path)
        # print buy_stock_type
        # print stock_info
        self.buy_price = stock_info.ix[stock_info.first_valid_index(), buy_stock_type]
        self.sell_stock_type = sell_stock_type
        self.stock_ticker = stock_ticker
        self.previous_price = self.buy_price
        self.amount *= (1 - self.transaction_cost)


class AveragePortfolio(Constant):
    def __init__(self, root_path, total_num=10, total_value=10000., transaction_cost=0, price_type=const.STOCK_ADJPRCWD,
                 account_class=Investment, stock_price_path=None):

        self.init_path(root_path)
        self.free_amount = total_value
        self.free_account_num = total_num
        self.account_list = []
        self.wealth_stock_type = price_type
        self.transaction_cost = transaction_cost
        self.account_class = account_class
        self.stock_price_path = self.STOCK_DATA_PATH if stock_price_path is None else stock_price_path

    def short_stocks(self, buy_date, end_date, stock_ticker, buy_stock_type, sell_stock_type):
        """ If there is a free account, buy target stock, else do nothing """
        if self.free_account_num == 0:
            return

        buy_amount = float(self.free_amount) / self.free_account_num
        self.free_amount -= buy_amount
        account = self.account_class(amount=buy_amount, root_path=self.ROOT_PATH,
                                     stock_price_type=self.wealth_stock_type,
                                     price_path=self.stock_price_path,
                                     transaction_cost=self.transaction_cost)
        account.short_stock(buy_date, end_date, stock_ticker, buy_stock_type, sell_stock_type)
        self.account_list.append(account)
        self.free_account_num -= 1

    def get_current_values(self, current_date):
        """ get current investment value """
        amount = self.free_amount
        new_amount_list = []

        for account in self.account_list:
            amount += account.get_current_value(current_date)
            if account.is_free(current_date):
                self.free_amount += account.get_current_value(current_date)
                self.free_account_num += 1

            else:
                new_amount_list.append(account)

        self.account_list = new_amount_list

        return amount


class AccountHedge399300(Constant):
    """ This class is each investment account info """

    def __init__(self, amount, root_path, stock_price_type=None, transaction_cost=0., price_path=None):
        self.init_path(root_path=root_path)
        self.amount = amount

        # stock price of previous day
        self.previous_price = None

        # this parameter are used to determine which price are used to calculate the final result
        self.stock_price_type = self.STOCK_CLOSE_PRICE if stock_price_type is None else stock_price_type

        self.transaction_cost = transaction_cost
        self.price_path = price_path

        # end date use to mark the end date of one investment, if this variable is None means that current account is
        # free.
        self.end_date = None

        # ticker of trade stock
        self.stock_ticker = None
        self.sell_stock_type = None
        self.buy_price = None
        self.hedge_price = None

    def is_free(self, current_date):
        """ Whether this investment account has free money """
        return self.end_date is None or current_date >= self.end_date

    def get_current_value(self, current_date):
        """ Given date info return the value of current date """

        # this means current investment is still in use
        if self.end_date is not None:
            if self.is_free(current_date):

                stock_info = load_stock_info(current_date, self.stock_ticker, price_path=self.price_path)
                sell_price = stock_info.ix[stock_info.first_valid_index(), self.sell_stock_type]
                current_hedge_price = self.load_hedge_price(price_type=self.sell_stock_type,
                                                            current_date=current_date)

                # the final amount is calculated used return rate
                self.amount *= (sell_price * (1 - self.transaction_cost) / self.buy_price -
                                current_hedge_price / self.hedge_price + 1)

                # Clear unused data
                self.end_date = None

                amount = self.amount

            else:
                # based on the stock type to load target data
                stock_info = load_stock_info(current_date, self.stock_ticker, price_path=self.price_path)

                # this means no trading on target date, use previous data
                if stock_info.empty:
                    current_price = self.previous_price
                else:
                    current_price = stock_info.loc[stock_info.first_valid_index(), self.stock_price_type]
                    self.previous_price = current_price

                current_hedge_price = self.load_hedge_price(price_type=self.stock_price_type,
                                                            current_date=current_date)

                amount = self.amount * (current_price / self.buy_price - current_hedge_price / self.hedge_price + 1)

        else:
            amount = self.amount

        return amount

    def short_stock(self, buy_date, end_date, stock_ticker, buy_stock_type, sell_stock_type):
        """ use this investment account to buy some stock """
        # print buy_date, stock_ticker, self.price_path
        stock_info = load_stock_info(buy_date, stock_ticker, price_path=self.price_path)
        self.end_date = end_date
        self.stock_ticker = stock_ticker
        self.sell_stock_type = sell_stock_type
        self.amount *= (1 - self.transaction_cost)
        self.buy_price = stock_info.ix[stock_info.first_valid_index(), buy_stock_type]
        self.hedge_price = self.load_hedge_price(price_type=buy_stock_type, current_date=buy_date)
        self.previous_price = stock_info.ix[stock_info.first_valid_index(), self.stock_price_type]

    def load_hedge_price(self, price_type, current_date):
        index_df = pd.read_pickle(self.SZ_399300_PATH)

        index_df = index_df[index_df.index == current_date]

        if index_df.empty:
            return np.nan

        else:
            return index_df.ix[index_df.first_valid_index(), price_type]
