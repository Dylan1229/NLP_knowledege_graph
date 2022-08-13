import sys
import os
curPath = os.path.abspath(os.path.dirname(__file__))
rootPath = os.path.split(curPath)[0]
sys.path.append(rootPath)


# --------------redis配置（20161105以后）-----------------
"""存储详情页的url的redis设置"""
# REDIS_IP = '192.168.1.105'
REDIS_IP = '172.16.124.239'
# REDIS_IP = '192.168.43.52'
REDIS_PORT = 6379
REDIS_DB = 0

"""redis数据库中存储ip代理池的集合名"""
IP_POOL_TABLE = 'use_proxy'

"""存储url的集合名"""
URLS_COL = 'urls2007'

"""存储url备份的集合名(全量url)"""
URLS_BKP_COL = 'urls2007_backup'
# -------------------------------------------------------


# ----------redis配置（20071212-20161104）---------------

"""存储url的集合名"""
URLS_COL_old2007 = 'urls2007'

"""存储url备份的集合名(全量url)"""
URLS_BKP_COL_old2007 = 'urls2007_backup'

"""记录爬取超时10次以上的日期表"""
MORETIME_TABLE = 'more_time'

"""记录爬取详细页失败的url"""
FAILURE_TABLE = 'failure_url'
# -------------------------------------------------------


# ----------redis配置（19990526 - 20070119）---------------
"""存储url的集合名"""
URLS_COL_old2006 = 'urls2006'

"""存储url备份的集合名(全量url)"""
URLS_BKP_COL_old2006 = 'urls2006_backup'
# -------------------------------------------------------


# ----------------------mongoDB配置----------------------
MONGO_IP = '172.16.124.239'
MONGO_PORT = '27017'

"""存储新浪新闻详细页内容db和集合"""
MONGO_DB = 'finance_data'
MONGO_COL = 'sina_2007'
# -------------------------------------------------------


# --------------------查询日期范围设置--------------------
# 2014-05-09 到 至今
START_DATE_1 = '2007-12-12'
"""如果到当前日期，则设置为None即可"""
END_DATE_1 = '2016-11-04'

"""是否需要反转列表，1表示需要，0表示不需要"""
NEED_REVERSE = "0"
# -------------------------------------------------------


# --------------------查询日期范围设置--------------------
# 20070120 - 20071211
START_DATE_2 = '2007-01-20'
"""如果到当前日期，则设置为None即可"""
END_DATE_2 = '2007-12-11'

"""是否需要反转列表，1表示需要，0表示不需要"""
NEED_REVERSE = "0"
# -------------------------------------------------------


# --------------------查询日期范围设置--------------------
# 20021125 - 20070119
# START_DATE_3 = '2002-11-25'
START_DATE_3 = '2004-02-03'
"""如果到当前日期，则设置为None即可"""
END_DATE_3 = '2007-01-19'

"""是否需要反转列表，1表示需要，0表示不需要"""
NEED_REVERSE = "0"
# -------------------------------------------------------


# -------------------master端请求设置---------------------
"""请求头的用户代理"""
USER_AGENT_LIST = [
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.108 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.139 Safari/537.36'
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; 360SE)",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24"
]

"""请求头基本信息"""
HEADER_STR = """
Connection: Keep-Alive
Accept-Encoding: gzip, deflate, br
    """
# ---------------------------------------------------------


# ---------------------slaver端请求设置---------------------
HEADER_STR_SLAVER = """
Accept-Language: zh-cn
cache_control: no-cache
Pragma: no-cache
SN-REQID: 
User-Agent: sinafinance__4.23.0.1__android__37de17d5a77b40f3__7.1.2__HUAWEI+LIO-AN00
Host: app.finance.sina.com.cn
Connection: Keep-Alive
Accept-Encoding: gzip
    """

PARAM_STR_SLAVER = """
version: 4.23.0.1
app_key: 2399350321
format: json
column: news_focus
mode: raw
wapH5: y
url: http://finance.sina.com.cn/tech/2020-11-19/doc-iiznctke2248937.shtml
wm: b122
from: 7049995012
chwm: 32010_0001
imei: 351564670432137
zxtype: finance
filter: 1
type: 1
docid: 
    """
# ---------------------------------------------------------
