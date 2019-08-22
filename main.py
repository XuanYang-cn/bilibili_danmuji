import time
import threading
import requests
from queue import Queue
from collections import OrderedDict


class Danmu():
    CHECK_URL = 'https://api.live.bilibili.com/lottery/v1/Storm/check'
    MSG_URL = 'https://api.live.bilibili.com/ajax/msg'

    def __init__(self, roomid: str, interval=1):
        self._tasks = Queue()
        self._unique = OrderedDict()
        self.roomid = str(roomid)
        self.interval = interval
        self._headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/76.0.3809.100 Safari/537.36",
            "Referer": "https://live.bilibili.com/" + self.roomid,
        }

    def check(self):
        payload = {'roomid': self.roomid}
        with requests.Session() as session:
            res = session.get(url=self.CHECK_URL, headers=self._headers, params=payload)
            assert res.status_code == 200
            print(f'Successfully Checked! Roomid = {self.roomid}')

    def get_danmu(self):
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
        while True:
            time.sleep(0.5)
            item = self._tasks.get()

            if item:
                # Colored: bilibili pink
                nickname = '\033[35m' + item['nickname']+'\033[0m'
                print(f"[{item['timeline']}] {nickname}: {item['text']}")

    def run(self):
        t1 = threading.Thread(target=self.print_worker)
        t2 = threading.Thread(target=self.get_danmu_worker)

        t1.start()
        t2.start()
        t1.join()
        t2.join()


if __name__ == '__main__':
    roomid = input("请输入房间号: ").strip()
    yx = Danmu(roomid)
    yx.check()
    yx.run()
