from .logger import Log
from . import LOG_FILE_DISABLE, LOG_LEVEL
import botocore
import boto3


logger = Log()
logger.set_level(LOG_LEVEL)
if not LOG_FILE_DISABLE:
    logger.set_file_handler()
logger.set_msg_handler()


class AmazonS3():
    """s3
    """

    def __init__(self, access_key_id: str, secret_access_key: str, region_name: str):
        self.s3_resource = boto3.resource(
            's3',
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            region_name=region_name
        )

    def upload_file(self, file_path_in_local: str, file_path_in_S3: str, bucket: str):
        """上傳檔案到 AWS S3

        Args:
            file_path_in_local (str): 本地的檔案路徑
            file_path_in_S3 (str): s3上的檔案路徑
            bucket (str): 目標bucket
        """
        self.s3_resource.Bucket(bucket).upload_file(
            file_path_in_local, file_path_in_S3)

    def check_file_exists(self, file_path_in_s3: str, bucket: str) -> bool:
        """_summary_

        Args:
            file_path_in_s3 (str): s3上的檔案路徑
            bucket (str): s3的bucket名稱

        Returns:
            bool: True = 檔案存在, False = 檔案不存在
        """
        try:
            self.s3_resource.Object(bucket, file_path_in_s3).load()
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error('file not found')
            else:
                logger.error(f"Something went wrong. Http error code is {e.response['Error']['Code']}")
            return False
        return True
