# Python-M3U8

M3U8 串流視訊下載與預覽工具。支援批量下載 M3U8 串流影片，以及從 M3U8 網址生成預覽片段。

## 目錄

- [專案說明](#專案說明)
- [安裝依賴](#安裝依賴)
- [腳本說明](#腳本說明)
- [設定檔說明](#設定檔說明)
- [執行流程](#執行流程)
- [注意事項](#注意事項)

## 專案說明

本工具提供兩個腳本：

- `main-download.py`：根據 JSON 設定批量下載多個 M3U8 串流影片。
- `main-preview.py`：輸入 M3U8 網址，截取部分片段合成預覽影片。

## 安裝依賴

```bash
pip install -r requirements.txt
```

## 腳本說明

### main-download.py（批量下載）

```bash
usage: python main-download.py [-o OUTPUT]

參數：
  -o OUTPUT, --output OUTPUT   輸出資料夾（預設 output）
```

根據 `conf/m3u8_source.json` 的設定批量下載 M3U8 影片。

### main-preview.py（生成預覽片）

```bash
usage: python main-preview.py -u URL [-o OUTPUT] [-l LOG_LEVEL]

必填：
  -u URL, --url URL                               M3U8 影片位址

選填：
  -o OUTPUT, --output OUTPUT                      輸出資料夾（預設 output）
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}          log 等級（預設 WARNING）
```

截取 M3U8 影片的部分片段並合成預覽影片。

## 設定檔說明

### conf/config.ini.default

複製為 `conf/config.ini` 後修改：

```bash
cp conf/config.ini.default conf/config.ini
```

```ini
[SETTING]
; OUTPUT_PATH=      # 下載輸出資料夾，預設 output
; M3U8_JSON_PATH=   # JSON 設定檔路徑，預設 conf/m3u8_source.json
```

### conf/m3u8_source.json

```json
[
  {
    "execute": true,
    "m3u8_source_path": "conf/sample.txt",
    "options": {
      "m3u8_headers": {},
      "ts_headers": {},
      "ts_url": null
    }
  }
]
```

| 欄位 | 說明 |
|------|------|
| `execute` | `true` 才會執行此組設定 |
| `m3u8_source_path` | 來源清單檔案路徑，格式為每行 `檔名:網址` |
| `m3u8_headers` | 請求 M3U8 時的 HTTP Headers |
| `ts_headers` | 請求 TS 片段時的 HTTP Headers |
| `ts_url` | 指定 TS 片段的基底網址，若為 `null` 則從 M3U8 自動解析 |

### 來源清單檔案格式（m3u8_source_path）

每行格式為 `檔名:網址`：

```
video1:https://example.com/stream1/index.m3u8
video2:https://example.com/stream2/index.m3u8
```

## 執行流程

### 批量下載流程

```
讀取 conf/m3u8_source.json
  → 遍歷 execute: true 的設定
    → 讀取 m3u8_source_path 指定的清單檔（每行 檔名:網址）
      → 對每個 M3U8 網址：
        1. 請求 M3U8 播放清單（帶 m3u8_headers）
        2. 解析 TS 片段清單
        3. 下載所有 TS 片段（帶 ts_headers）
        4. 合併輸出至 OUTPUT 資料夾
```

### 預覽片生成流程

```
輸入 M3U8 網址
  → 請求並解析 M3U8 播放清單
    → 截取部分 TS 片段
      → 合成預覽影片並輸出
```

## 執行範例

```bash
# 批量下載，輸出至 downloads 資料夾
python main-download.py -o downloads

# 生成預覽片
python main-preview.py -u "https://example.com/stream/index.m3u8" -o previews

# 生成預覽片（顯示詳細 log）
python main-preview.py -u "https://example.com/stream/index.m3u8" -l DEBUG
```

## 注意事項

- `m3u8_source_path` 支援相對路徑（相對於執行目錄）。
- 若 M3U8 串流需要特定 Headers（如 Referer、Authorization），需在 `m3u8_headers` 或 `ts_headers` 中填寫。
- `ts_url` 用於 TS 片段網址與 M3U8 不在同一 domain 的情況。
- 輸出資料夾不存在時會自動建立。
- 部分受 DRM 保護的串流無法直接下載，需確認串流的授權方式。
