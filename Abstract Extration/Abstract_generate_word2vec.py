# coding:utf-8
import pkuseg
import math
import numpy as np
import gensim
import pymongo
# import time
# import threading
import re
from heapq import nlargest
from itertools import product, count
import os
print(os.getcwd())
#seg = pkuseg.pkuseg(model_name="news", user_dict="buchong.txt")
seg = pkuseg.pkuseg(model_name="news", user_dict="default")
#model = gensim.models.Word2Vec.load('model_w2v/wiki_corpus-300.bin')
model = gensim.models.Word2Vec.load('wiki_corpus.bin')

np.seterr(all='warn')
MONGO_DB_NAME = 'finance_data'  #数据库名称
MONGO_DB_COLLECTIONS = ['sina2017']   #数据库集合

BATCH_SIZE = 10
THREADS = 25

LIMITED=10000  #设置一次执行最多对多少条新闻进行摘要提取
def cut_sentences(sentence):  # 划分句子
    para = re.sub('([。！？])([^”’])', r"\1\n\2", sentence)
    return para.split("\n")


# 句子中的stopwords
def create_stopwords():  # 中文常用停词表
    stop_list = [line.strip() for line in open("stopwords.txt", 'r', encoding='utf-8').readlines()]
    return stop_list


def create_graph(word_sent):
    """
    传入句子链表  返回句子之间相似度的图
    :param word_sent:
    :return:
    """
    num = len(word_sent)  # content中单词个数
    # 定义一个0矩阵board，大小为num*num，board中值为两个句子的相似度
    board = [[0.0 for _ in range(num)] for _ in range(num)]

    for i, j in product(range(num), repeat=2):
        if i != j:
            board[i][j] = compute_similarity_by_avg(word_sent[i], word_sent[j])
    return board


def cosine_similarity(vec1, vec2):
    '''
    计算两个向量之间的余弦相似度
    :param vec1:
    :param vec2:
    :return:
    '''
    tx = np.array(vec1)
    ty = np.array(vec2)
    cos1 = np.sum(tx * ty)
    cos21 = np.sqrt(sum(tx ** 2))
    cos22 = np.sqrt(sum(ty ** 2))
    cosine_value = cos1 / float(cos21 * cos22)
    return cosine_value


def seg_text_to_vector(sentence):
    '''
    对一个句子求词向量
    :param sentence:
    :return:
    '''
    vector = np.zeros(250)
    for word in sentence:
        try:
            a = model[word]
            for q in a:
                if np.isnan(q):
                    continue
        except:
            continue
        # 不分词语的权重
        vector += a
    return vector


def compute_similarity_by_avg(sents_1, sents_2):
    '''
    对两个句子求平均词向量
    :param sents_1:
    :param sents_2:
    :return:
    '''
    if len(sents_1) == 0 or len(sents_2) == 0:
        return 0.0
    vec1 = seg_text_to_vector(sents_1)
    vec2 = seg_text_to_vector(sents_2)

    similarity = cosine_similarity(vec1 / len(sents_1), vec2 / len(sents_2))
    return similarity


def calculate_score(weight_graph, scores, i):
    """
    计算句子在图中的分数
    :param weight_graph:
    :param scores:
    :param i:
    :return:
    """
    length = len(weight_graph)
    d = 0.85
    added_score = 0.0

    for j in range(length):
        fraction = 0.0
        denominator = 0.0
        # 计算分子
        fraction = weight_graph[j][i] * scores[j]
        # 计算分母
        for k in range(length):
            denominator += weight_graph[j][k]
            if denominator == 0:
                denominator = 1
        added_score += fraction / denominator
    # 算出最终的分数
    weighted_score = (1 - d) + d * added_score
    return weighted_score


def weight_sentences_rank(weight_graph):
    '''
    输入相似度的图（矩阵)
    返回各个句子的分数
    :param weight_graph:
    :return:
    '''
    # 初始分数设置为0.5
    scores = [0.5 for _ in range(len(weight_graph))]
    old_scores = [0.0 for _ in range(len(weight_graph))]

    # 开始迭代
    while different(scores, old_scores):
        for i in range(len(weight_graph)):
            old_scores[i] = scores[i]
        for i in range(len(weight_graph)):
            scores[i] = calculate_score(weight_graph, scores, i)
    return scores


def different(scores, old_scores):
    '''
    判断前后分数有无变化
    :param scores:
    :param old_scores:
    :return:
    '''
    flag = False
    for i in range(len(scores)):
        if math.fabs(scores[i] - old_scores[i]) >= 0.0001:
            flag = True
            break
    return flag


def filter_symbols(sents):  # 返回移除所有停词后的句子（content）
    stopwords = create_stopwords()  # 停词表
    _sents = []
    for sentence in sents:
        for word in sentence:
            if word in stopwords:
                sentence.remove(word)  # 移除停词
        if sentence:
            _sents.append(sentence)
    return _sents


def filter_model(sents):
    '''
    去掉模型中不存在的单词
    :param sents:
    :return:
    '''
    _sents = []
    for sentence in sents:
        for word in sentence:
            if word not in model:
                sentence.remove(word)
        if sentence:
            _sents.append(sentence)
    return _sents


