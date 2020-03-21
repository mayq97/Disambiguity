#!/usr/bin/python
# -*- coding: UTF-8 -*-

from sklearn.feature_extraction.text import  TfidfVectorizer, TfidfTransformer
from sklearn.metrics.pairwise import cosine_similarity


def aff_sim(aff_1,aff_2,threshold = 0.6):

    '''
    判断两个机构的名称的相似度
    :param aff_1:
    :param aff_2:
    :return:
    '''
    try:
        tfidf_vec = TfidfVectorizer()
        tfidf_matrix = tfidf_vec.fit_transform([aff_1,aff_2])
        arr = tfidf_matrix.toarray()
        sim = cosine_similarity([arr[0,:]],[arr[1,:]])
        sim = sim[0,0]
    except:
        return False
    return True if sim >= threshold else False
def name_is_Abbr(name):
    '''
    判断name 是否是缩写形式，缩写一般是A M或者 A. M

    :param name:
    :return:
    '''

    name = name.strip()
    if len(name) == 1 or (len(name) > 1 and (name[1] == " " or name[1] == "." or name[1] == "-")):
        return True
    else:
        return False

if __name__ == "__main__":
    # read_data()
    # db.close()
    # print(author_type)
    # create_table_articles_info()
    pass
