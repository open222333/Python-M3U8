from src.preview import M3U8ToPreview
from argparse import ArgumentParser
from src import OUTPUT_PATH

parser = ArgumentParser(description='將m3u8網址生成預覽片')
group = parser.add_argument_group('通用')
group.add_argument('-u', '--url', type=str, help='影片位址', required=True)
group.add_argument('-o', '--output', type=str, help='輸出資料夾', default=OUTPUT_PATH)
group.add_argument(
    '-l', '--log_level', type=str, help='設定紀錄log等級 DEBUG,INFO,WARNING,ERROR,CRITICAL 預設WARNING',
    choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='WARNING'
)
args = parser.parse_args()


if __name__ == '__main__':
    m3u8topreview = M3U8ToPreview(m3u8_url=args.url)
    m3u8topreview.generate_preview(output_dir=args.output)
