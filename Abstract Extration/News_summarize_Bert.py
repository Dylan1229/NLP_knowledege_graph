# -*- coding: utf-8 -*-
"""
Created on Sat Dec 26 21:34:30 2020

@author: 41291
"""

import pymongo
import numpy as np
import re
from bson import ObjectId


np.seterr(all='warn')
MONGO_DB_NAME = 'finance_data'  #数据库名称
MONGO_DB_COLLECTIONS = ['sina2017']   #数据库集合

LIMITED=1  #设置一次执行最多对多少条新闻进行摘要提取

def cut_sentences(sentence):    #划分句子并去除引号
    para=re.sub('\n', '', sentence)
    para=re.sub('\'', '', para)
    para=re.sub('\"', '', para)
    para=re.sub('“', '', para)
    para=re.sub('”', '', para)
    para=re.sub('“', '', para)
    para=re.sub('‘', '', para)
    para=re.sub('’', '', para)
    para=re.sub('([。！？])', r"\1\n", para)
    return para  


def summarizeText():       #摘要提取
    from summarizer import Summarizer
    mongo_client = pymongo.MongoClient('mongodb://172.16.124.239:27017/')  #连接数据库
    mongo_newsdb = mongo_client[MONGO_DB_NAME]
    #print(mongo_newsdb)
    dblist = mongo_client.list_database_names()
    # dblist = myclient.database_names() 
    
    if MONGO_DB_NAME in dblist:  
      print("数据库已存在！")
    cnt=1
    for coll_name in MONGO_DB_COLLECTIONS:
        print("--- Processing summarizeText collection '{}'".format(coll_name))
        mongo_coll = mongo_newsdb[coll_name]
        #articles = list(mongo_coll.find({
        #    "new_content_1":None}).limit(mongo_coll.estimated_document_count()))
        articles = list(mongo_coll.find({"abstract_3":None}).limit(LIMITED))   

        articles_count = len(articles)
        #print(articles_count)
        for article in articles:   
            body = article['new_content_1']
            body=cut_sentences(body)
            #print(body)
            model = Summarizer()
            result = model(body, ratio=0.2)  # Specified with ratio
            result = model(body, num_sentences=3)  # Will return 3 sentences 
            abstract=re.sub('([。！？]+)', r"\1\n", result)
           # print(abstract)
           # print("\n")
            mongo_coll.update_one({'_id': article['_id']}, {'$set': {
                'abstract_3': abstract
            }}, upsert=False)
            print("第"+str(article['_id'])+"条数据处理完毕\n")
            print("已处理"+str(cnt)+"条数据， 还剩下"+str(articles_count-cnt)+"条数据\n")
            cnt+=1
            
            
summarizeText()         
