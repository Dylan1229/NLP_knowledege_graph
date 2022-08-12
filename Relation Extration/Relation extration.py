# coding:utf-8
'''
按行读取文章 并获取三元组
将三元组写入MongoDB中
author:you
'''

import time
import pymongo
import re
import os
import requests
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import urllib.parse
from pyltp import Segmentor, Postagger, Parser, NamedEntityRecognizer

#定义全局变量
print("正在连接MongoDB数据库......")
MONGO_DB_NAME = 'finance_data'  #数据库名称
MONGO_DB_COLLECTIONS = ['sina_test']   #数据库集合
#client = pymongo.MongoClient(host='127.0.0.1',port=27017,username='root', password='ustc406ljj', authSource='admin')
# db = client["ep"]
# collect = db['news']  #新闻内容
# collect_write = db['TE']  #新闻标题

client = pymongo.MongoClient('mongodb://192.168.1.103:27017/')  # 连接数据库
db = client[MONGO_DB_NAME]
    # print(mongo_newsdb)
dblist = client.list_database_names()
    # dblist = myclient.database_names()
collect = db['sina_test']  #新闻内容

print("正在加载LTP模型... ...")
MODELDIR = "ltp_data_v3.3.1/ltp_data"
segmentor = Segmentor()
segmentor.load(MODELDIR+"/cws.model")
print(MODELDIR+"/cws.model")
#segmentor.load_with_lexicon(os.path.join(MODELDIR, "cws.model"),os.path.join(MODELDIR, "Fina_dic.txt"))
segmentor.load_with_lexicon(MODELDIR+"/cws.model",MODELDIR + "/Fina_dic.txt")

postagger = Postagger()
postagger.load(MODELDIR+"/pos.model")
parser = Parser()
parser.load(MODELDIR+"/parser.model")
recognizer = NamedEntityRecognizer()
recognizer.load(MODELDIR+"/ner.model")





def fact_triple_extract(sentence):   #事实三元组抽取
    words = segmentor.segment(sentence)
    postags = postagger.postag(words)
    netags = recognizer.recognize(words, postags)
    arcs = parser.parse(words, postags)
    child_dict_list = build_parse_child_dict(words, postags, arcs)
    result = []
    for index in range(len(postags)):
        # 抽取以谓词为中心的事实三元组
        if postags[index] == 'v':
            child_dict = child_dict_list[index]
            # 主谓宾
            if 'SBV' in child_dict and 'VOB' in child_dict:
                e1 = complete_e(words, postags, child_dict_list, child_dict['SBV'][0])
                r = words[index]
                e2 = complete_e(words, postags, child_dict_list, child_dict['VOB'][0])
                flag = filter(e1, r, e2)
                if flag == True:
                    String = "(" + str(e1) + "," + str(r) + "," + str(e2) + ")"
                    result.append(String)
                    # return "("+str(e1)+","+str(r)+","+str(e2)+")"
                    # out_file.write("主语谓语宾语关系\t(%s, %s, %s)\n" % (e1, r, e2))
                    # out_file.flush()
            # 定语后置，动宾关系
            if arcs[index].relation == 'ATT':
                if 'VOB' in child_dict:
                    e1 = complete_e(words, postags, child_dict_list, arcs[index].head - 1)
                    r = words[index]
                    e2 = complete_e(words, postags, child_dict_list, child_dict['VOB'][0])
                    temp_string = r + e2
                    if temp_string == e1[:len(temp_string)]:
                        e1 = e1[len(temp_string):]
                    if temp_string not in e1:
                        flag = filter(e1, r, e2)
                        if flag == True:
                            String = "(" + str(e1) + "," + str(r) + "," + str(e2) + ")"
                            result.append(String)
                            # out_file.write("定语后置动宾关系\t(%s, %s, %s)\n" % (e1, r, e2))
                            # out_file.flush()
            # 含有介宾关系的主谓动补关系
            if 'SBV' in child_dict and 'CMP' in child_dict:
                # e1 = words[child_dict['SBV'][0]]
                e1 = complete_e(words, postags, child_dict_list, child_dict['SBV'][0])
                cmp_index = child_dict['CMP'][0]
                r = words[index] + words[cmp_index]
                if 'POB' in (child_dict_list[cmp_index]):
                    e2 = complete_e(words, postags, child_dict_list, child_dict_list[cmp_index]['POB'][0])
                    flag = filter(e1, r, e2)
                    if flag == True:
                        String = "(" + str(e1) + "," + str(r) + "," + str(e2) + ")"
                        result.append(String)
                        # return "(" + str(e1) + "," + str(r) + "," + str(e2) + ")"
                        # out_file.write("介宾关系主谓动补\t(%s, %s, %s)\n" % (e1, r, e2))
                        # out_file.flush()

        # 尝试抽取命名实体有关的三元组
        if netags[index][0] == 'S' or netags[index][0] == 'B':
            ni = index
            if netags[ni][0] == 'B':
                while netags[ni][0] != 'E':
                    ni += 1
                e1 = ''.join(words[index:ni + 1])
            else:
                e1 = words[ni]
            if arcs[ni].relation == 'ATT' and postags[arcs[ni].head - 1] == 'n' and netags[arcs[ni].head - 1] == 'O':
                r = complete_e(words, postags, child_dict_list, arcs[ni].head - 1)
                if e1 in r:
                    r = r[(r.index(e1) + len(e1)):]
                if arcs[arcs[ni].head - 1].relation == 'ATT' and netags[arcs[arcs[ni].head - 1].head - 1] != 'O':
                    e2 = complete_e(words, postags, child_dict_list, arcs[arcs[ni].head - 1].head - 1)
                    mi = arcs[arcs[ni].head - 1].head - 1
                    li = mi
                    if netags[mi][0] == 'B':
                        while netags[mi][0] != 'E':
                            mi += 1
                        e = ''.join(words[li + 1:mi + 1])
                        e2 += e
                    if r in e2:
                        e2 = e2[(e2.index(r) + len(r)):]
                    if r + e2 in sentence:
                        String = "(" + str(e1) + "," + str(r) + "," + str(e2) + ")"
                        result.append(String)
                        # return "(" + str(e1) + "," + str(r) + "," + str(e2) + ")"
                        # out_file.write("人名//地名//机构\t(%s, %s, %s)\n" % (e1, r, e2))
                        # out_file.flush()
    return result












