import os
import re
import re
import binascii
import requests
import subprocess
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from fake_useragent import FakeUserAgent
from urllib.parse import urlparse
from urllib3 import disable_warnings
from urllib3.exceptions import InsecureRequestWarning
from .logger import Log
from .progress_bar import ProgressBar
from . import LOG_LEVEL, LOG_FILE_DISABLE


class M3U8():

    def __init__(self, m3u8_file_source: str, file_name: str, output_dir: str = None, **kwargs) -> None:
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

        self.key_url = None
        self.key = None
        self.crypto_method = None
        self.iv = None

        self.ts_url_prefix = None
        self.ts_urls = []
        self.file_name = file_name
        self.ts_file_path = os.path.join(self.output_dir, f'{self.file_name}.ts')
        ua = FakeUserAgent()
        self.ua = ua.random
        self.m3u8_headers = {'user-agent': self.ua}
        self.ts_headers = {'user-agent': self.ua}
        disable_warnings(InsecureRequestWarning)

        log_level = kwargs.get('log_level', LOG_LEVEL)
        self.logger = Log('M3U8')
        self.logger.set_level(log_level)
        if not LOG_FILE_DISABLE:
            self.logger.set_file_handler()
        self.logger.set_msg_handler()

    def set_m3u8_headers(self, m3u8_headers: dict):
        """設置 m3u8 標頭

        Args:
            m3u8_headers (dict): _description_
        """
        self.m3u8_headers.update(m3u8_headers)

    def set_ts_headers(self, ts_headers: dict):
        """設置 ts 標頭

        Args:
            ts_headers (dict): _description_
        """
        self.ts_headers.update(ts_headers)

    def set_ts_url_prefix(self, ts_url_prefix):
        """設置 ts 網址 前綴

        Args:
            ts_url_prefix (str):
            範例:
            https://www.example.com/path/to/page
            內的
            https://www.example.com/path/to/

            最後需要斜線
        """
        self.ts_url_prefix = ts_url_prefix

    def __set_m3u8_from_url(self, **headers):
        try:
            self.logger.info(f'從網址 {self.m3u8_file_source} 取得m3u8內容')
            self.m3u8_content = requests.get(self.m3u8_file_source, headers=headers)
        except Exception as err:
            self.logger.error(err, exc_info=True)

    def __set_m3u8_from_file(self):
        try:
            self.logger.info(f'從本地檔案 {self.m3u8_file_source} 取得m3u8內容')
            with open(self.m3u8_file_source, 'r') as f:
                self.m3u8_content = f.read()
        except Exception as err:
            self.logger.error(err, exc_info=True)

    def __binary_to_hex(self, binary_key: bytes):
        """二進制轉十六進制

        Args:
            binary_key (bytes): _description_

        Returns:
            _type_: _description_
        """
        hex_key = binascii.hexlify(binary_key).decode()
        return hex_key

    def __parse_ts_url_prefix(self):
        """解析m3u8網址 將網址部分設置為 ts_url_prefix
        """
        self.logger.info(f'解析 ts url')
        r = urlparse(self.m3u8_file_source)
        dir_path, _ = os.path.split(r.path)
        ts_url_prefix = f'{r.scheme}://{r.netloc}{dir_path}/'
        self.logger.info(f'解析 ts url 結果: {ts_url_prefix}')
        self.set_ts_url_prefix(ts_url_prefix)

    def __parse_m3u8(self):
        """解析m3u8內容
        取得ts網址串列, key_url
        """
        try:
            self.logger.info('解析m3u8內容')
            content = self.m3u8_content.text.split('\n')
            for i in content:
                if i == '':
                    pass
                elif i.startswith("#EXT-X-KEY"):
                    # 使用正則表達式提取 METHOD、URI 和 IV
                    method_match = re.search(r'METHOD=(\w+)', i)
                    uri_match = re.search(r'URI="([^"]+)"', i)
                    iv_match = re.search(r'IV=([\da-fA-Fx]+)', i)

                    if method_match:
                        self.crypto_method = method_match.group(1)
                    if uri_match:
                        self.key_url = uri_match.group(1)
                        r = requests.get(self.key_url)
                        self.key = r.content
                        # self.key = self.__binary_to_hex(r.content)
                        self.logger.info(f'key: {self.key}')
                    if iv_match:
                        iv_value = iv_match.group(1)
                        if iv_value.startswith('0x'):
                            iv_value = iv_value[2:]
                        self.iv = iv_value
                        self.logger.info(f'iv: {self.iv}')
                elif not i.startswith("#"):
                    if self.ts_url_prefix:
                        self.ts_urls.append(f'{self.ts_url_prefix}{i.strip()}')
                    else:
                        self.ts_urls.append(i.strip())
            self.logger.debug(f'ts列表: {self.ts_urls}')
        except Exception as err:
            self.logger.error(err, exc_info=True)

    def is_ffmpeg_installed(self) -> bool:
        """ffmpeg 是否已安裝

        Returns:
            bool: _description_
        """
        try:
            subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
            return True
        except FileNotFoundError:
            return False

    def covert_to_mp4(self):
        """轉檔成mp4
        """
        output_file = os.path.join(self.output_dir, f'{self.file_name}.mp4')
        command = ["ffmpeg", "-i", self.ts_file_path, "-c", "copy", output_file]
        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode == 0:
            self.logger.info("Command executed successfully.")
            if os.path.exists(self.ts_file_path):
                os.remove(self.ts_file_path)
        else:
            self.logger.error(f"Command encountered an error.\nError output: {result.stderr}")

    def aes_128_cbc_decrypt(self, content, key, iv, create_decrypted_file: bool = False):
        """aes-128 cbc模式 解碼

        Args:
            content (str): _description_
            key (str): _description_
            iv (str): _description_

        Returns:
            _type_: _description_
        """
        try:
            self.logger.info('進行 aes-128 cbc模式 解碼')
            # 對content進行填充操作，使用了pad函數並指定了pkcs7填充方式。
            # 這是對資料應用PKCS7填充，以確保其長度達到16位元組的倍數。
            content = pad(content, 16, style='pkcs7')
            cipher = AES.new(key, AES.MODE_CBC, bytes.fromhex(iv))
            decrypted_data = cipher.decrypt(content)
            # 解填充
            padding = decrypted_data[-1]
            decrypted_data = decrypted_data[:-padding]

            if create_decrypted_file:
                with open(os.path.join(self.output_dir, f'{self.file_name}.ts'), 'wb') as f:
                    f.write(decrypted_data)

            return decrypted_data
        except Exception as err:
            self.logger.error(f'{err}\nkey: {key}\niv: {iv}\n{content}\n{decrypted_data}')
            return None

    def download_and_merge_ts(self, ts_urls: list, headers: dict) -> bool:
        """下載並合併ts檔

        Args:
            ts_urls (list): ts網址串列
            headers (dict)

        Returns:
            bool: _description_
        """
        try:
            self.logger.info('下載並合併ts檔')
            count = 0
            for ts_url in ts_urls:
                bar = ProgressBar(title=self.file_name)
                match = re.split(r'/', ts_url)
                ts_name = match[len(match) - 1]
                ts_content = requests.get(url=ts_url, headers=headers, stream=True)
                with open(self.ts_file_path, 'ab') as f:
                    data_length = 0
                    for chunk in ts_content.iter_content(chunk_size=1024):
                        data_length += len(chunk)
                        f.write(chunk)
                count += 1
                bar(total=len(ts_urls), done=count, in_loop=True)
        except requests.exceptions.MissingSchema as err:
            self.logger.error(f'網址無效: {ts_url}')
            return False
        except Exception as err:
            self.logger.error(f'{ts_name}\n{ts_url}\n異常 {err}', exc_info=True)
            return False
        return True

    def run(self):
        try:
            if re.search(r'[a-zA-z]+://[^\s]*', self.m3u8_file_source):
                self.__set_m3u8_from_url()
            else:
                self.__set_m3u8_from_file()

            if not hasattr(self, 'm3u8_content'):
                raise RuntimeError('取得m3u8內容 失敗')

            self.__parse_m3u8()

            if len(self.ts_urls) == 0:
                raise RuntimeError('解析m3u8內容 失敗')

            if not os.path.exists(self.ts_file_path):
                download_and_merge_ts_result = self.download_and_merge_ts(
                    ts_urls=self.ts_urls,
                    headers=self.ts_headers
                )

                if not download_and_merge_ts_result:
                    raise RuntimeError(f'下載並合併ts檔 失敗')

            if self.key:
                with open(self.ts_file_path, 'rb') as f:
                    decrypt_result = self.aes_128_cbc_decrypt(
                        content=f.read(),
                        key=self.key,
                        iv=self.iv,
                        create_decrypted_file=True
                    )

                if decrypt_result == None:
                    raise RuntimeError('解碼失敗')

            if self.is_ffmpeg_installed():
                self.covert_to_mp4()
            else:
                raise RuntimeError('沒有安裝 ffmpeg, 無法執行轉檔 mp4')
        except Exception as err:
            self.logger.error(err, exc_info=True)


