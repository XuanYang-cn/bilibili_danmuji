import os
import sys
import requests
from bs4 import BeautifulSoup

FILE_NAME = '专场招聘.txt'


def get_info_and_store():
    URL = 'http://www.xsjy.whu.edu.cn/zftal-web/zfjy!wzxx!whdx10486/xjhxx_cxXjhForWeb.html'
    header = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
            'Referer': URL
    }

    payload = {
        'queryModel.showCount': 214,
        'queryModel.sortName': "sfyx, abs(jlsj) ,xjhkssj,sqbh",
        'queryModel.sortOrder': 'asc'
    }
    param = {'doType': 'query'}

    with requests.Session() as session:
        res = session.post(url=URL, headers=header, params=param, data=payload)

        jobs = res.json().get('items')

    file_path = os.path.join(os.path.abspath('.'), FILE_NAME)
    with open(file_path, 'w') as f:
        for item in jobs:
            item = {key: value for key, value in item.items() if value is not None}
            item.pop('queryModel')
            print(item)
            f.write(str(item))
            f.write('\n')


def company_detail(sqbh):
    url = 'http://www.xsjy.whu.edu.cn/zftal-web/zfjy!wzxx/zfjy!wzxx!whdx10486/xjhxx_ckXjhxx.html'
    header = {
            'Content-Type': 'text/html;charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36',
            'Referer': url,

            'Cookie': 'JSESSIONID=C8E491B5A8D851287581F92C038BA725; JSESSIONID=E96D4910CE347A141302261477FB04CB',
    }
    param = {'sqbh': sqbh}
    with requests.Session() as session:
        res = session.get(url=url, headers=header, params=param, timeout=3)
        assert res.status_code == 200

        text = res.text
    soup = BeautifulSoup(text, features="html.parser")
    a = soup.get_text()
    print(type(a))
    


if __name__ == '__main__':
    company_detail('8bd2ad939239504dec810b2700b4f0d9')