def replaceNews(sentence):    #划分句子并去除引号
    para=re.sub('\n', '', sentence)
    para=re.sub('\'', '', para)
    para=re.sub('\"', '', para)
    para=re.sub('“', '', para)
    para=re.sub('”', '', para)
    para=re.sub('“', '', para)
    para=re.sub('‘', '', para)
    para=re.sub('’', '', para)
    para = re.sub('\s', '', para)
    #para=re.sub('([。！？])', r"\1\n", para)
    return para

def summarize(text, n):
    # tokens为一段话（已经用\n划分了）

    tokens = cut_sentences(text)  # 划分句子成列表（tokens为List)
    sentences = []  # 存储分句后的句子
    sents = []  # 存储分词后的词

    # jieba.load_userdict("buchong.txt")

    for sent in tokens:  # sent为一句话（String)
        lenth = len(sent)
        if(lenth == 0) :
            continue
        if sent[0] == '（' or sent[0] == '）' or sent[lenth - 1] == '）':  # 把括号去掉
            sent = sent.replace('（', '')
            sent = sent.replace('）', '')
        sentences.append(sent)  # sentences加上这句话   sentences为list<String>
        sents.append([word for word in seg.cut(sent) if word])
        # sents为一个句子分词（S、B）后 即List<String after seg.cut>
        # 此时得到所有句子的分词
        # sents.append([word for word in jieba.cut(sent) if word])

    sents = filter_symbols(sents)
    sents = filter_model(sents)
    graph = create_graph(sents)
    scores = weight_sentences_rank(graph)

    if n > len(scores):
        n = len(scores)

    sent_selected = nlargest(n, zip(scores, count()))
    sent_index = []

    for i in range(n):
        # print(sent_selected[i][1])
        sent_index.append(sent_selected[i][1])
    return [sentences[i] for i in sent_index]


'''
def main():
    mongo_client = pymongo.MongoClient('192.168.1.103', 27017)
    mongo_newsdb = mongo_client[MONGO_DB_NAME]

    for coll_name in MONGO_DB_COLLECTIONS:
        print("--- Processing collection '{}'".format(coll_name))
        mongo_coll = mongo_newsdb[coll_name]

        # for i in range(mongo_coll.estimated_document_count() // BATCH_SIZE + 1):
        #     articles = list(mongo_coll.find({'abstract': None}).skip(i * BATCH_SIZE).limit(BATCH_SIZE))
        #     articles_count = len(articles)
        #     if articles_count == 0:
        #         break
        #     threads = init_extract_threads(mongo_coll, articles, THREADS)
        #     for t in threads:
        #         t.start()
        #     tick = time.time()
        #     while len(articles) > 0:
        #         time.sleep(10)
        #         print("Batch {}: {}/{} articles processed in {} seconds"
        #               .format(i, articles_count - len(articles), articles_count, time.time() - tick))
        articles = list(mongo_coll.find({'abstract-3': None}).limit(mongo_coll.estimated_document_count()))
        articles_count = len(articles)

        # if articles_count == 0:
        #     break
        # threads = init_extract_threads(mongo_coll, articles, THREADS)
        # for t in threads:
        #     t.start()
        # tick = time.time()
        # time.sleep(10)
        # print(" {}/{} articles processed in {} seconds"
        #       .format(articles_count - len(articles), articles_count, time.time() - tick))
        for article in articles:
            text = article['new_content']
            abstract = summarize(text, 3)

            # print(abstract)
            mongo_coll.update_one({'_id': article['_id']}, {'$set': {
                'abstract-3': abstract
            }}, upsert=False)
'''



def main():
    mongo_client = pymongo.MongoClient('mongodb://192.168.1.103:27017/')  # 连接数据库
    mongo_newsdb = mongo_client[MONGO_DB_NAME]
    # print(mongo_newsdb)
    dblist = mongo_client.list_database_names()
    # dblist = myclient.database_names()

    if MONGO_DB_NAME in dblist:
        print("数据库已存在！")
    cnt = 1
    for coll_name in MONGO_DB_COLLECTIONS:
        print("--- Processing summarizeText collection '{}'".format(coll_name))
        mongo_coll = mongo_newsdb[coll_name]
        # articles = list(mongo_coll.find({
        #    "new_content_1":None}).limit(mongo_coll.estimated_document_count()))
        articles = list(mongo_coll.find({"abstract_3": None}).limit(LIMITED))

        articles_count = len(articles)
        # print(articles_count)
        for article in articles:
            body = article['new_content_1']
            #body = cut_sentences(body)
            # print(body)
            body = replaceNews(body)
            abstract = summarize(body, 3)
            print(abstract)
            # abstract = replaceNews(abstract)
            # abstract = re.sub('([。！？]+)', r"\1\n", abstract)
            # print(abstract)
            # print("\n")
            mongo_coll.update_one({'_id': article['_id']}, {'$set': {
                'abstract_3': abstract
            }}, upsert=False)
            print("第" + str(article['_id']) + "条数据处理完毕\n")
            print("已处理" + str(cnt) + "条数据， 还剩下" + str(articles_count - cnt) + "条数据\n")
            cnt += 1


if __name__ == '__main__':
    main()