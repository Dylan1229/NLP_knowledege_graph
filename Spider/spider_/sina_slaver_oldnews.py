# 2002-2016年用（urls2006, urls2007, urls2015)

import json
import multiprocessing
import random
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
from pymongo import MongoClient
from spider import setting
from bs4 import BeautifulSoup

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
header_dic = spider_util.parse_fidder(setting.HEADER_STR)
header_dic['user-agent'] = random.choice(setting.USER_AGENT_LIST)

"""
slaver端爬虫爬取新闻详细
"""
def slaver_requests():
    # 从redis中随机取出一个元素并删除该元素
    url = _conn.spop(setting.URLS_COL)

    if url is None:
        return

    trytimes = 10  # 请求重试的次数
    for i in range(trytimes):

        try:
            response = requests.get(url, headers=header_dic, timeout=3)
            if response.status_code == 200:

                # 获取详细信息
                return response.content

            else:
                print("html错误码：" + str(response.status_code))

        except:
            print(url.decode('utf-8') + " 重试次数：" + str(i + 1))

    # 在redis中记录超时的日期信息
    _conn.sadd(setting.FAILURE_TABLE, url)


"""
筛选爬取的网页详细内容
"""
def parse_html(html):

    html = html.decode('gb2312', errors='ignore')

    soup = BeautifulSoup(html, 'html.parser')

    title, media, column, content, createdatetime = '', '', '财经', '', ''

    titles = soup.select('#artibodyTitle h1')
    medias = soup.select('#artibodyTitle .from_info a')
    contents = soup.select('#artibody')
    from_infos = soup.select('#artibodyTitle .from_info')
    link_reds = soup.select('#artibodyTitle .from_info .linkRed02')

    if titles:
        title = titles[0].text
    if medias:
        media = medias[0].text
    if contents:
        content = contents[0].text
    if from_infos and link_reds:
        createdatetime = from_infos[0].text.replace('<span class="linkRed02">', '').replace('</span>', '').replace(link_reds[0].text, '')
        createdatetime = createdatetime.replace('http://www.sina.com.cn ', '').replace('&nbsp;', '')

    if not content:
        return {}

    # 存到mongoDB的数据
    mongo_data = {'title': title,
                  'keywords': '',
                  'url': '',
                  'media': media,
                  'hot_words': '',
                  'column': column,
                  'content': content,
                  'createdatetime': createdatetime}

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
