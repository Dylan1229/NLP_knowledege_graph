import pymongo
import jieba.posseg as pseg
from py2neo import Graph, Node, Relationship, NodeMatcher


# 连接neo4j数据库，输入地址、用户名、密码
graph = Graph('http://localhost:7474', username='neo4j', password='123456')
# 在数据库中找有没有这个节点
def findHasNode(label, name, desc):
    #data2 = graph.find_one(label=label, property_key='name', property_value=name)
    matcher = NodeMatcher(graph)
    data2 = matcher.match(desc=desc).first()
    if(data2 == None):
        data2 = matcher.match(name=name).first()
        if data2 == None:
            return 0
        else:
            return data2
    else:
        return data2

def createRelationship(t1, t1_name, t1_desc, t2, t2_name, t2_desc, r):
    # t1 = 'PersonTest' #哪种类型的节点
    # t1_name = '张三'
    # t2 = 'PersonTest'
    # t2_name = "王五"
    tempDate = findHasNode(t1, t1_name, t1_desc)
    tempDate2 = findHasNode(t2, t2_name, t2_desc)

    # 如果没有tempDate这个节点就创建这个节点，并进行返回这个节点
    if(tempDate == 0):
        graph.create(Node(t1, name=t1_name, desc=t1_desc))
        tempDate = findHasNode(t1, t1_name, t1_desc)

    # 如果没有tempDate2这个节点就创建这个节点，并进行返回这个节点
    if(tempDate2 == 0):
        graph.create(Node(t2, name=t2_name, desc=t2_desc))
        tempDate2 = findHasNode(t2, t2_name, t2_desc)

    graph.create(Relationship(tempDate, r, tempDate2))

# 创建结点
# mongo_client = pymongo.MongoClient('127.0.0.1', 27017, username='root', password='ustc406ljj', authSource='admin')
mongo_client = pymongo.MongoClient(host='127.0.0.1', port=27017)
db = mongo_client['finance_data']
coll = db['sina_test']
articles = list(coll.find({}))
print(len(articles))
for article in articles:
    if 'triple' in article:
        triples = article['triple']
        triples_des = article['triple_des']

        if len(triples) > 0:
            for triple_ in triples:
                triple_ = triple_.strip('(')
                triple_ = triple_.strip(')')
                s1 = triple_.split(",")[0]
                e1 = s1
                r = triple_.split(",")[1]
                s3 = triple_.split(",")[2]
                e2 = s3
                e1_label=[]
                e1_name=[]
                e2_name=[]
                e2_label=[]
                # 获得e1、e2的词性
                for i in pseg.cut(e1):
                    e1_label.append(i.flag)
                    e1_name.append(i.word)

                for j in pseg.cut(e2):
                    e2_label.append(j.flag)
                    e2_name.append(j.word)

                # 根据实体链接结果实现多个同义单词对应一个实体
                e1_desc = e1
                e2_desc = e2
                if e1 in triples_des:
                    e1_desc = triples_des[e1]

                if e2 in triples_des:
                    e2_desc = triples_des[e2]

                createRelationship(e1_label[0], e1, e1_desc, e2_label[0], e2, e2_desc, r)

print(graph)
