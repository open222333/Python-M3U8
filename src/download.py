import os
import re
import re
import requests
from fake_useragent import FakeUserAgent
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from .logger import Log
from .progress_bar import ProgressBar
from . import LOG_LEVEL, LOG_FILE_DISABLE


logger = Log('DOWNLOAD')
logger.set_level(LOG_LEVEL)
if not LOG_FILE_DISABLE:
    logger.set_file_handler()
logger.set_msg_handler


class M3U8():

    def __init__(self, m3u8_file_source: str, file_name: str, output_dir: str = None) -> None:
        """_summary_

        Args:
            m3u8_file_source (str): m3u8 url位址
            file_name (str): 輸出檔名
            output_dir (str, optional): 輸出資料夾. Defaults to None.
        """
        self.m3u8_file_source = m3u8_file_source

        self.output_dir = output_dir

        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.ts_url = None
        self.file_name = file_name
        disable_warnings(InsecureRequestWarning)

    def set_m3u8_headers(self, **headers):
        self.m3u8_headers = headers

    def set_ts_headers(self, **headers):
        self.ts_headers = headers

    def set_ts_url(self, ts_url):
        self.ts_url = ts_url

    def __set_m3u8_from_url(self, **headers):
        try:
            self.m3u8_content = requests.get(self.m3u8_file_source, headers=headers)
        except Exception as err:
            logger.error(err, exc_info=True)

    def __set_m3u8_from_file(self):
        try:
            with open(self.m3u8_file_source, 'r') as f:
                self.m3u8_content = f.read()
        except Exception as err:
            logger.error(err, exc_info=True)

    def __parse_m3u8(self) -> list:
        """解析m3u8內容 取得ts網址串列

        Returns:
            list: 回傳檔名串列
        """
        try:
            content = self.m3u8_content.split('\n')
            result = []
            for i in content:
                if i == '':
                    pass
                elif not i.startswith("#"):
                    if self.ts_url:
                        result.append(f'{self.ts_url}{i.strip()}')
                    else:
                        result.append(i.strip())
            return result
        except Exception as err:
            logger.error(err, exc_info=True)

    def download_and_merge_ts(self, ts_urls: list, **headers) -> bool:
        """下載並合併ts檔

        Args:
            ts_urls (list): ts網址串列

        Returns:
            bool: _description_
        """
        ts_file = os.path.join(self.output_dir, f'{self.file_name}.ts')

        try:
            count = 0
            for ts_url in ts_urls:
                bar = ProgressBar()
                match = re.split(r'/', ts_url)
                ts_name = match[len(match) - 1]
                ts_content = requests.get(url=ts_url, headers=headers, stream=True)
                total = ts_content.headers.get('content-length')
                with open(ts_file, 'ab') as f:
                    data_length = 0
                    for chunk in ts_content.iter_content(chunk_size=1024):
                        f.write(chunk)
                        data_length += len(chunk)
                        bar(total=total, done=data_length, in_loop=True)
                count += 1
        except Exception as err:
            logger.error(f'{ts_name} 異常 {err}', exc_info=True)
            return False
        return True

    def run(self):
        try:
            if re.search(r'[a-zA-z]+://[^\s]*', self.m3u8_file_source):
                self.__set_m3u8_from_url()
            else:
                self.__set_m3u8_from_file()
            self.download_and_merge_ts(
                self.__parse_m3u8(),
                self.ts_headers
            )
        except Exception as err:
            logger.error(err, exc_info=True)


class M3U8Script():

    def __init__(self, datas: list, output_dir: str) -> None:
        """批量執行m3u8下載

        Args:
            datas (list): 輸入資料格式, [{ "filename": 檔名,"url": m3u8網址 },...]
            output_dir (str): 輸出資料夾
        """
        try:
            self.datas = datas
            ua = FakeUserAgent()
            self.ua = ua.random
            self.output_dir = output_dir

            self.ts_url = None

            self.m3u8_headers = {'user-agent': self.ua}
            self.ts_headers = {'user-agent': self.ua}

            self.per = 100
        except Exception as err:
            logger.error(err, exc_info=True)

    def set_per(self, per: int):
        """設置 每次執行幾筆

        Args:
            per (int): _description_
        """
        self.per = per

    def set_ts_url(self, ts_url: str):
        """設置 ts 網址

        Args:
            ts_url (str): _description_
        """
        self.ts_url = ts_url

    def set_m3u8_headers(self, m3u8_headers: dict):
        """設置 m3u8 標頭

        Args:
            m3u8_headers (dict): _description_
        """
        self.m3u8_headers = m3u8_headers
        self.m3u8_headers['user-agent'] = self.ua

    def set_ts_headers(self, ts_headers: dict):
        """設置 ts 標頭

        Args:
            ts_headers (dict): _description_
        """
        self.ts_headers = ts_headers
        self.ts_headers['user-agent'] = self.ua

    def run(self):
        total = len(self.datas)
        done = 0
        logger.info(f'{done}/{total} 0.0%')
        start = 0
        while True:
            end = start + self.per
            if end >= total:
                end == total

            for data in self.datas[start:end]:
                done += 1
                try:
                    m3u8 = M3U8(
                        m3u8_file_source=data['url'],
                        file_name=data['filename'],
                        output_dir=self.output_dir
                    )
                    if self.ts_url:
                        m3u8.set_ts_url(self.ts_url)
                    m3u8.set_m3u8_headers(self.m3u8_headers)
                    m3u8.set_ts_headers(self.ts_headers)
                    m3u8.run()

                    # 計算百分比
                    precent = float(round(100 * done / total, 1))
                    logger.info(f'{done}/{total} {precent}%')
                except Exception as err:
                    logger.error(err, exc_info=True)

            if end == total:
                break
