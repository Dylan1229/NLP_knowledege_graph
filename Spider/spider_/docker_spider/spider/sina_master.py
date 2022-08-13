import json
import multiprocessing
import re
import sys
import time

import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)

import requests
from redis import Redis
from spider import spider_util
from requests import HTTPError

_conn = Redis(host='172.16.124.239', port=6379, db=0)

"""
master端爬虫爬取url列表
"""
def master_requests():
    url = r'https://app.finance.sina.com.cn/news/tianyi/index?'

    header_str = """
User-Agent: sinafinance__4.23.0.1__android__37de17d5a77b40f3__7.1.2__HUAWEI+LIO-AN00
Host: app.finance.sina.com.cn
Connection: Keep-Alive
Accept-Encoding: gzip
    """

    # 生成header字典
    header_dic = spider_util.parse_fidder(header_str)

    param_str = """
action: 0
up: 0
down: 0
tm: 
did: 37de17d5a77b40f3
column: news_focus
device_id_old: 92f54cae185c6389
device_id_fake: b9393627e6cd5a7d
device_id_spns: 92f54cae185c6389
uid: 
pdps_params: {"app":{"version":"4.23.0.1","timestamp":"1605696533265","osv":"7.1.2","os":"Android","size":["900*1600"],"device_type":"4","connection_type":"2","ip":"192.168.43.155","make":"HUAWEI","device_id":"7A2FFD2DC3EF7BB58A81A35860DECF86","did":"37de17d5a77b40f3","device_id_new":"351564670432137","model":"LIO-AN00","carrier":"WiFi","name":"cn.com.sina.finance"}}
net_type: 2
type: finance
deviceid: 37de17d5a77b40f3
imei: 351564670432137
wm: b122
from: 7049995012
chwm: 32010_0001
version: 4.23.0.1
    """

    # 生成params
    param_dic = spider_util.parse_fidder(param_str)

    # 是否是第一次请求数据
    first_value = 0

    # 一直请求新的url
    while (True):

        # 第一次请求时
        if first_value == 0:
            first_value = 1
            print('当前页数: ' + param_dic['up'])
        else:
            # 上滑请求
            param_dic['action'] = str(1)
            param_dic['up'] = str(int(param_dic['up']) + 1)
            print('当前页数: ' + param_dic['up'])

        master_request(header_dic, param_dic, url)


"""
master端爬取一页的url列表
"""
def master_request(header_dic, param_dic, url):
    try:
        response = requests.get(url, headers=header_dic, params=param_dic)
        if response.status_code == 200:

            # 获取master页面返回信息
            texts = response.text
            print(texts)
            if not texts:
                print("已爬取完所有url!!!")
                sys.exit(0)

            # 获取详情页的url列表
            detail_urls = []
            if texts != '':
                detail_urls = spider_util.parse_urls(texts)
                # print(detail_urls)

                # 将url加入redis数据库
                for detail_url in detail_urls:
                    # url_backup用于备份，存储全量的url链接
                    if _conn.sadd('urls_backup', detail_url) != 1:
                        print('数据还没有更新，暂无新数据可爬取')
                    else:
                        # urls库用于分给slaver爬取
                        _conn.sadd('urls', detail_url)
    except HTTPError as e:
        print(e.read().decode('utf-8'))


def main():
    # master爬虫爬取url列表
    master_requests()


if __name__ == '__main__':
    start = time.time()

    main()
    # print(_conn.scard('urls_backup'))

    end = time.time()
    print("花费时间为：" + str(end - start))
