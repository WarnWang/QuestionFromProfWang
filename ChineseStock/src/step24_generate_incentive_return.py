#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Filename: step24_generate_incentive_return
# @Date: 2017-02-24
# @Author: Mark Wang
# @Email: wangyouan@gmial.com

if __name__ == '__main__':
    import os
    import sys
    import logging
    import datetime

    from xvfbwrapper import Xvfb

    from constants.path_info import Path
    from calculate_return_utils.calculate_return_utils_20170219 import CalculateReturnUtils20170219
    from report_generator.report_generator_add_alpha_hedge import ReportGeneratorAlphaHedge

    logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                        format='%(asctime)-15s %(name)s %(levelname)-8s: %(message)s')

    transaction_cost = 0.002
    suffix = 'stock_incentives'
    report_path = os.path.join(Path.REPORT_DATA_PATH, 'report_data_20170224', 'incentives_report')

    vdisplay = Xvfb(width=1366, height=768)
    vdisplay.start()

    test_info = ReportGeneratorAlphaHedge(transaction_cost=transaction_cost, report_path=report_path,
                                          folder_suffix=suffix, trading_days_list_path=Path.TRADING_DAYS_20170216_PATH,
                                          stock_price_path=Path.STOCK_PRICE_20170214_PATH)

    test_info.INFO_TYPE_LIST = [test_info.ALL]

    for i in range(6):
        test_info.main_progress(calculate_class=CalculateReturnUtils20170219, stop_loss_rate=i)

    result_path = os.path.join(Path.RESULT_PATH, suffix)
    test_info.generate_histogram_from_result_path(result_path)
    test_info.find_best_period_between_target_period(result_path=result_path,
                                                     end_date=datetime.datetime(2016, 7, 20),
                                                     start_date=datetime.datetime(2013, 7, 22))
    test_info.find_best_period_between_target_period(result_path=result_path,
                                                     end_date=datetime.datetime(2016, 7, 20),
                                                     start_date=datetime.datetime(2013, 7, 22)
                                                     )
    test_info.find_best_period_between_target_period(result_path=result_path,
                                                     end_date=datetime.datetime(2014, 12, 31),
                                                     start_date=datetime.datetime(2009, 1, 1),
                                                     )
    test_info.find_best_period_between_target_period(result_path=result_path,
                                                     end_date=None,
                                                     start_date=datetime.datetime(2016, 2, 1)
                                                     )
    vdisplay.stop()
