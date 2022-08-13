import json
import multiprocessing
import re
import threading
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
from pymongo import MongoClient
from spider import setting
from concurrent.futures import ThreadPoolExecutor

_conn = Redis(host=setting.REDIS_IP, port=setting.REDIS_PORT, db=setting.REDIS_DB)

# mondb数据库连接
# _mongo_conn = MongoClient('mongodb://172.16.124.239:27017/')
# _mongo_conn = MongoClient('127.0.0.1', 27017)
_mongo_conn = MongoClient('mongodb://' + setting.MONGO_IP + ':' + setting.MONGO_PORT + '/')

# 取得finance_data数据库，不存在则会自行创建
db = _mongo_conn[setting.MONGO_DB]

# 取得sina集合（类似于表），没有则创建一个
sina_col = db[setting.MONGO_COL]

print(_mongo_conn.server_info())

# 生成header字典
header_dic = spider_util.parse_fidder(setting.HEADER_STR_SLAVER)

# 生成params
param_dic = spider_util.parse_fidder(setting.PARAM_STR_SLAVER)

# 基础url
url = "https://app.finance.sina.com.cn/toutiao/content?"

"""
slaver端爬虫爬取新闻详细
"""
def slaver_requests():
    # 从redis中随机取出一个元素并删除该元素
    param_url = _conn.spop(setting.URLS_COL)

    if param_url is None:
        return

    # 拼接url
    param_dic["url"] = param_url.decode('utf-8')

    trytimes = 10  # 请求重试的次数
    for i in range(trytimes):

        try:
            response = requests.get(url, headers=header_dic, params=param_dic, timeout=3)
            if response.status_code == 200:

                # 获取详细信息
                return response.text

            else:
                print("html错误码：" + str(response.status_code))

        except:
            print(param_dic["url"] + " 重试次数：" + str(i + 1))

    # 在redis中记录超时的日期信息
    _conn.sadd(setting.FAILURE_TABLE, param_dic["url"])


"""
筛选爬取的网页详细内容
"""
def parse_html(html):

    # 字符串加载为python字典
    dict_data = json.loads(html)

    if not spider_util.get_str_from_list(spider_util.get_value_from_json('content', dict_data, [])):
        return {}

    # 存到mongoDB的数据
    mongo_data = {'title': spider_util.get_str_from_list(spider_util.get_value_from_json('title', dict_data, [])),
                  'keywords': spider_util.get_str_from_list(spider_util.get_value_from_json('keywords', dict_data, [])),
                  'url': spider_util.get_str_from_list(spider_util.get_value_from_json('url', dict_data, [])),
                  'media': spider_util.get_str_from_list(spider_util.get_value_from_json('media', dict_data, [])),
                  'hot_words': spider_util.get_str_from_list(spider_util.get_value_from_json('hot_words', dict_data, [])),
                  'column': spider_util.get_str_from_list(spider_util.get_value_from_json('column', dict_data, [])),
                  'content': spider_util.get_str_from_list(spider_util.get_value_from_json('content', dict_data, [])),
                  'createdatetime': spider_util.get_str_from_list(spider_util.get_value_from_json('createdatetime', dict_data, []))}

    return mongo_data


"""
写数据到mongoDB
"""
def write_data_to_db(db_list):

    if db_list:
        sina_col.insert_many(db_list, ordered=False)

def main():

    # 保存批量待存入db数据
    db_list = []

    start_clear_time = time.time()

    while True:
        end_clear_time = time.time()
        # 批量插入数据（如果暂存的数据大于10000，或者时间大于5分钟，则批量插入数据）
        if len(db_list) > 100 or (end_clear_time - start_clear_time) > 300:

            print("查询" + str(len(db_list)) + "条所需时间：" + str(end_clear_time - start_clear_time))

            start_clear_time = time.time()

            # 写数据到mongoDB
            write_data_to_db(db_list)

            db_list.clear()

        # slaver爬虫爬取新闻详细信息
        html = slaver_requests()

        if html is None:
            continue

        # 数据筛选
        mongo_data = parse_html(html)

        if mongo_data:
            db_list.append(mongo_data)


if __name__ == '__main__':
    start = time.time()

    # with ThreadPoolExecutor(max_workers=5) as t:
    #     task1 = t.submit(main)
    #     task2 = t.submit(main)
    #     task3 = t.submit(main)
    #     task4 = t.submit(main)

    main()

    end = time.time()
    print("花费时间为：" + str(end - start))
