import requests
import pymysql
import time
import datetime
import sys
from bs4 import BeautifulSoup
#import date


def insert(curs, data):
# insert data into database
    try:
        sql = """INSERT INTO petition_crawled (id, title, agreement, provider, category, created_at, finished_at, crawled_at, content, status, disagreement,block)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s)"""

        curs.execute(sql, (data['id'], data['title'], int(data['agreement']), data['provider'], data['category'],
                               datetime.datetime.strptime(data['created_at'], "%Y-%m-%d").date(),
                               datetime.datetime.strptime(data['finished_at'], "%Y-%m-%d").date(),
                               datetime.datetime.strptime(data['crawled_at'], "%Y-%m-%d").date(),
                               data['content'], data['status'],data['disagreement'], data['block']))
        conn.commit()
    except:
        print("# insert except!!")
        sys.exit()

def update(curs, data):
# update data from database
    try:
        sql = """UPDATE petition_crawled SET title = %s, agreement = %s, provider = %s, category = %s, created_at = %s,
                finished_at = %s, crawled_at = %s, content = %s, status = %s, disagreement = %s, block=%s  WHERE id = %s"""

        curs.execute(sql, (data['title'], data['agreement'], data['provider'], data['category'],
                            datetime.datetime.strptime(data['created_at'], "%Y-%m-%d").date(), # error
                            datetime.datetime.strptime(data['finished_at'], "%Y-%m-%d").date(), #non error
                            datetime.datetime.strptime(data['crawled_at'], "%Y-%m-%d").date(),
                            data['content'], data['status'],data['disagreement'], data['block'],data['id']))
        conn.commit()

    except:
        print("# update except!!")
        sys.exit()

def parse_json_data(data_in, only):
# parse json data
    data = {}
    json_data = data_in
    if json_data['status'] == "ok":
        for item in json_data['item']:

            # check if item is expired
            sql = "SELECT status FROM petition_crawled WHERE id = %s"
            curs.execute(sql, (item['id']))
            status = curs.fetchone()
            if status != None: # if item already exists
                if status[0] == '1': # if item is expired
                    return False

            data['id'] = item['id'] # 408609
            data['title'] = item['title']
            replaced_agreement= item['agreement'].replace(",","") # 1,192,049 -> 1192049 
            data['agreement'] = int(replaced_agreement)
            #print(item['agreement'],data['agreement'])
            data['provider'] = item['provider'] # naver / twitter / kakao / facebook
            if item['category'] == "전체":
                data['category'] = 0
            elif item['category'] == "정치개혁":
                data['category'] = 35
            elif item['category'] == "외교/통일/국방":
                data['category'] = 36
            elif item['category'] == "일자리":
                data['category'] = 37
            elif item['category'] == "미래":
                data['category'] = 38
            elif item['category'] == "성장동력":
                data['category'] = 39
            elif item['category'] == "농산어촌":
                data['category'] = 40
            elif item['category'] == "보건복지":
                data['category'] = 41
            elif item['category'] == "육아/교육":
                data['category'] = 42
            elif item['category'] == "안전/환경":
                data['category'] = 43
            elif item['category'] == "저출산/고령화대책":
                data['category'] = 44
            elif item['category'] == "행정":
                data['category'] = 45
            elif item['category'] == "반려동물":
                data['category'] = 46
            elif item['category'] == "교통/건축/국토":
                data['category'] = 47
            elif item['category'] == "경제민주화":
                data['category'] = 48
            elif item['category'] == "인권/성평등":
                data['category'] = 49
            elif item['category'] == "문화/예술/체육/언론":
                data['category'] = 50
            elif item['category'] == "기타":
                data['category'] = 51
            else :
                data['category'] = item['category']

            data['created_at'] = item['created'] # 2018-10-17
            data['finished_at'] = item['finished'] # 2018-11-16
            data['crawled_at'] = time.strftime('%Y-%m-%d')  # 2019-08-08 00:00:35
            if only == 1:
                data['status'] = 0 # in progress
            else:
                data['status'] = 1 # expired

            try:
                req = requests.get('https://www1.president.go.kr/petitions/'+str(item['id']))
                html = req.text
            except:
                print("# request except!!")
                sys.exit()



            soup = BeautifulSoup(html, 'html.parser')

            contents = soup.select(
                '#cont_view > div.cs_area > div.new_contents > div > div.petitionsView_left > div > div.petitionsView_write > div.View_write'
            )

            for content in contents:
                data['content'] = content.text
            data['disagreement'] = 0
            data['block'] = 0



            print(data['id'], data['category'])

            sql = "SELECT * FROM petition_crawled WHERE id = %s"
            if(curs.execute(sql, (data['id']))): # if item already exists
                update(curs, data)
            else:
                insert(curs, data)

            time.sleep(0.0001)

    else:
        print("error!")
        sys.exit()

def request_expired(curs, api, headers):
# request data expired
    param = {
        'c': '0', # category
        'only': '2', # 1: in progress / 2: expired (21)
        'page': 1,
        'order': '1' # 1: sort by most recent / 2: sort by recommended
    }

    while True:
        res = requests.post(api, headers=headers, data=param)
        json_data = res.json()
        if(len(json_data['item'])) == 0: # end of page
            print("end of page: no more data!")
            break
        parse_json_data(json_data, param['only'])
        param['page'] = param['page'] + 1

def request_progress(curs, api, headers):
# request data in progress
    param = {
        'c': '0', # category
        'only': '1', # 1: in progress / 2: expired (21)
        'page': 1,
        'order': '1' # 1: sort by most recent / 2: sort by recommended
    }

    while True:
        res = requests.post(api, headers=headers, data=param)
        json_data = res.json()
        if(len(json_data['item'])) == 0: # end of page
            print("end of page: no more data!")
            break
        result = parse_json_data(json_data, param['only'])
        if result == False:
            print("end of new data")
            break
        param['page'] = param['page'] + 1


if __name__ == "__main__":

    conn = pymysql.connect(host='127.0.0.1', port=3306, user='modutrend', password='trend1q2w3e!@',
                           db='petition', charset='utf8mb4', )

    curs = conn.cursor()

    api = "https://www1.president.go.kr/api/petitions/list"

    headers = {
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Content-Length': '25',
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Cookie': '_ga=GA1.3.797362558.1563182740; PHPSESSID=o3dcjttobo2j5gbtg1dgopf2n3; _gid=GA1.3.1717301274.1563798614',
        'Host': 'www1.president.go.kr',
        'Origin': 'https://www1.president.go.kr',
        'Referer': 'https://www1.president.go.kr/petitions/?c=0&only=2&page=2&order=1',
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }

#    sql = "SELECT COUNT(*) FROM articles"
#    curs.execute(sql)
#    count = curs.fetchone()[0]

#    if(count == 0):
    request_expired(curs, api, headers)
    request_progress(curs, api, headers)

#    else:
#        request_progress(curs, api, headers)
#        request_expired(curs, api, headers)
