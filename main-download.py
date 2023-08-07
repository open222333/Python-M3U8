from src.download import M3U8Script
from src.logger import Log
from src import OUTPUT_PATH, LOG_LEVEL, M3U8_INFO
from argparse import ArgumentParser
from pprint import pformat

parser = ArgumentParser(description='根據設定 批量下載m3u8')
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
            datas = []
            for item in items:
                if item != '':
                    temp = item.split(':')
                    logger.debug(f'添加m3u8資訊: {temp}')
                    data = {
                        'filename': temp[0],
                        'url': temp[1]
                    }
                    datas.append(data)

            m3u8s = M3U8Script(
                datas=datas,
                output_dir=OUTPUT_PATH
            )
            m3u8s.run()
