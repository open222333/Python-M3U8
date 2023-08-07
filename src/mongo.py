from pymongo import MongoClient
import random


class MongoRandomSample():

    def __init__(self, host: str, db: str, collection: str) -> None:
        """抽樣指定資料庫以及集合的資料,數量預設為200

        Args:
            db (str): 要抽取樣本的資料庫名稱
            collection (str): 要抽取樣本的集合名稱
        """
        self.sample_size = 200
        self.client = MongoClient(host)
        self.db = db
        self.collection = collection
        self.query = None

    def set_sample_size(self, size: int):
        """設置樣本數量

        Args:
            size (int): 指定數量
        """
        self.sample_size = size

    def set_query(self, **kwargs):
        self.query = kwargs

    def get_random_datas(self):
        """取得樣本

        Returns:
            list: mongo文件
        """
        if self.query:
            documents = list(self.client[self.db][self.collection].find(self.query))
        else:
            documents = list(self.client[self.db][self.collection].find())
        random_documents = random.sample(documents, self.sample_size)
        return random_documents
