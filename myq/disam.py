#!/usr/bin/python
# -*- coding: UTF-8 -*-
'''
    1. 根据作者的名字（first name 的第一个字母 + last name）对article_info 数据进行分组
        得到 author_article_list 表，分组后的作者数目凡是大于等于2的，都是需要消歧的；
    2. 分组后的，每一组中的名字，一定是相同的，不需要对名字进行判断了；（条件 1 2自动满足）
    3. 对其他条件进行判断，只需满足其中一个，其他两个条件就不再判断了。
        A 两位作者至少有一个相似的从属关系；
        B 两位作者至少有一位共同作者；
        C 两位作者至少互相引用了一次；
'''
import json
import pymysql
from itertools import combinations,product
from tqdm  import tqdm
from myq.mongodb_util import get_mongo_collection,get_mongo_client
from myq.util import aff_sim,name_is_Abbr
import logging
logging.basicConfig(level = logging.INFO,format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

db = pymysql.connect("localhost","root","admin","aps")
cursor = db.cursor()
client = get_mongo_client()
table_articles  = get_mongo_collection(client,"whu_aps","articles")
table_citation = get_mongo_collection(client,"whu_aps","citation")
table_result = get_mongo_collection(client,"whu_aps","result")
author_id = 79857
save_data = []


def coauthor(au_list):
    temp = au_list[1] & au_list[0]
    return True if len(temp) >0 else False




def get_affs_coauthors_info(articles_id_list,lname):
    '''
    :param articles_id_list:
    :param lname:
    :return:
    '''
    results = table_articles.find({
    'id': {
        '$in': articles_id_list
    }
    })
    article_author_list = {}

    for row in results:
        article_id = row["id"]
        coauthors = set()
        affs = set()
        for author in row["authors"]:
            try:
                if author["surname"] == lname:
                    affs = set(author["affiliation"])
                else:
                    coauthors.add(author["name"])
            except:
                pass
        article_author_list[article_id] = {"coauthors":coauthors,"affs":affs}
    return article_author_list
def aff_check(aff_list_1,aff_list_2):
    for aff_piar in product(aff_list_1,aff_list_2):
        if aff_sim(aff_piar[0],aff_piar[1]):
            return True
    return False

def name_check(name_1,name_2):
    '''
    判断两个名字是否一致，
    name_1,name_2 如果都不是缩写形式 则进行直接匹配
                    如果有一个存在缩写情况，则只需首字母一样
    :param name_1:
    :param name_2:
    :return:
    '''
    name_1 = name_1.lower().strip()
    name_2 = name_2.lower().strip()

    if name_is_Abbr(name_1) or name_is_Abbr(name_2):
        return True if (len(name_1) >=1 and len(name_2)>=1) and name_1[0] == name_2[0] else False
    else:
        return True if name_1 == name_2 else False
def get_refs(id_list):
    results = table_citation.find({
        'citing_doi': {
            '$in': id_list
        }
    })
    refs = {}
    for row in results:
        temp = refs.get(row["citing_doi"],set())
        temp.add(row["cited_doi"])
        refs[row["citing_doi"]] = temp
    return refs


def name_disam():
    '''
    SELECT full_name_2,id_list,lname_list,num,all_equal from author_article_list WHERE num >1
    full_name_2 数量出现两次及以上的则需要进行消岐
    :return:
    '''
    global author_id
    sql_1 = "SELECT id_list,fname_list,lname_list from author_article_list WHERE num >1 limit "
    sql_1_result_num = 145661
    batch_size = 10000
    def add_result(i,j,equal):
        global author_id
        if equal:
            if flag[i] == 0 and flag[j] == 0:
                author_id = author_id + 1
                flag[i] = author_id
                flag[j] = author_id
                temp_output[author_id] = set([i,j])
            elif flag[i] > 0 and flag[j] == 0:
                flag[j] = flag[i]
                temp = temp_output.get(flag[i],set())
                temp.add(j)
                temp_output[flag[i]] = temp
            elif flag[i] == 0 and flag[j] > 0:
                flag[i] = flag[j]
                temp = temp_output.get(flag[j], set())
                temp.add(i)
                temp_output[flag[j]] = temp
            elif  flag[j] > 0 and flag[i] > 0  and not (flag[i] == flag[j]):
                temp = temp_output[flag[i]] | temp_output[flag[j]]
                temp_output[flag[i]] = temp
                del temp_output[flag[j]]
                for art  in temp:
                    flag[art] = flag[i]
        else:
            if flag[i] == 0:
                author_id = author_id+1
                flag[i] = author_id
                temp_output[author_id] = set([i])
            if flag[j] == 0:
                author_id = author_id+1
                flag[j] = author_id
                temp_output[author_id] = set([j])

    def cocite(article_1, article_2):
        try:
            return True if article_1 in ref_list[article_2] and article_2 in ref_list[article_1] else False
        except:
            return False

    for idx in range(0,sql_1_result_num,batch_size):
        sql = sql_1 + "{},{}".format(str(int(idx)),str(int(batch_size)))
        cursor.execute(sql)
        #SELECT id_list,fname_list,lname_list from author_article_list WHERE num >1 limit 0,1000
        results = cursor.fetchall()
        results = list(results)
        for row_index,row in enumerate(results):
            articles_id_list = json.loads(row[0])
            fname_list = json.loads(row[1])
            lname_list = json.loads(row[2])
            temp_output = {}
            flag = [0]*len(articles_id_list)
            art_info = get_affs_coauthors_info(articles_id_list,lname_list[0])
            ref_list = get_refs(articles_id_list)
            for art_piar in combinations(range(len(articles_id_list)),2):
                i = art_piar[0]
                j = art_piar[1]
                art_id_i = articles_id_list[i]
                art_id_j = articles_id_list[j]

                if name_check(fname_list[i],fname_list[j]):
                    temp_art_authors = [art_info[art_id_i]["coauthors"],art_info[art_id_j]["coauthors"]]
                    if aff_check(art_info[art_id_i]["affs"],art_info[art_id_j]["affs"]) or cocite(art_id_i,art_id_j) or coauthor(temp_art_authors):
                        add_result(i,j,True)
                    else:
                        add_result(i,j,False)
                else:
                    add_result(i,j,False)
            update(temp_output,articles_id_list,fname_list,lname_list)
            row_index = row_index +1
            if row_index % 100 == 0 :
                logger.info("process {} to {} at {} / {}".format(idx,idx+batch_size,row_index,batch_size))


def name_freq_equal_1():
    """
    SELECT full_name_2,id_list from author_article_list WHERE num =1
    名字出现一次的不需要进行消岐
    :return:
    """
    sql_2 = "SELECT full_name,id_list from author_article_list WHERE num =1 ORDER BY num ASC limit "
    sql_2_result_num = 79857

    batch_size = 1000
    author_id = 0
    for idx in tqdm(range(0, sql_2_result_num, 1000)):
        sql = sql_2 + "{},{}".format(str(int(idx)), str(int(batch_size)))
        cursor.execute(sql)
        results = cursor.fetchall()
        temp_output = []
        for row in results:
            author_id = author_id + 1
            temp_output.append((json.loads(row[1])[0], row[0],author_id))

        cursor.executemany(r"INSERT INTO result(id, full_name_2, author_id) VALUES (%s,%s,%s)",
                       temp_output)
        db.commit()
        logger.info("add ", 1000 , "records to db")

        temp_output.clear()
        logger.info("*" * 40)
    print(author_id)

def update(temp_output,articles_id_list,fname_list,lname_list):
    '''
    将需要保存的作者信息 暂存在 save_data 中，当暂存数量大于1000时，提交数据
    :param data:
    :param full_name_2:
    :return:
    '''

    for au_id in temp_output.keys():
        au_art_list = temp_output[au_id]
        for id in au_art_list:
            save_data.append((articles_id_list[id],
                              fname_list[id],
                              lname_list[id],
                              au_id))

    if len(save_data) >= 10000:
        cursor.executemany(r"INSERT INTO result(id, fname, lname,author_id) VALUES (%s,%s,%s,%s)",
                           save_data)
        db.commit()
        logger.info("add {} records to db".format(len(save_data)))
        save_data.clear()
        logger.info("*"*50)


if __name__ == "__main__":
    # name_freq_equal_1()
    name_disam()
    cursor.executemany(r"INSERT INTO result(id, fname, lname,author_id) VALUES (%s,%s,%s,%s)",
                       save_data)
    logger.info("add {} records to db".format(len(save_data)))
    db.commit()
    logger.info("Finish ! ")




