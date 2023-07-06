from . import LOG_FILE_DISABLE, LOG_LEVEL
from .logger import Log
from pymediainfo import MediaInfo
import os


m3u8_logger = Log()
m3u8_logger.set_level(LOG_LEVEL)
if not LOG_FILE_DISABLE:
    m3u8_logger.set_file_handler()
m3u8_logger.set_msg_handler()


class ConvertToM3U8():

    def __init__(self, url: str, video_path: str, video_name: str, output_dir: str = 'output', quality: str = '720', encode: str = 'h264', test: bool = False) -> None:
        """_summary_

        Args:
            url (str): 上傳位置網址
            video_path (str): 原檔位置
            video_name (str): 輸出檔名
            output_dir (str, optional): 輸出資料夾. Defaults to 'output'.
            quality (str, optional): 畫質. Defaults to '720'.
            encode (str, optional): h264 h265 av1. Defaults to 'h264'.
        """
        self.video_path = video_path
        self.video_name = video_name
        self.output_dir = output_dir
        self.encode = encode
        self.quality = quality
        self.url = url
        self.test = test

    def get_video_aspect_ratio(self) -> float:
        """取得影片寬高比

        Returns:
            float: \n"直式": < 1\n"橫式": >= 1\n"拿不到資料": = 0
        """
        m3u8_logger.info('get_video_aspect_ratio start')
        try:
            media = MediaInfo.parse(self.video_path)
            width = 0
            height = 0
            for track in media.tracks:
                if track.track_type == 'Video':
                    width = track.width
                    height = track.height
                    break
            m3u8_logger.info('get_video_aspect_ratio end')
            return round(width / height, 2)
        except Exception as err:
            m3u8_logger.error(f'get_video_aspect_ratio error: {err}', exc_info=True)
            return 0

    def get_video_duration(self) -> int:
        """取得影片時間長度

        Returns:
            int: 回傳數值為 int 以秒為基本單位
        """
        m3u8_logger.info('get_video_duration start')
        duration = 0

        try:
            media = MediaInfo.parse(self.video_path)
            for track in media.tracks:
                if track.track_type == 'Video':
                    duration = track.duration
                    break
        except Exception as err:
            m3u8_logger.error(f'get_video_duration error: {err}', exc_info=True)
            return 0

        if duration == 0:
            try:
                command = f'ffprobe -allowed_extensions ALL {self.video_path} 2>&1 | grep "Duration" | cut -d " " -f 4 | sed s/,//'
                m3u8_logger.debug(f'指令\n{command}\n')
                result = os.popen(command).read()
                m3u8_logger.debug(f'結果 {result}')
                hour, minute, second = result.split(':')
                duration = ((float(hour) * 3600) + (float(minute) * 60) + int(float(second))) * 1000
            except Exception as err:
                m3u8_logger.error(f'get_video_duration error: {err}', exc_info=True)
                return 0

        m3u8_logger.info('get_video_duration end')
        return int(float(duration) / 1000)

    def video_convert_to_ts(self) -> str:
        """影片轉檔成ts格式

        ffmpeg Documentation:
        https://ffmpeg.org/ffmpeg.html

        av1:
        https://trac.ffmpeg.org/wiki/Encode/AV1

        質量由 -crf 決定
        比特率限制由 -b:v 決定，其中比特率必須非零。
        -r

        Returns:
            str: 輸出檔案 {self.output_dir}/{self.video_name}
        """
        m3u8_logger.info('video_convert_to_ts start')
        encoding = ''

        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)

        if self.encode == 'h264':
            encoding = 'libx264 -crf 23'
        elif self.encode == 'h265':
            encoding = 'libx265 -crf 28 -tune fastdecode'
        elif self.encode == 'av1':
            encoding = 'libaom-av1 -crf 30'
        else:
            m3u8_logger.error('video_convert_to_ts encoding 輸入錯誤')
            return ''

        if self.encode in ['h264', 'h265']:
            '''
            -c[:stream_specifier] codec (input/output,per-stream)
                http://ffmpeg.org/ffmpeg-all.html#Stream-specifiers-1
            -b
                以比特/秒為單位設置比特率。設置此項會自動激活恆定比特率 (CBR) 模式。如果未指定此選項，則設置為 128kbps。
                Set bit rate in bits/s. Setting this automatically activates constant bit rate (CBR) mode. If this option is unspecified it is set to 128kbps.
            -r[:stream_specifier] fps (input/output,per-stream)
                Set frame rate (Hz value, fraction or abbreviation).
            -ar[:stream_specifier] freq (input/output,per-stream)
                Set the audio sampling frequency. For output streams it is set by default to the frequency of the corresponding input stream. For input streams this option only makes sense for audio grabbing devices and raw demuxers and is mapped to the corresponding demuxer options.
            -video_track_timescale
                Set the timescale used for video tracks. Range is 0 to INT_MAX. If set to 0, the timescale is automatically set based on the native stream time base. Default is 0.
            -vf filtergraph (output)
                Create the filtergraph specified by filtergraph and use it to filter the stream.

                This is an alias for -filter:v, see the -filter option.

            stream_specifier
            http://ffmpeg.org/ffmpeg-all.html#Stream-specifiers-1

            -filter option
            http://ffmpeg.org/ffmpeg-all.html#filter_005foption
            '''
            command = f'ffmpeg -i {self.video_path} -c:v {encoding} -c:a aac -b:a 192k -r 30 -ar 44100 -video_track_timescale 90000 -vf scale=-2:{self.quality} {self.output_dir}/{self.video_name}-{self.quality} -y'
        else:
            command = f'ffmpeg -i {self.video_path} -c:v {encoding} -c:a aac -b:a 192k -r 30 -ar 44100 -video_track_timescale 90000 -vf scale=-2:{self.quality} {self.output_dir}/{self.video_name}-{self.quality} -y'

        m3u8_logger.debug(f'指令\n{command}\n')
        if not self.test:
            os.system(command)

        m3u8_logger.info('video_convert_to_ts end')
        return f'{self.output_dir}/{self.video_name}-{self.quality}.ts'

    def generate_enctyption_key(self) -> str:
        """產生加密的key
        key file 用 openssl 產生一個 16位元的 binary key
        key 產完之後 上傳到 s3

        Returns:
            str: 回傳字串 key_{self.quality}.key
        """
        m3u8_logger.info('generateEnctyptionKey start')

        command = f'openssl rand 16 > {self.output_dir}/key/key_{self.quality}.key'
        m3u8_logger.debug(f'指令\n{command}\n')
        if not self.test:
            os.system(command)
        m3u8_logger.info('generateEnctyptionKey end')
        return f'key_{self.quality}.key'

    def generate_enctyption_key_info(self, key_url: str, key_file_path: str) -> str:
        """產生加密m3u8時需要的keyinfo

        key info format:\n
        key URI        = http形式的key位置\n
        key file path  = key位置\n
        IV (optional)\n

        Args:
            key_url (str): key URI
            key_file_path (str): key file path

        Returns:
            str: 檔名 'key_{self.quality}.keyinfo'
        """
        m3u8_logger.info('generate_enctyption_key_info start')
        iv = os.popen('openssl rand -hex 16').read()
        data = f'{key_url}\n{key_file_path}\n{iv}'

        m3u8_logger.debug(f'keyinfo: \n{data}\n')

        with open(f'{self.output_dir}/key_{self.quality}.keyinfo', 'w') as k:
            k.write(data)
        m3u8_logger.info('generate_enctyption_key_info end')
        return f'key_{self.quality}.keyinfo'

    def video_convert_to_encrypted_m3u8(self, video_path: str, keyinfo_path: str, output_video_dir: str, output_video_name: str):
        """影片轉成加密的m3u8

        Args:
            video_path (str): ts 影片網址
            keyinfo_path (str): 加密資訊位址
            output_video_dir (str): _description_
            output_video_name (str): _description_
        """
        m3u8_logger.info('video_convert_to_encrypted_m3u8 start')
        if not os.path.exists(output_video_dir):
            os.mkdir(output_video_dir)

        command = f'ffmpeg -i {video_path} -c copy -hls_segment_type mpegts -hls_time 10 -start_number 1 -hls_key_info_file {keyinfo_path} -hls_segment_filename {output_video_dir}/{output_video_name}_%05d.ts -hls_list_size 0 -hls_playlist_type vod -hls_flags delete_segments+split_by_time {output_video_dir}/{output_video_name}.m3u8 -y'

        m3u8_logger.debug(f'指令\n{command}\n')

        if not self.test:
            os.system(command)
        m3u8_logger.info('video_convert_to_encrypted_m3u8 end')

    def remove_m3u8_key_host(self, m3u8_path_in_local: str, key_dir_in_s3: str, key_name: str):
        """刪除m3u8內的網址 將 key_dir_in_s3/key_name 替換成 key_name

        Args:
            m3u8_path_in_local (str): 本地的m3u8檔案
            key_dir_in_s3 (str): s3上key路徑
            key_name (str): s3上key名稱
        """
        file_data = ''
        with open(m3u8_path_in_local, 'r', encoding='utf-8') as f:
            for line in f:
                if key_name in line:
                    old = f'{key_dir_in_s3}/{key_name}'
                    newline = line.replace(old, key_name)
                    file_data += newline
                else:
                    file_data += line
        m3u8_logger.debug(f'刪除m3u8內的網址: \n{file_data}\n')
        with open(m3u8_path_in_local, 'w', encoding='utf-8') as f:
            f.write(file_data)

    def run(self):
        # 將影片轉換成ts
        ts_path = self.video_convert_to_ts(self.encode)

        # 加密
        self.generate_enctyption_key()
        self.generate_enctyption_key_info(
            f'{self.url}/{self.output_dir}/key_{self.quality}.key'
            f'{self.output_dir}/key_{self.quality}.key'
        )

        self.video_convert_to_encrypted_m3u8(
            f'{self.output_dir}/key_{self.quality}.keyinfo',
            f'{self.output_dir}',
            f'{self.video_name}-{self.quality}'
        )
        if not self.test:
            os.remove(f'{self.output_dir}/key_{self.quality}.keyinfo')

        self.remove_m3u8_key_host(
            f'{self.output_dir}/{self.video_name}-{self.quality}.m3u8',
            f'{self.url}/{self.output_dir}',
            f'key_{self.quality}.key'
        )
