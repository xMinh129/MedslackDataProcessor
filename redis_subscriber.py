#from configs.redis_config import r
import threading
import json
import requests
#from configs.device_config import DEVICE


import redis

config = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
    }

r = redis.StrictRedis(**config)


class Listener(threading.Thread):
    def __init__(self, r, channels):
        threading.Thread.__init__(self)
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)

    def work(self, item):
        try:
            data_from_queue = json.loads(item['data'])
            print(data_from_queue)
            if item['channel'].decode("utf-8") == 'heart_rate':
                headers = {'data_type': 'heart_rate'}
            elif item['channel'].decode("utf-8") == 'spo2':
                headers = {'data_type': 'spo2'}
            response = requests.post('http://35.240.193.146:5010/api/stats/new', json=data_from_queue, headers=headers)
            print(response)
        except Exception as e:
            print(e)

    def run(self):
        for item in self.pubsub.listen():
            self.work(item)


if __name__ == "__main__":
    client = Listener(r, ['heart_rate', 'spo2'])
    client.start()
