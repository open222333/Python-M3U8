from configparser import ConfigParser
import logging
import json
import os

config = ConfigParser()
config.read('.conf/config.ini')

# ******log設定******
# 關閉log功能 輸入選項 (true, True, 1) 預設 不關閉
LOG_DISABLE = config.getboolean('LOG', 'LOG_DISABLE', fallback=False)
# logs路徑 預設 logs
LOG_PATH = config.get('LOG', 'LOG_PATH', fallback='logs')
# 關閉紀錄log檔案 輸入選項 (true, True, 1)  預設 不關閉
LOG_FILE_DISABLE = config.getboolean('LOG', 'LOG_FILE_DISABLE', fallback=False)
# 設定紀錄log等級 DEBUG,INFO,WARNING,ERROR,CRITICAL 預設WARNING
LOG_LEVEL = config.get('LOG', 'LOG_LEVEL', fallback='WARNING')


if LOG_DISABLE:
    logging.disable()


OUTPUT_PATH = config.get('SETTING', 'OUTPUT_PATH', fallback='output')

if not os.path.exists(OUTPUT_PATH):
    os.makedirs(OUTPUT_PATH)

# 下載m3u8 json檔路徑 預設 conf/m3u8_source.json
M3U8_JSON_PATH = config.get('SETTING', 'M3U8_JSON_PATH', fallback='conf/m3u8_source.json')
M3U8_INFO = []
if os.path.exists(M3U8_JSON_PATH):
    with open(M3U8_JSON_PATH, 'r') as f:
        M3U8_INFO = json.loads(f.read())
