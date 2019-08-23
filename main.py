import os
import time
import datetime
import threading
import requests
from queue import Queue
from collections import OrderedDict


class Color:
    BILIBILI_PINK = '\033[35m'
    SCORE_YELLOW = '\033[93m'
    GREEN = '\033[94m'
    ENDC = '\033[0m'
    SUCCESS_CHECKIN = GREEN + "打卡成功" + ENDC


class Point:
    def __init__(self):
        self.score = 0
        self.edit_time = 0

    def __repr__(self):
        return f"{Color.SCORE_YELLOW}总积分 {self.score}{Color.ENDC}"

    def __eq__(self, point):
        if isinstance(point, int):
            return self.score == point
        return self.score == point.score

    def __gt__(self, point):
        if isinstance(point, int):
            return self.score > point
        return self.score > point.score

    def __lt__(self, point):
        if isinstance(point, int):
            return self.score < point
        return self.score < point.score

    def add_score(self, score):
        self.score += score
        self.edit_time += 1


class Audience:
    def __init__(self, uid, nickname):
        self.uid = uid
        self.nickname = nickname
        self.point = Point()
        self.last_checkin_time = None
        self.colored_nickname = Color.BILIBILI_PINK + self.nickname + Color.ENDC

    def __repr__(self):
        return f"{Color.BILIBILI_PINK}{self.point}{Color.ENDC}"

    def add_score(self, score):
        if not self.last_checkin_time or datetime.date.today() > self.last_checkin_time:
            self.last_checkin_time = datetime.date.today()
            return self.point.add_score(score)
        else:
            raise ValueError(f'{self.colored_nickname} 今日已打卡，不要重复打卡哦;p')

    def get_checkin_times(self):
        return self.point.edit_time()


class Danmu():
    CHECK_URL = 'https://api.live.bilibili.com/lottery/v1/Storm/check'
    MSG_URL = 'https://api.live.bilibili.com/ajax/msg'

    def __init__(self, roomid: str, interval=1, front=30):
        self.roomid = str(roomid)  # 直播房间号
        self.interval = interval  # 间隔多少秒爬取一次弹幕， 默认为1
        self.audiences = {}
        self.front = front

        self._checkin_list = {}
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
            audience = self.audiences.get(dm['uid'], None)
            if audience:
                audience.nickname = dm.get('nickname')
            else:
                self.audiences.update({dm['uid']: Audience(dm['uid'], dm['nickname'])})

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
                uid = item.get('uid')
                text = item.get('text')
                audience = self.audiences.get(uid)
                print(f"[{item['timeline']}] {audience.colored_nickname}: {text}")

                # TODO re
                if text == "打卡" or text == '积分':
                    self._checkin_task.put(item)

    def check_in_worker(self):
        '''打印打卡成功'''
        while True:
            item = self._checkin_task.get()

            if item:
                audience = self.audiences.get(item.get('uid'))
                if item.get('text') == '打卡':
                    # TODO setable
                    score = 20 if len(self.audiences) < self.front else 10
                    try:
                        audience.add_score(score)
                    except ValueError as e:
                        print(e)
                    else:
                        print(f"[{item['timeline']}] {audience.colored_nickname} {Color.SUCCESS_CHECKIN} "
                              f"获得{score}积分，{audience.point}")
                if item.get('text') == '积分':
                    print(f"[{item['timeline']}] {audience.colored_nickname} {audience.point}")

    def run(self):
        t1 = threading.Thread(target=self.print_worker)
        t2 = threading.Thread(target=self.get_danmu_worker)
        t3 = threading.Thread(target=self.check_in_worker)

        t1.start()
        t2.start()
        t3.start()
        # TODO these threads will never join
        t1.join()
        t2.join()
        t3.join()


if __name__ == '__main__':
    roomid = input("请输入房间号: ").strip()
    # 7734200
    yx = Danmu(roomid)
    yx.check()
    yx.run()
