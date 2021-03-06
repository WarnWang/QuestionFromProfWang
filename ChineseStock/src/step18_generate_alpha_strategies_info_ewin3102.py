#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Filename: step18_generate_alpha_strategies_info_ewin3102
# @Date: 2017-02-16
# @Author: Mark Wang
# @Email: wangyouan@gmial.com


import datetime
import os

import pandas as pd
import pathos

from calculate_return_utils.calculate_return_utils_20170117_data import generate_result_statistics
from constants.path_info import temp_path, result_path
from util_functions.os_related import get_process_num, make_dirs
from util_functions.util_function import print_info, get_max_draw_down, plot_multiline, get_annualized_return, \
    get_sharpe_ratio
from constants import portfolio_num_range, holding_days_list, Constant

const = Constant()


def merge_result(result_path):
    file_list = os.listdir(result_path)

    df = pd.DataFrame()

    for file_name in file_list:
        if not file_name.endswith('.p') or 'alpha' in file_name:
            continue

        column_name = file_name[:-2]
        df[column_name] = pd.read_pickle(os.path.join(result_path, file_name))

    return df


def merge_alpha_strategy_result(result_path):
    file_list = os.listdir(result_path)

    df = pd.DataFrame()

    for file_name in file_list:
        if not file_name.endswith('.p') or 'alpha' not in file_name:
            continue

        column_name = '_'.join(file_name.split('_')[:-1])
        df[column_name] = pd.read_pickle(os.path.join(result_path, file_name))

    return df


def based_on_sr_rate_generate_result(stop_loss_rate, folder_suffix, transaction_cost, report_path, calculate_class):
    process_num = get_process_num()

    transaction_cost_str = str(int(round(1000 * transaction_cost)))

    wealth_path = os.path.join(temp_path, folder_suffix,
                               'cost_{}_sr_{}_wealth'.format(transaction_cost_str, stop_loss_rate))

    save_path = os.path.join(result_path, folder_suffix, 'cost_{}_sr_{}'.format(transaction_cost_str,
                                                                                stop_loss_rate))
    report_return_path = os.path.join(temp_path, folder_suffix,
                                      'cost_{}_sr_{}_report'.format(transaction_cost_str, stop_loss_rate))
    picture_save_path = os.path.join(save_path, 'picture')
    better_picture_save_path = os.path.join(save_path, 'picture_1_5')
    best_picture_save_path = os.path.join(save_path, 'picture_2')

    make_dirs(
        [wealth_path, save_path, report_return_path, picture_save_path, better_picture_save_path,
         best_picture_save_path])

    # define some parameters
    portfolio_info = []
    for portfolio_num in portfolio_num_range:
        for holding_days in holding_days_list:
            portfolio_info.append({const.PORTFOLIO_NUM: portfolio_num, const.HOLDING_DAYS: holding_days,
                                   const.TRANSACTION_COST: transaction_cost,
                                   const.REPORT_RETURN_PATH: report_return_path,
                                   const.WEALTH_DATA_PATH: wealth_path,
                                   const.STOPLOSS_RATE: -float(stop_loss_rate) / 100,
                                   const.REPORT_PATH: report_path})

    calculator = calculate_class()

    # pool = multiprocessing.Pool(process_num)
    pool = pathos.multiprocessing.ProcessingPool(process_num)
    for info_type in [const.ALL]:
        print_info('info type: {}'.format(info_type))

        def change_info_type(x):
            x[const.INFO_TYPE] = info_type
            return x

        new_portfolio_info = map(change_info_type, portfolio_info)

        pool.map(calculator.calculate_return_and_wealth, new_portfolio_info)
        print_info('info type {} processed finished'.format(info_type))

    print_info('all info type processed finished, start generate result')
    wealth_result = merge_result(wealth_path)
    alpha_strategy_result = merge_alpha_strategy_result(wealth_path)
    today_str = datetime.datetime.today().strftime('%Y%m%d')
    wealth_result.to_pickle(os.path.join(save_path,
                                         '{}_{}sr.p'.format(today_str, stop_loss_rate)))
    wealth_result.to_csv(os.path.join(save_path,
                                      '{}_{}sr.csv'.format(today_str, stop_loss_rate)))
    alpha_strategy_result.to_pickle(os.path.join(save_path,
                                                 '{}_{}sr_alpha.p'.format(today_str, stop_loss_rate)))
    alpha_strategy_result.to_csv(os.path.join(save_path,
                                              '{}_{}sr_alpha.csv'.format(today_str, stop_loss_rate)))

    statistic_df, best_strategy_df, sharpe_ratio, ann_return = generate_result_statistics(wealth_result)
    statistic_df.to_pickle(os.path.join(save_path, '{}_statistic_{}.p'.format(today_str, stop_loss_rate)))
    best_strategy_df.to_pickle(os.path.join(save_path, '{}_best_strategies_{}.p'.format(today_str, stop_loss_rate)))
    statistic_df.to_csv(os.path.join(save_path, '{}_statistic_{}.csv'.format(today_str, stop_loss_rate)))
    best_strategy_df.to_csv(os.path.join(save_path, '{}_best_strategies_{}.csv'.format(today_str, stop_loss_rate)))

    data_list = [wealth_result, wealth_result[wealth_result.index < datetime.datetime(2015, 1, 1)],
                 wealth_result[wealth_result.index > datetime.datetime(2015, 1, 1)]]

    time_period = ['all', 'before_2015', 'after_2015']

    labels = ['Raw Strategy', 'Beta Strategy', 'Beta Strategy']
    line1 = 'Transaction cost 0.2% SR {}%'.format(stop_loss_rate)

    for method in wealth_result.keys():
        if sharpe_ratio[method] > 2:
            pic_path = best_picture_save_path
        elif sharpe_ratio[method] > 1.5:
            pic_path = better_picture_save_path
        else:
            pic_path = picture_save_path
        plot_data_list = [wealth_result[method], alpha_strategy_result[method],
                          wealth_result[method] - alpha_strategy_result[method]]

        info_list = [line1]

        for i, i_wealth in enumerate(data_list):
            sharpe_ratio = get_sharpe_ratio(i_wealth[method], df_type=const.WEALTH_DATAFRAME)
            ann_return = get_annualized_return(i_wealth[method], df_type=const.WEALTH_DATAFRAME)
            max_draw_down = get_max_draw_down(i_wealth[method])
            line = 'Data {}: Sharpe ratio {:.3f}, Annualized return {:.2f}%, Max drawdown rate {:.2f}%'.format(
                time_period[i], sharpe_ratio, ann_return, max_draw_down
            )
            info_list.append(line)

        text = '\n'.join(info_list)
        plot_multiline(plot_data_list, labels, method, os.path.join(pic_path, '{}.png'.format(method)), text)


if __name__ == '__main__':
    from ChineseStock.src.calculate_return_utils.calculate_return_utils_20170216 import CalculateReturnUtils20170216
    from ChineseStock.src.constants.path_info import Path

    transaction_cost = 0.002
    suffix = 'insider_stock_20170214_alpha_strategy_no_neglect_period'
    report_path = os.path.join(Path.REPORT_DATA_PATH, 'report_info_buy_only')

    if hasattr(os, 'uname'):

        from xvfbwrapper import Xvfb

        vdisplay = Xvfb(width=1366, height=768)
        vdisplay.start()

        for i in range(1, 4):
            print_info('SR is {}'.format(i))
            based_on_sr_rate_generate_result(i, suffix, transaction_cost=transaction_cost,
                                             report_path=report_path, calculate_class=CalculateReturnUtils20170216)

        vdisplay.stop()
