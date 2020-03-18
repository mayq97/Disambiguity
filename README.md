# Disambiguity
科研文献中作者的消岐
在科研文献中作者同名现象非常严重，因此需要对同名作者进行消岐

本程序目的是对APS 数据集中的作者进行消岐，主要应用领域是图书情报领域

# 参考文献

Quantifying the evolution of individual scientific impact 提出了三个准则

- 1. Last names of the two authors are identical;

- 2. Initials of the first names and, when available, given names are the same. If the full first names and given names are present for both authors, they have to be identical;

- 3. One of the following is true:

    • The two authors cited each other at least once;

    • The two authors share at least one co-author;

    • The two authors share at least one similar affiliations (measured by cosine similarity and tf-idf metrics) (51)
    
# 具体操作流程 
- 1.数据导入到mysql 中

- 2.将同名作者（FirstName的第一个字母 + LastName）进行分组

- 3.将引文数据，论文数据导入到 mongodb 中，（目的是提高处理的速度）

- 4.基于上述三个准则中 -3 条件的三个子条件进行作者消岐
