import shelve
import time


class Cache:
    def __init__(self):
        self.__db = shelve.open('cache')

    @staticmethod
    def is_resource_fresh(resource):
        return 'expires-at' in resource and \
               resource['expires-at'] > time.time()

    def get_resource(self, url):
        return self.__db[url] if url in self.__db else None

    def set_resource(self, url, resource):
        self.__db[url] = resource

    def delete_resource(self, url):
        del self.__db[url]
