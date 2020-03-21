import pymongo
from tqdm import tqdm

MONOGO_HOST = "127.0.0.1"
MONOGO_PORT = 27017

'''
在mongodb 中为 每个集合建立索引 可以提高查询速度
语法 createIndex()方法基本语法格式如下所示：
>
>db.collection.createIndex(keys, options)
语法中 Key 值为你要创建的索引字段，1 为指定按升序创建索引，如果你想按降序来创建索引指定为 -1 即可。
createIndex() 方法中你也可以设置使用多个字段创建索引（关系型数据库中称作复合索引）。
实例
>db.col.createIndex({"title":1})
>db.col.createIndex({"title":1,"description":-1})
'''


def get_mongo_client():
    return pymongo.MongoClient(host=MONOGO_HOST, port=MONOGO_PORT)


def get_mongo_collection(client, db_name, coll_name):
    return client[db_name][coll_name]

def import_data_from_mysql_to_mongodb():
    import pymysql
    import json

    db = pymysql.connect("localhost", "root", "admin", "aps")
    cursor = db.cursor()

    client = get_mongo_client()
    table = get_mongo_collection(client,"whu_aps","articles")
    aps_citation_num = 596786
    batch_size = 50000
    sql = "select id,authors from articles limit "
    for start in tqdm(range(0,aps_citation_num,batch_size)):
        cursor.execute(sql+ "{},{}".format(start,batch_size))
        result = cursor.fetchall()
        temp = []
        for row in result:
            temp.append({"id" : row[0],
                              "authors": json.loads(row[1])})
        table.insert_many(temp)

if __name__ == "__main__":
    import_data_from_mysql_to_mongodb()