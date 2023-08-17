# Python-M3U8

```
m3u8相關
```

# 用法

```bash
# 安裝依賴套件
pip install -r requirements.txt
```

## main-download.py

```ini
; 下載放置資料夾位置 預設 output
OUTPUT_PATH=

; 下載m3u8 json檔路徑 預設 conf/m3u8_source.json
M3U8_JSON_PATH=
```

```json
[
  {
    "execute": true, // 是否執行
    "m3u8_source_path": "sample.txt", // 資料 檔名:網址
    "options": {
      "m3u8_headers": {}, // m3u8標頭
      "ts_headers": {}, // ts 標頭
      "ts_url": null // ts 網址
    }
  }
]
```

```bash
usage: main-download.py [-h] [-o OUTPUT]

根據設定 下載m3u8

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        輸出資料夾
```

## main-preview.py

```bash
usage: main-preview.py [-h] -u URL [-o OUTPUT] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

將m3u8網址生成預覽片

options:
  -h, --help            show this help message and exit

通用:
  -u URL, --url URL     影片位址
  -o OUTPUT, --output OUTPUT
                        輸出資料夾
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --log_level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        設定紀錄log等級 DEBUG,INFO,WARNING,ERROR,CRITICAL 預設WARNING
```