def build_parse_child_dict(words, postags, arcs):
    '''
    为句子中的每个词语维护一个保存句法依存儿子节点的字典
    '''
    child_dict_list = []
    for index in range(len(words)):
        child_dict={}
        for arc_index in range(len(arcs)):
            if arcs[arc_index].head == index + 1:
                if arcs[arc_index].relation in child_dict:
                    child_dict[arcs[arc_index].relation].append(arc_index)
                else:
                    child_dict[arcs[arc_index].relation] = []
                    child_dict[arcs[arc_index].relation].append(arc_index)
        child_dict_list.append(child_dict)
    return child_dict_list








def complete_e(words, postags, child_dict_list, word_index):
    '''
    完善识别的部分实体
    '''
    child_dict = child_dict_list[word_index]
    prefix = ''
    if 'ATT' in child_dict:
        for i in range(len(child_dict['ATT'])):
            prefix += complete_e(words, postags, child_dict_list, child_dict['ATT'][i])

    postfix = ''
    if postags[word_index] == 'v':
        if 'VOB' in child_dict:
            postfix += complete_e(words, postags, child_dict_list, child_dict['VOB'][0])
        if 'SBV' in child_dict:
            prefix = complete_e(words, postags, child_dict_list, child_dict['SBV'][0]) + prefix

    return prefix + words[word_index] + postfix









def filter(e1,r,e2):
    verb = "觉得，认为，提到，希望，报道，称，感觉，感到，强调，指出，说，声称，透露，告诉，看，听说,表示，阐述,入,表达，深表，出于"
    pronoun = "我，我们，你，你们，它，它们，他，他们，她，她们，咱们，这，那，这些，那些，有人，之后，您，自己，他人，这边，那边" \
              "这样，那样，本人，一，二，三，四，五，六，七，八，九，十，其中，这其中,时,双方，此次，上述，此前，之前，此举，前者，后者" \
              "之间，两人，两个,两国,同时，若，如果，假如，谁，许多人，一群人，一种，两种，三种，另一种，一方面，另一方面，下一步，" \
              "1,2,3，4,5,6,7,8,9,0，各地，当地，中,上面,大家，下面，以下，以后，有的，家中，屋里，内部，外部，整体，局部，该，其" \
              "这种，那种，昨天，今天，明天，后天，诸多，哪里，各个，一切，还有，部分"
    if(len(e1)==1): return False
    if(len(e2)==1): return False
    if('该' in e1):return False
    if('该' in e2): return False
    e1_list = segmentor.segment(e1)
    e2_list = segmentor.segment(e2)
    for index in range(len(e1_list)):
        if(e1_list[index] in pronoun):
            return False
    for index in range(len(e2_list)):
        if(e2_list[index] in pronoun):
            return False
    if(r in verb):
        return False
    strs = str(e1)+str(r)+str(e2)
    return getNumber(strs)
    # return True










