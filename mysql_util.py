#!/usr/bin/python
# -*- coding: UTF-8 -*-
import pymysql
import os
import json
from tqdm import tqdm
import pickle
import logging

logger = logging.getLogger(__name__)
logger.setLevel(level = logging.INFO)
errors = []
author_type = set()
colummns_name_list = ["id","title","journal","issue","volume",
                          "pub_date","authors",
                          "affiliations","articleType",
                          "classificationSchemes"]
db = pymysql.connect("localhost","root","admin","aps")
cursor = db.cursor()

def get_data_path():
    pk_path = "./json_path.pk"
    if not os.path.exists(pk_path):
        abs_path, relavate_path = get_files_path(
            r"D:\data\APS\aps-dataset-metadata-2016")
        path_list = []
        for path in abs_path:
            subdirs, _ = get_files_path(path)
            for subdir in tqdm(subdirs):
                file_list, _ = get_files_path(subdir)
                path_list.extend(file_list)
        pickle.dump(path_list, open(pk_path, "wb"))
    else:
        path_list = pickle.load(open(pk_path, "rb"))
    return  path_list

def get_files_path(dir):
    '''
    获取文件夹下的所有文件
    :param dir:
    :return:
    '''
    files_name_list = os.listdir(dir)
    return [os.path.join(dir,fn) for fn in files_name_list],files_name_list

def create_table_articles(file_list):
    maxauthors = 0
    maxaff = 0
    val = []
    i = 0
    for txt_path in tqdm(file_list):
        with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
            txt = f.readlines()
            art_json = json.loads(txt[0])
            id = art_json["id"]
            affiliations = []
            authors = []
            if "affiliations" in art_json.keys():
                affiliations = art_json["affiliations"]
                if "authors" in art_json.keys() and len(art_json["authors"]) > 0:
                    authors = get_authors(art_json["authors"],affiliations)
            else:
                if "authors" in art_json.keys() and len(art_json["authors"]) > 0:
                    authors = art_json["authors"]
                    temp_authors = []
                    for author in authors:
                        temp_authors.append(author)
            try:
                del art_json["id"]
                del art_json["publisher"]
                del art_json["rights"]
                del art_json["identifiers"]
                del art_json["rights"]
                del art_json["affiliations"]
                del art_json["authors"]
            except:
                pass
            if len(authors) >= maxauthors:
                maxauthors = len(authors)
            if len(affiliations) >= maxaff:
                maxaff = len(affiliations)
            val.append((id,json.dumps(art_json),json.dumps(authors),json.dumps(affiliations)))
        i = i +1
        if (i+1)%50000 == 0:
            cursor.executemany(r"insert into articles(id,info,authors,affiliations) values(%s,%s,%s,%s)",
                               val)
            db.commit()
            print("add to db {} records".format(len(val)))
            val = []

    cursor.executemany(r"insert into articles(id,info,authors,affiliations) values(%s,%s,%s,%s)",
                       val)
    db.commit()
    print("add to db {} records".format(len(val)))
    print(maxauthors)
    print(maxaff)
def get_authors(authors,affiliations):
    temp_aff = {}
    for affiliation in affiliations:
        temp_aff[affiliation["id"]] = affiliation["name"]
    temp_authors = []

    for author in authors:
        author_type.add(author["type"])
        try:
            if "affiliationIds" in author:
                author["affiliation"] = [temp_aff[id] for id in author["affiliationIds"]]
                del author["affiliationIds"]
        except:
            print(authors)
        temp_authors.append(author)
    return temp_authors

def create_table_articles_info():
    sql_1 = "SELECT id,authors from articles limit "
    sql_1_result_num = 596786
    batch_size = 2000

    for idx in tqdm(range(0, sql_1_result_num, batch_size)):
        cursor.execute(sql_1 + "{},{}".format(str(int(idx)), str(int(batch_size))) )
        results = cursor.fetchall()
        temp = []
        for row in results:
            id = row[0]
            authors = json.loads(row[1])
            for author in authors:
                try:
                    type = author["type"]
                    if type == "Person":
                        fname = author["firstname"] if "firstname" in author.keys() else ""
                        lname = author["surname"] if "surname" in author.keys() else ""
                        full_name = fname + " " + lname
                        if len(fname) >=1 :
                            full_name_2 = fname[0] + " " + lname
                        else:
                            full_name_2 = lname
                        temp_row = [id, fname, lname, full_name.strip(), full_name_2.strip(),type]
                    else:
                        temp_row = [id, author["name"], "", author["name"].strip(), author["name"].strip(),type]
                    temp.append(tuple(temp_row))
                except:
                    pass
        cursor.executemany(r"insert into articles_info(id,fname,lname,full_name,full_name_2,au_type) values(%s,%s,%s,%s,%s,%s)",
                           temp)
        db.commit()
        print("add ",len(temp) ," to db")
    # cursor.execute("""
    #     CREATE TABLE author_article_list as SELECT
    # full_name_2,
    # JSON_ARRAYAGG(id) as id_list,
    # JSON_ARRAYAGG(fname) as fname_list,
    # JSON_ARRAYAGG(lname)	as lname_list
    # from
    # articles_info
    # GROUP BY
    # full_name_2""")



if __name__ == "__main__":
    # file_list = get_data_path()
    # create_table_articles(file_list)
    create_table_articles_info()
