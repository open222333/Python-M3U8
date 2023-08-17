from src.download import M3U8
from src.logger import Log
from src import OUTPUT_PATH, LOG_LEVEL, M3U8_INFO
from argparse import ArgumentParser
from pprint import pformat

parser = ArgumentParser(description='根據設定 下載m3u8')
parser.add_argument('-o', '--output', type=str, help='輸出資料夾', default=OUTPUT_PATH)
args = parser.parse_args()

if __name__ == '__main__':
    logger = Log('MAIN-DOWNLOAD')
    logger.set_msg_handler()
    logger.set_level(LOG_LEVEL)

    setting_info = {
        '輸出資料夾': args.output
    }
    logger.info(f'{pformat(setting_info)}')

    for info in M3U8_INFO:
        if info['execute']:
            logger.debug(f'執行設定:\n{pformat(info)}')
            with open(info['m3u8_source_path']) as f:
                items = f.read().split('\n')
            for item in items:
                if item != '':
                    temp = item.split(',')
                    filename = temp[0]
                    m3u8_url = temp[1]
                    logger.debug(f'添加m3u8資訊: {filename}\n{m3u8_url}')

                    m3u8 = M3U8(
                        m3u8_file_source=m3u8_url,
                        file_name=filename,
                        output_dir=OUTPUT_PATH
                    )
                    if info['options']['ts_url']:
                        m3u8.set_ts_url(info['options']['ts_url'])
                    m3u8.set_m3u8_headers(info['options']['m3u8_headers'])
                    m3u8.set_ts_headers(info['options']['ts_headers'])
                    m3u8.run()