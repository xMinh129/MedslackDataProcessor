from configs.redis_config import r
import threading
import json
import requests
from configs.device_config import DEVICE


class Listener(threading.Thread):
    def __init__(self, r, channels):
        threading.Thread.__init__(self)
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)

    def work(self, item):
        try:
            data_from_queue = json.loads(item['data'])
            # TODO to send data to our backend
            # if item['channel'] == 'heart_rate':
            #     headers = {'data_type': 'heart_rate', 'deviceID': DEVICE['deviceID'], 'password': DEVICE['password']}
            # elif item['channel'] == 'blood_pressure':
            #     headers = {'data_type': 'blood_pressure', 'deviceID': DEVICE['deviceID'],
            #                'password': DEVICE['password']}
            # response = requests.post('http://localhost:5010/api/data/new', json=data_from_queue, headers=headers)
            # TODO to print the result from post request
            print data_from_queue
        except Exception as e:
            print e

    def run(self):
        for item in self.pubsub.listen():
            self.work(item)


if __name__ == "__main__":
    client = Listener(r, ['heart_rate', 'blood_pressure'])
    client.start()
