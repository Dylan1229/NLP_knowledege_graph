# 20021125 - 20070119

import json
import multiprocessing
import random
import re

import time
from lxml import etree
from bs4 import BeautifulSoup

import requests
import sys

import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

from redis import Redis
from spider import spider_util
from requests import HTTPError
from spider import setting

# _conn = Redis(host='172.16.124.239', port=6379, db=0)
_conn = Redis(host=setting.REDIS_IP, port=setting.REDIS_PORT, db=setting.REDIS_DB)

# Randomly choose the IP proxy pool
ips = []
# Gain all the hash data from redis
ip_dict = _conn.hgetall(setting.IP_POOL_TABLE)
for ke in ip_dict.keys():
    ips.append(ke.decode('utf-8'))

# Generate header dictionary
# header_dic = spider_util.parse_fidder(setting.HEADER_STR)
# header_dic['user-agent'] = random.choice(setting.USER_AGENT_LIST)
header_dic = {}
header_dic['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'

# base url(pageid=153 and lid=2516 indicates financial news) collect data from 20071212 to 20161104 
base_url = "http://news.sina.com.cn/old1000/news1000_"

# Cauculate the total number of url
url_count = 0

'''
Spider url  
Set the way to process pool
'''
def request_sina(url):

    trytimes = 10  # The times of reconnection
    for i in range(trytimes):

        try:
            url1 = base_url + url
            print(url)
            # ip_agent = random.choice(ips)
            # response = requests.get(url1, headers=header_dic, proxies={"http": "http://{}".format(ip_agent)}, timeout=3)
            response = requests.get(url1, headers=header_dic, timeout=3)
            # response = requests.get(url1)
            if response.status_code == 200:
                return response.content

            if response.status_code == 404:
                return ""

        except:
            print(url + "reconnection times:" + str(i + 1))

    # Log timed out date information in redis
    _conn.sadd(setting.MORETIME_TABLE, url1)

"""
Filter the details of crawled web pages
"""
def parse_result(html):

    if html is None or html == '':
        return []

    html = html.decode('gb2312', errors='ignore')

    if "[财经]" not in html:
        return []

    s = r'<li>.*?<a href="*http://finance.sina.com.cn/(.*?).shtml'

    pattern = re.compile(s, re.S)

    items = re.findall(pattern, html)

    for idx, item_url in enumerate(items):

        items[idx] = r"http://finance.sina.com.cn/" + item_url + ".shtml"

    return items


def write_item_to_redis(url_list):

    # Bulk insert into redis database
    if url_list:
        if _conn.sadd(setting.URLS_BKP_COL_old2006, *set(url_list)) == 0:
            print('数据还没有更新，暂无新数据可爬取')
        else:
            _conn.sadd(setting.URLS_COL_old2006, *set(url_list))

    # 将url加入redis数据库
    # for detail_url in url_list:
    #     # print(detail_url)
    #     # url_backup用于备份，存储全量的url链接
    #     if _conn.sadd(setting.URLS_BKP_COL_old2007, detail_url) != 1:
    #         print('数据还没有更新，暂无新数据可爬取')
    #     else:
    #         # urls库用于分给slaver爬取
    #         _conn.sadd(setting.URLS_COL_old2007, detail_url)

def main(url):
    # Initiate a crawler request
    html = request_sina(url)

    # Data filtering
    url_list = parse_result(html)

    # Write docs
    write_item_to_redis(url_list)

def get_url(url):
    return url


if __name__ == '__main__':

    start = time.time()

    # Initial total number of urls in database
    orignate_url = int(_conn.scard(setting.URLS_BKP_COL_old2006))

    urls = []

    # Introduce a process pool and create a corresponding process pool according to the number of cpu cores
    # The number of processes does not need to be greater than the number of cores
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    print("cpu核数为:" + str(multiprocessing.cpu_count()))

    # Get all dates from 20071212 to 20161104 in the format yyyy-mm-dd
    start_date = setting.START_DATE_3
    end_date = setting.END_DATE_3
    all_date1 = spider_util.get_date_list(start_date, end_date)

    if all_date1 is None:
        print("该日期范围内没有可查询的数据")
        sys.exit(0)

    # List inversion (reverse query, used for query error)
    if setting.NEED_REVERSE == "1":
        all_date1.reverse()

    for date_item in all_date1:
        date_item = date_item.replace("-", "")
        url = date_item + ".shtml"

        pool.apply_async(get_url, (url,), callback=main)

    # Execute our main function through the map method and pass the url we obtained
    # pool.map(main, urls)

    # Call the close() method of the thread pool so that it no longer creates processes
    pool.close()
    # Call the join() method to let the process of the process pool finish executing and then end
    pool.join()

    end = time.time()

    print("待爬取的url总件数为:" + str(url_count))
    print("去重存储成功的url总件数为:" + str(int(_conn.scard(setting.URLS_BKP_COL_old2006)) - orignate_url))
    print("花费时间为：" + str(end - start))




