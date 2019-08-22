import os
import time
import threading
import requests
from queue import Queue
from collections import OrderedDict


class Danmu():
    CHECK_URL = 'https://api.live.bilibili.com/lottery/v1/Storm/check'
    MSG_URL = 'https://api.live.bilibili.com/ajax/msg'

    def __init__(self, roomid: str, interval=1):
        self.roomid = str(roomid)  # 直播房间号
        self.interval = interval  # 间隔多少秒爬取一次弹幕， 默认为1

        #  self._filepath = os.path.join(os.path.abspath('.'), self.roomid+'.txt')
        #  if not os.path.isfile(self._filepath):
        #      with open(self._filepath, 'w') as f:
        #          pass
        self._tasks = Queue()  # 需要依次打印的弹幕
        self._checkin_task = Queue()  # 需要记录的打卡弹幕
        self._unique = OrderedDict()  # 存储最近10个新弹幕
        self._headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
            "Referer": "https://live.bilibili.com/" + self.roomid,
        }

    def check(self):
        '''Check 直播间的状态是否正常'''
        payload = {'roomid': self.roomid}
        with requests.Session() as session:
            res = session.get(url=self.CHECK_URL, headers=self._headers, params=payload)
            assert res.status_code == 200
            print(f'Successfully Checked! Roomid = {self.roomid}')

    def get_danmu(self):
        '''单线程实时获取弹幕，去除重复弹幕'''
        payload = {
                'roomid': self.roomid,
                'csrf_token': '',
                'csrf': '',
                'visit_id': ''
        }
        with requests.Session() as session:
            res = session.post(url=self.MSG_URL, headers=self._headers, data=payload)
            assert res.status_code == 200
            raw_dms = res.json()['data']['room']  # It's a list of 10

        for dm in raw_dms:
            ucode = (dm['check_info']['ct'], dm['check_info']['ts'])

            if ucode not in self._unique:
                self._unique.update({ucode: 0})
                self._tasks.put(dm)

        # Get rid of old danmus
        while len(self._unique) > 10:
            self._unique.popitem(False)

    def get_danmu_worker(self):
        while True:
            self.get_danmu()
            time.sleep(self.interval)

    def print_worker(self):
        '''顺序打印所有弹幕'''
        while True:
            item = self._tasks.get()

            if item:
                # Colored: bilibili pink
                nickname = '\033[35m' + item['nickname']+'\033[0m'
                text = item['text']
                print(f"[{item['timeline']}] {nickname}: {text}")

                # TODO re
                if text == "打卡":
                    self._checkin_task.put(item)

    def check_in_worker(self):
        '''打印打卡成功'''
        while True:
            item = self._checkin_task.get()

            if item:
                nickname = '\033[35m' + item['nickname']+'\033[0m'
                print(f"[{item['timeline']}] {nickname} \033[94m打卡成功\033[0m")



    def run(self):
        t1 = threading.Thread(target=self.print_worker)
        t2 = threading.Thread(target=self.get_danmu_worker)

        t1.start()
        t2.start()
        # TODO these threads will never join
        t1.join()
        t2.join()


if __name__ == '__main__':
    roomid = input("请输入房间号: ").strip()
    # 7734200
    yx = Danmu(roomid, interval=0.2)
    yx.check()
    yx.run()
