import re
import datetime,time
from datetime import timedelta

"""
将fiddler中复制的header或者webforms生成字典
"""
def parse_fidder(itemstr):
    item_dict = {}
    items = itemstr.split('\n')
    for item in items:
        key = item.split(':')[0].strip()
        if key:
            value = "".join(item.split(':')[1:]).strip()
            item_dict[key] = value

    return item_dict


"""
根据返回的文本提取urls
"""
def parse_urls(html):
    s = '"url":"(.*?)","comment_count".*?'

    pattern = re.compile(s, re.S)

    urls = re.findall(pattern, html)

    # 去除 esg广告，zt_d直播，hyt直播
    matchers = ['esg', 'zt_d', 'hyt']
    matching = [s for s in urls if not any(xs in s for xs in matchers)]
    matching2 = [re.sub(r'\\/', r'/', s) for s in matching]

    return matching2


"""
根据返回的文本提取urls
"""
def parse_urls2(html):
    s = '"link":"(.*?)","pic".*?'

    pattern = re.compile(s, re.S)

    urls = re.findall(pattern, html)

    # 去除 esg广告，zt_d直播，hyt直播
    matchers = ['esg', 'zt_d', 'hyt']
    matching = [s for s in urls if not any(xs in s for xs in matchers)]
    matching2 = [re.sub(r'\\/', r'/', s) for s in matching]

    return matching2

def get_value_from_json(key, tdict, tem_list):
    """
    从Json中获取key值，
    :param key:
    :param tdict:
    :param tem_list:
    :return:
    """
    if not isinstance(tdict, dict):
        return tdict + "is not dict"
    elif key in tdict.keys():
        tem_list.append(tdict[key])
    else:
        for value in tdict.values():
            if isinstance(value, dict):
                get_value_from_json(key, value, tem_list)
            elif isinstance(value, (list, tuple)):
                _get_value(key, value, tem_list)
    return tem_list


def _get_value(key, tdict, tem_list):
    """
    :param key:
    :param tdict:
    :param tem_list:
    :return:
    """
    for value in tdict:
        if isinstance(value, (list, tuple)):
            _get_value(tdict)
        elif isinstance(value, dict):
            get_value_from_json(key, value, tem_list)


def get_str_from_list(_list):
    str_list = str(_list).lstrip('[').lstrip('[').lstrip('[').lstrip('[').rstrip(']').rstrip(']').rstrip(']').rstrip(']')
    return str_list


"""--------------------------------------------------------
获取两个日期之间的所有日期，包括开始日期，结束日期
获取两个日期之间的所有月份，包括开始月份，结束月份
"""
def gen_dates(b_date, days):
    day = timedelta(days=1)
    # print(day)
    for i in range(days):
        # print(b_date + day*i)
        yield b_date + day*i

def get_date_list(start_date, end_date):
    """
    获取日期列表
    :param start: 开始日期
    :param end: 结束日期
    :return:
    """
    if start_date is not None:
        start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    if end_date is None:
        end = datetime.datetime.now()
    else:
        end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
    data = []
    for d in gen_dates(start, ((end-start).days + 1)):    # 29 + 1
        # print(d)   # datetime.datetime  类型
        data.append(d.strftime("%Y-%m-%d"))
    return data

def get_month_list(start_date, end_date):
    """
    获取月份列表
    :param start: 开始日期
    :param end: 结束日期
    :return:
    """
    dates = get_date_list(start_date, end_date)
    months = []
    for i in dates:
        if i[:7] not in months:
            months.append(i[:7])
    return months

def get_strptime(date):
    """
    获取指定日期的时间戳
    """
    return int(time.mktime(time.strptime(date, "%Y-%m-%d")))

def get_nextstrptime(date):
    """
    获取指定日期下一天的时间戳
    """

    day = timedelta(days=1)

    return get_strptime((datetime.datetime.strptime(date, "%Y-%m-%d") + day*1).strftime("%Y-%m-%d"))


"""-------------------------------------------------------------
"""
if __name__ == '__main__':
    ss = '2020-10-14'
    print(get_strptime(ss))
    print(get_nextstrptime(ss))