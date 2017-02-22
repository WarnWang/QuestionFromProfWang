#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Filename: sz_suspension_resume_download
# @Date: 2017-02-22
# @Author: Mark Wang
# @Email: wangyouan@gmial.com

import re
import time
import datetime

import pandas as pd
from bs4 import BeautifulSoup

from sz_downloader import SZDownloader


class SZSuspensionResumeDownload(SZDownloader):
    def init_constant(self):
        self.SECURITY_NAME = 'security_name'
        self.SUSPENSION_DATE = 'suspension_date'
        self.RESUME_DATE = 'resume_date'
        self.SUSPENSION_DURATION = 'suspension_duration'
        self.result_dict = {self.TICKER: None,
                            self.SECURITY_NAME: None,
                            self.SUSPENSION_DATE: None,
                            self.RESUME_DATE: None,
                            self.SUSPENSION_DURATION: None,
                            self.REPORT_REASON: None}

        self.start_date = datetime.datetime(2005, 1, 4)
        self.end_date = datetime.datetime.today()

        self.post_dict = {'ACTIONID': 7,
                          'AJAX': 'AJAX-TRUE',
                          'CATALOGID': '1798',
                          'TABKEY': 'tab1',
                          'REPORT_ACTION': 'search',
                          'txtKsrq': '2005-01-08',
                          'txtZzrq': '2005-01-08', }

    def _download_report(self, start_date, end_date):
        self.logger.info('Download data from {} to {}'.format(start_date, end_date))

        result_list = []
        i_date = start_date
        failed_date_list = []

        while i_date <= end_date:
            self.logger.info('Start to download {} data info'.format(i_date))

            try:

                result_list.append(self._download_target_date_info(i_date))
                i_date += datetime.timedelta(days=1)

            except Exception, err:
                self.logger.warn('Download date {} failed as {}'.format(i_date, err))
                failed_date_list.append(i_date)

            finally:
                time.sleep(1)

        self.logger.info('Download finished')
        if failed_date_list:
            self.logger.warn('Target data download failed {}'.format(failed_date_list))

    def _download_target_date_info(self, target_date):
        post_dict = self.post_dict.copy()
        post_dict['txtZzrq'] = post_dict['txtKsrq'] = target_date.strftime('%Y-%m-%d')

        response = self.http_post(post_dict)
        soup = BeautifulSoup(response, 'lxml')

        if self.has_next_page(soup):
            result_list = [self._decode_page_info(soup)]
            next_button = soup.find('input', {"class": "cls-navigate-next", 'type': 'button'})
            digit_info = re.findall(r'\d+', next_button.get('onclick'))
            total_page = int(digit_info[-2])
            total_records = int(digit_info[-1])

            self.logger.debug('There are {} pages and {} records'.format(total_page, total_records))
            for i in range(1, total_page):
                post_dict = self.post_dict.copy()
                post_dict.update({'tab1PAGENUM': i,
                                  'tab1PAGECOUNT': total_page,
                                  'tab1RECORDCOUNT': total_records,
                                  'REPORT_ACTION': 'navigate', })

                result_list.append(self._decode_page_info(BeautifulSoup(self.http_post(post_dict), 'lxml')))

            return pd.concat(result_list, axis=0, ignore_index=True)

        else:
            return self._decode_page_info(soup)

    def _decode_page_info(self, soup):
        pass
