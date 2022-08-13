#  20021125 - 20070119

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


# ip代理池随机选择
ips = []
# 获取redis中所有的hash数据
ip_dict = _conn.hgetall(setting.IP_POOL_TABLE)
for ke in ip_dict.keys():
    ips.append(ke.decode('utf-8'))


# 生成header字典
# 生成header字典
# header_dic = spider_util.parse_fidder(setting.HEADER_STR)
# header_dic['user-agent'] = random.choice(setting.USER_AGENT_LIST)
header_dic = {}
header_dic['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36'

# 基础url(pageid=153和lid=2516表明是财经类新闻) 收集从20071212 - 20161104 范围内的数据
base_url = "http://news.sina.com.cn/old1000/news1000_"

# 统计url总数量
url_count = 0

'''
爬取url  
加入进程池的方式
'''
def request_sina(url):

    trytimes = 10  # 请求重试的次数
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

            print(url + "重试次数：" + str(i + 1))

    # 在redis中记录超时的日期信息
    _conn.sadd(setting.MORETIME_TABLE, url1)

"""
筛选爬取的网页详细内容
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

    # 批量插入redis数据库
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
    # 发起爬虫请求
    html = request_sina(url)

    # 数据筛选
    url_list = parse_result(html)

    # 写文件
    write_item_to_redis(url_list)

def get_url(url):
    return url


if __name__ == '__main__':

    start = time.time()

    # 数据库初始url总量
    orignate_url = int(_conn.scard(setting.URLS_BKP_COL_old2006))

    urls = []

    # 引入进程池，根据cpu的内核数量创建相应的进程池
    # 进程数不需要大于内核数，因为进程数创建的再多反而没什么好处
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    print("cpu核数为：" + str(multiprocessing.cpu_count()))

    # 获取从20071212到20161104的所有日期，格式为yyyy-mm-dd
    start_date = setting.START_DATE_3
    end_date = setting.END_DATE_3
    all_date1 = spider_util.get_date_list(start_date, end_date)

    if all_date1 is None:
        print("该日期范围内没有可查询的数据")
        sys.exit(0)

    # 列表反转（反向查询，用于查询出错时）
    if setting.NEED_REVERSE == "1":
        all_date1.reverse()

    for date_item in all_date1:
        date_item = date_item.replace("-", "")
        url = date_item + ".shtml"

        pool.apply_async(get_url, (url,), callback=main)

    # 通过map方法执行我们的主函数，将我们获得的url传过去
    # pool.map(main, urls)

    # 调用线程池的close()方法，让它不再创建进程
    pool.close()
    # 调用join()方法，让进程池的进程执行完毕再结束
    pool.join()

    end = time.time()

    print("待爬取的url总件数为：" + str(url_count))
    print("去重存储成功的url总件数为：" + str(int(_conn.scard(setting.URLS_BKP_COL_old2006)) - orignate_url))
    print("花费时间为：" + str(end - start))




