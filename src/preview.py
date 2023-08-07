from . import LOG_FILE_DISABLE, LOG_LEVEL
from .logger import Log
from typing import Union
from fake_useragent import FakeUserAgent
import subprocess
import requests
import cv2
import os


preview_logger = Log()
preview_logger.set_level(LOG_LEVEL)
if not LOG_FILE_DISABLE:
    preview_logger.set_file_handler()
preview_logger.set_msg_handler()


class M3U8ToPreview():
    """根據m3u8網址 建立 預覽片

    Args:
        m3u8_url (str): m3u8網址
    """

    def __init__(self, m3u8_url: str):
        self.m3u8_url = m3u8_url
        self.intro_mp4 = m3u8_url.rsplit('/', 1)[1].replace('.m3u8', '') + '.mp4'
        self.temp_dir = 'temp'
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        self.clip_files = []
        self.video_total_duration = None

    def set_temp_dir(self, temp_dir: str):
        self.temp_dir = temp_dir
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

    def set_log_level(self, level: str):
        preview_logger.set_level(level)

    def set_video_total_duration(self, video_total_duration: int):
        """設置影片時間長度

        Args:
            duration (int): 時間長度 單位 秒
        """
        self.video_total_duration = video_total_duration

    def get_video_duration(self) -> int:
        """取得m3u8網址的影片長度

        Returns:
            int: 秒數
        """
        user_agent = FakeUserAgent().google
        headers = {'User-Agent': user_agent}
        response = requests.get(self.m3u8_url, headers=headers)
        m3u8_content = response.text
        lines = m3u8_content.split("\n")
        durations = []

        for line in lines:
            if line.startswith("#EXTINF:"):
                line = line.replace("#EXTINF:", "")
                duration = float(line.split(",")[0])
                durations.append(duration)

        total_duration = int(sum(durations))
        self.video_total_duration = total_duration
        return total_duration

    def get_time_str(self, total_seconds: Union[int, float]) -> str:
        """依照秒數 回傳中文時間

        Args:
            total_seconds (int): 總秒數

        Returns:
            str: 回傳時間
        """
        msg = ''
        seconds = int(round(total_seconds % 60, 0))
        minutes = int((total_seconds // 60) % 60)
        hours = int(((total_seconds // 60) // 60) % 24)
        days = int(((total_seconds // 60) // 60) // 24)
        if days != 0:
            msg += f"{days}天"
        if hours != 0:
            msg += f"{hours}時"
        if minutes != 0:
            msg += f"{minutes}分"
        if seconds != 0:
            msg += f"{seconds}秒"
        return msg

    def get_time_point(self, total_seconds: Union[int, float]) -> str:
        """依照秒數 回傳 00:00:00格式

        Args:
            total_secends (int): 總秒數

        Returns:
            str: 回傳時間
        """
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def set_config(self):
        """透過影片秒數設定擷取的秒數和片段

        Returns:
            dict: {'split': split, 'duration': duration}
        """
        # result = subprocess.run(['ffmpeg', '-i', self.m3u8_url], capture_output=True, text=True)

        # 使用正則表達式從輸出結果中擷取影片時長
        # duration_str = re.search('Duration: (.*?),', result.stderr).group(1)

        # 將時間字串轉換成總秒數
        # hh, mm, ss = duration_str.split(':')
        # total_seconds = int(int(hh) * 3600 + int(mm) * 60 + float(ss))

        preview_logger.info(f'總秒數: {self.video_total_duration}')

        # 擷取的秒數
        # duration
        # 切幾份
        # split
        if self.video_total_duration <= 10 * 60:
            split = None
            duration = None
        elif self.video_total_duration <= 30 * 60:
            split = 3
            duration = 20
        elif self.video_total_duration <= 60 * 60:
            split = 4
            duration = 15
        elif self.video_total_duration <= 60 * 60 + 30 * 60:
            split = 5
            duration = 12
        else:
            split = 6
            duration = 10
        if split and duration:
            preview_logger.info(f'透過影片秒數設定片段數量和擷取的秒數:\n片段數量: {split}, 擷取的秒數: {duration}')
        # return {'split': split, 'duration': duration}
        self.split = split
        self.duration = duration

    def find_m3u8_time_point(self) -> Union[str, None]:
        """計算每隔n個影格的相似度 將時間點存入 self.time_points

        Args:
            output_mp4 (str): 原影片 輸入的M3U8
            split (int): 分割數量

        Returns:
            Union[str, None]: 正常回傳None 發生異常回傳錯誤訊息
        """
        # 計算每隔n個影格的相似度
        cap = cv2.VideoCapture(self.m3u8_url)
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        preview_logger.info(f"計算每隔n個影格的相似度 fps:{fps}")

        previous_frame = None
        similarity_scores = []
        frame_count = 0

        while cap.isOpened():
            ret, frame = cap.read()
            preview_logger.debug(f'計算每隔n個影格的相似度 ret: {ret}, frame: {frame}')

            if not ret:
                break

            if frame_count % fps == 0:  # 只計算每秒第一個影格
                if previous_frame is None:
                    previous_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    continue

                current_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                similarity_score = cv2.matchTemplate(current_frame, previous_frame, cv2.TM_CCOEFF_NORMED)
                similarity_scores.append(int(similarity_score))
                previous_frame = current_frame

            frame_count += 1

        # 先計算每個等分內的數量
        num_per_group = len(similarity_scores) // (self.split + 2)

        # 以每個等分的最高點作為選取標準
        try:
            max_similarity_indices = []
            for i in range(self.split + 2):
                start = i * num_per_group
                end = start + num_per_group
                group_indices = range(start, end)
                max_index = max(group_indices, key=lambda i: similarity_scores[i])
                max_similarity_indices.append(max_index)

            time_points = max_similarity_indices

            preview_logger.info(f'時間點: {time_points}')

            # 剔除頭尾
            self.time_points = time_points[1:-1]
            return None
        except Exception as err:
            err_msg = f'{err}\n{self.m3u8_url}\n影片處理過程中沒有計算出任何相似度得分'
            preview_logger.error(err_msg, exc_info=True)
            return err_msg

    def clip_time_points(self):
        """分割影片
        """
        self.str_time_points = []
        for i, time in enumerate(self.time_points):
            output_file = f'{self.temp_dir}/clip{i}.mp4'
            preview_logger.info(f'生成暫存檔:{output_file}')
            self.clip_files.append(output_file)

            # 使用 FFmpeg 剪輯
            preview_logger.info(f'時間點:{self.get_time_point(time)}, 長度: {self.duration}秒')
            self.str_time_points.append(f'時間點:{self.get_time_point(time)}, 長度: {self.duration}秒')
            command = f"ffmpeg -ss {time} -i {self.m3u8_url} -t {self.duration} -c copy -y {output_file}"
            preview_logger.info(f'使用 FFmpeg 剪輯 指令:\n{command}')
            result = subprocess.run(command, shell=True, capture_output=True)
            preview_logger.info(f'使用 FFmpeg 剪輯 結果:\nstdout={result.stdout.decode("utf-8")}\nstderr={result.stderr.decode("utf-8")}')

    def get_filelist(self):
        """建立 合併檔案指令字串

        Returns:
            _type_: _description_
        """
        i_option = "concat:"
        for i in range(len(self.clip_files)):
            if i != len(self.clip_files) - 1:
                i_option += f"{self.clip_files[i]}|"
            else:
                i_option += f"{self.clip_files[i]}"
        preview_logger.info(f'預計合併檔案列表: {i_option}')
        return i_option

    def merge_clips(self, output_dir: str = None):
        """合併分段影片

        Args:
            intro_mp4 (str): 輸出檔案
        """
        # 合併剪輯的mp4
        # merge_video_txt = self.get_filelist()
        merge_video_txt = "merge_video.txt"
        clip_files = [f for f in os.listdir(self.temp_dir) if f.startswith("clip") and f.endswith(".mp4")]

        clip_files.sort()

        # 將檔案名稱寫入"merge_video.txt"檔案中
        preview_logger.info('將檔案名稱寫入"merge_video.txt"檔案中')
        with open(merge_video_txt, "w") as f:
            for clip_file in clip_files:
                preview_logger.info(f'將檔案名稱寫入"merge_video.txt"檔案中: file {self.temp_dir}/{clip_file}')
                f.write(f"file '{self.temp_dir}/{clip_file}'\n")

        with open(merge_video_txt, 'r') as f:
            preview_logger.debug(f'merge_video_txt內容: {f.read()}')

        if output_dir:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)

            command = f"ffmpeg -f concat -safe 0 -i {merge_video_txt} -c copy {output_dir}/{self.intro_mp4}"
        else:
            command = f"ffmpeg -f concat -safe 0 -i {merge_video_txt} -c copy {self.intro_mp4}"
        preview_logger.info(f'合併剪輯的mp4 指令:\n{command}')
        result = subprocess.run(command, shell=True, capture_output=True)
        preview_logger.info(f'合併剪輯的mp4 結果:\nstdout={result.stdout.decode("utf-8")}\nstderr={result.stderr.decode("utf-8")}')

    def delete_temp_file(self):
        # 刪除暫存檔案
        # for file in glob.glob("clip*.mp4"):
        for file in os.listdir(self.temp_dir):
            if os.path.exists(f'{self.temp_dir}/{file}'):
                preview_logger.info(f'刪除檔案: {self.temp_dir}/{file}')
                os.remove(f'{self.temp_dir}/{file}')

        # 刪除 merge_video.txt 檔案
        if os.path.exists("merge_video.txt"):
            preview_logger.info(f'刪除檔案: merge_video.txt')
            os.remove("merge_video.txt")

        # 刪除 OUTPUT_MP4 檔案
        # if os.path.exists(self.m3u8_url):
        #     preview_logger.info(f'刪除檔案: {self.m3u8_url}')
        #     os.remove(self.m3u8_url)

    def generate_preview(self, route_path: str, output_dir: str = None):
        """執行剪輯預覽片

        Args:
            route_path (str): 路由位置
            output_dir (str, optional): 輸出資料夾位置. Defaults to route_path.
        """
        if output_dir == None:
            output_dir = route_path
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        data = {}
        if self.video_total_duration == None:
            self.get_video_duration()
        self.set_config()
        if self.split is not None and self.duration is not None:
            data['duration'] = self.video_total_duration
            preview_logger.info(f'影片長度: {self.get_time_str(self.video_total_duration)}, 執行')
            r = self.find_m3u8_time_point()
            if r != None:
                data['detail'] = r
                return (False, data)
            else:
                data['points'] = self.time_points
                self.clip_time_points()
                data['str_points'] = self.str_time_points
                data['preview_video_path'] = f'{route_path}/{self.intro_mp4}'
                data['local_video_path'] = f'{output_dir}/{self.intro_mp4}'
                self.merge_clips(output_dir=output_dir)
                self.delete_temp_file()
                return (True, data)
        else:
            msg = f'影片長度: {self.get_time_str(self.video_total_duration)}, 不執行'
            preview_logger.info(msg)
            data['detail'] = msg
            return (False, data)