class M3U8Script():

    def __init__(self, datas: list, output_dir: str, **kwargs) -> None:
        """批量執行m3u8下載

        Args:
            datas (list): 輸入資料格式, [{ "filename": 檔名,"url": m3u8網址 },...]
            output_dir (str): 輸出資料夾
        """
        log_level = kwargs.get('log_level', LOG_LEVEL)
        self.logger = Log('M3U8Script')
        self.logger.set_level(log_level)
        if not LOG_FILE_DISABLE:
            self.logger.set_file_handler()
        self.logger.set_msg_handler()

        try:
            self.datas = datas
            self.output_dir = output_dir
            self.ts_url = None
            self.m3u8_headers = None
            self.ts_headers = None
            self.per = 100
        except Exception as err:
            self.logger.error(err, exc_info=True)

    def set_per(self, per: int):
        """設置 每次執行幾筆

        Args:
            per (int): _description_
        """
        self.per = per

    def set_script_ts_url(self, ts_url: str):
        """設置 ts 網址

        Args:
            ts_url (str): _description_
        """
        self.ts_url = ts_url

    def set_script_m3u8_headers(self, m3u8_headers: dict):
        """設置 m3u8 標頭

        Args:
            m3u8_headers (dict): _description_
        """
        self.m3u8_headers = m3u8_headers

    def set_script_ts_headers(self, ts_headers: dict):
        """設置 ts 標頭

        Args:
            ts_headers (dict): _description_
        """
        self.ts_headers = ts_headers

    def run(self):
        total = len(self.datas)
        done = 0
        self.logger.info(f'{done}/{total} 0.0%')
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
                        m3u8.set_ts_url_prefix(self.ts_url)
                    if self.m3u8_headers:
                        m3u8.set_m3u8_headers(self.m3u8_headers)
                    if self.ts_headers:
                        m3u8.set_ts_headers(self.ts_headers)
                    m3u8.run()

                    # 計算百分比
                    precent = float(round(100 * done / total, 1))
                    self.logger.info(f'{done}/{total} {precent}%')
                except Exception as err:
                    self.logger.error(err, exc_info=True)

            if end == total:
                break
