# Crawler

Requirements
```
# apt-get install python3-pip
# pip3 install requests
# pip3 install pymysql
# pip3 install beautifulsoup4
```

Database
```
CREATE TABLE articles( id char(10) NOT NULL, title text(65535), agreement char(10), provider char(10), category char(15), created_at char(15), finished_at char(15), crawled_at char(30), content text(65535), status boolean, PRIMARY KEY(id));
```
