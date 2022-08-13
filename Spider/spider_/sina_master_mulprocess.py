# 2014-05-09 到 至今

import json
import multiprocessing
import random
import re
import time

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
header_dic = spider_util.parse_fidder(setting.HEADER_STR)
header_dic['user-agent'] = random.choice(setting.USER_AGENT_LIST)

# 基础url(pageid=153和lid=2516表明是财经类新闻)
base_url = "https://feed.mix.sina.com.cn/api/roll/get?pageid=153&lid=2516&k=&num=50"

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
            ip_agent = random.choice(ips)
            response = requests.get(url1, headers=header_dic, proxies={"http": "http://{}".format(ip_agent)}, timeout=3)
            if response.status_code == 200:
                return response.text

        except:

            print("重试次数：" + str(i + 1))


"""
筛选爬取的网页详细内容
"""
def parse_result(html):

    # 存储详细页的url
    url_list = []

    # 字符串加载为python字典
    dict_data = json.loads(html)

    if not isinstance(dict_data, dict):
        return dict_data + "is not dict"

    if "result" in dict_data.keys():
        result = dict_data['result']

        if "data" in result.keys():
            datas = result['data']

            if isinstance(datas, list):

                for item in datas:
                    if "url" in item.keys():
                        url_list.append(item["url"])

    return url_list


def write_item_to_redis(url_list):

    # 批量插入redis数据库
    if url_list:
        if _conn.sadd(setting.URLS_BKP_COL, *set(url_list)) == 0:
            print('数据还没有更新，暂无新数据可爬取')
        else:
            _conn.sadd(setting.URLS_COL, *set(url_list))

    # 将url加入redis数据库
    # for detail_url in url_list:
    #     # print(detail_url)
    #     # url_backup用于备份，存储全量的url链接
    #     if _conn.sadd(setting.URLS_BKP_COL, detail_url) != 1:
    #         print('数据还没有更新，暂无新数据可爬取')
    #     else:
    #         # urls库用于分给slaver爬取
    #         _conn.sadd(setting.URLS_COL, detail_url)

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
    orignate_url = int(_conn.scard(setting.URLS_BKP_COL))

    urls = []

    # 引入进程池，根据cpu的内核数量创建相应的进程池
    # 进程数不需要大于内核数，因为进程数创建的再多反而没什么好处
    pool = multiprocessing.Pool(multiprocessing.cpu_count())
    print("cpu核数为：" + str(multiprocessing.cpu_count()))

    # 获取从2014-05-09到当前日期的所有日期，格式为yyyy-mm-dd
    # start_date = '2014-05-09'
    start_date = setting.START_DATE
    # end_date = None
    end_date = setting.END_DATE
    all_date1 = spider_util.get_date_list(start_date, end_date)

    if all_date1 is None:
        print("该日期范围内没有可查询的数据")

    # 列表反转（反向查询，用于查询出错时）
    if setting.NEED_REVERSE == "1":
        all_date1.reverse()

    for date_item in all_date1:
        etime = spider_util.get_strptime(date_item)
        stime = spider_util.get_nextstrptime(date_item)
        ctime = spider_util.get_nextstrptime(date_item)
        url = '&etime=%s&stime=%s&ctime=%s&date=%s&page=' % (etime, stime, ctime, date_item)
        url = base_url + url

        trytimes = 10 # 请求重试的次数
        for i in range(trytimes):

            try:
                ip_agent = random.choice(ips)
                response = requests.get(url + "1", headers=header_dic, proxies={"http": "http://{}".format(ip_agent)}, timeout=3)

                # 运行提示远程主机强迫关闭了一个现有的连接。服务器当成了DDOS攻击，解决办法如下，设置timeout时间
                # response = requests.get(url + "1", headers=header_dic, timeout=(3, 7))
                if response.status_code == 200:

                    json_data = json.loads(response.text)
                    totalPage = spider_util.get_str_from_list(spider_util.get_value_from_json('total', json_data, []))
                    print(date_item + "  :  " + totalPage)
                    url_count += int(totalPage)

                    if totalPage != "" and totalPage != "0":

                        # 根据总条数，得到需要访问的页数
                        for j in range(1, int(totalPage)//50 + 2):
                            # urls.append("&etime=%s&stime=%s&ctime=%s&date=%s&page=%s" % (etime, stime, ctime, date_item, str(i)))
                            cur_url = "&etime=%s&stime=%s&ctime=%s&date=%s&page=%s" % (etime, stime, ctime, date_item, str(j))
                            pool.apply_async(get_url, (cur_url,), callback=main)

                    break

            # except HTTPError as e:
            #
            #     print(e.read().decode('utf-8'))

            except:

                print("重试次数：" + str(i + 1))

    print("待爬取的url总件数为：" + str(url_count))

    # 通过map方法执行我们的主函数，将我们获得的url传过去
    # pool.map(main, urls)

    # 调用线程池的close()方法，让它不再创建进程
    pool.close()
    # 调用join()方法，让进程池的进程执行完毕再结束
    pool.join()

    end = time.time()

    print("去重存储成功的url总件数为：" + str(int(_conn.scard(setting.URLS_BKP_COL)) - orignate_url))
    print("花费时间为：" + str(end - start))