def getNumber(words):
    headers = {"headers": UserAgent().random}
    data = urllib.parse.quote(words)
    url = "http://www.baidu.com/baidu?cl=3&tn=baidutop10&wd="+str(data)
    time.sleep(0.1)
    r = requests.get(url,headers=headers)
    s = BeautifulSoup(r.text, 'html.parser')
    num = s.find('div', {'class': 'nums'})
    pattern = re.compile(r'[0-9]')
    num = pattern.findall(str(num))
    if(len(num)>0):
        result = int("".join(num))
    else: result=0
    print(result)
    if(result>=10000):
        return True
    else: return False








def strQ2B(ustring):
    '''
    :param ustring:
    :全角字符转换为半角字符
    '''
    rstring = ""
    for uchar in ustring:
        inside_code=ord(uchar)
        if inside_code == 12288:
            inside_code = 32
        elif (inside_code >= 65281 and inside_code <= 65374):
            inside_code -= 65248
        rstring += chr(inside_code)
    return rstring











def ariticle():
    
    #将文章按行分隔 并按行提取关系
    #id = 0

    articles = list(collect.find({},{'abstract_3': 1}).limit(2000))
    cnt = 1
    count = len(articles)
    for article_ in articles:
        Arraycontent = article_['abstract_3']
        for content in Arraycontent:
            if len(content)>0:
                content = strQ2B(content)
                content = content.split("\n")
                content = "".join(content)
                content = re.sub('([。！？\?])([^”’])', r"\1\n\2", content)  # 单字符断句符
                content = re.sub('(\.{6})([^”’])', r"\1\n\2", content)  # 英文省略号
                content = re.sub('(\…{2})([^”’])', r"\1\n\2", content)  # 中文省略号
                content = re.sub('([。！？\?][”’])([^，。！？\?])', r'\1\n\2', content)  # 考虑。”
                content = re.sub(':', r',', content)
                content = content.rstrip()  # 段尾如果有多余的\n就去掉它
                lines = content.split("\n")
                triple = []
                for line in lines:
                    if ("责任编辑") in line: continue
                    if ("原标题") in line: continue
                    if ("记者") in line: continue
                    tri = fact_triple_extract(line)
                    if(len(tri)):
                        for index in range(len(tri)):
                            triple.append(tri[index])
                    #调用提取三元组的公式即可
                #id = id + 1
               # print(id)
                print(triple)


                # print("一篇文章结束")
                collect.update_one({'_id': article_['_id'] }, {'$set': {
                    'triple': triple
                }}, upsert=False)
                #collect_write.update_one({'id':id},{'$set':{'baidu_triple':triple}})
        print("已经处理了"+str(cnt)+" 条数据，还剩下"+str(count-cnt)+"条")
        cnt+=1
        print("id为" + str(article_['_id']) + "的新闻处理完毕")


'''


def ariticle():
    content ='''"复星医药曲线进入美国市场9月18日，上海复星医药（集团）股份有限公司（下称复星医药，600196.sh/2196.hk）公告称，拟出资不超过10.91亿美元收购印度药企glandpharma约74%的股权，其中包括收购方将依据依诺肝素在美国上市销售所支付的不超过2500万美元的或有对价。"
"此前复星医药方面对第一财经记者透露，收购glandpharma，复星医药可以借助其生产线以及注册平台，从而扩大品牌在国际上的效应，以此协助复星医药进军包括美国在内的海外市场。"
"复星医药的这一股权收购比例相比较一年前下调了约12%：2016年7月，复星医药公告将收购印度药企glandpharma现有股东持有的79.997%的股权，同时认购标的公司发行的6.083%的可转换优先股。"'''
    content = strQ2B(content)
    content = content.split("\n")
    content = "".join(content)
    content = re.sub('([。！？\?])([^”’])', r"\1\n\2", content)  # 单字符断句符
    content = re.sub('(\.{6})([^”’])', r"\1\n\2", content)  # 英文省略号
    content = re.sub('(\…{2})([^”’])', r"\1\n\2", content)  # 中文省略号
    content = re.sub('([。！？\?][”’])([^，。！？\?])', r'\1\n\2', content)  # 考虑。”
    content = re.sub(':', r',', content)
    content = content.rstrip()  # 段尾如果有多余的\n就去掉它
    lines = content.split("\n")
    triple = []
    for line in lines:
        if ("责任编辑") in line: continue
        if ("原标题") in line: continue
        if ("记者") in line: continue
        tri = fact_triple_extract(line)
        if (len(tri)):
            for index in range(len(tri)):
                triple.append(tri[index])
                # 调用提取三元组的公式即可
                # id = id + 1
                # print(id)
    print(triple)
    print("一篇文章结束")
'''
if __name__ == '__main__':
    ariticle()

