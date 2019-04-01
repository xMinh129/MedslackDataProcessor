import threading
import json
import requests

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
        self.hr_dataset = []
        self.spo2_dataset = []

    def work(self, item):
        try:
            data_from_queue = json.loads(item['data'].decode('utf-8'))
            print(data_from_queue)

            if item['channel'].decode("utf-8") == 'heart_rate':
                self.hr_dataset.append(data_from_queue)
                # Sending data in chunks of 100 data points per API request
                if len(self.hr_dataset) >= 100:
                    try:
                        headers = {'data_type': 'heart_rate', 'device_authorization': 'easy_nmr_129'}
                        response = requests.post('http://35.240.193.146:5010/api/stats/new', json=self.hr_dataset,
                                                 headers=headers)
                        print('Response code: ' + response.status_code)
                        if response.status_code != 200:
                            for i in self.hr_dataset:
                                r.publish('heart_rate', i)
                                print('Error in sending. Data was put back on redis queue')
                            self.hr_dataset = []
                        else:
                            self.hr_dataset = []
                    except Exception as e:
                        print(e)
                        for i in self.hr_dataset:
                            r.publish('heart_rate', i)
                            print('Error in sending. Data was put back on redis queue')
                        self.hr_dataset = []

            elif item['channel'].decode("utf-8") == 'spo2':
                self.spo2_dataset.append(data_from_queue)
                # Sending data in chunks of 100 data points per API request
                if len(self.spo2_dataset) >= 100:
                    try:
                        headers = {'data_type': 'spo2', 'device_authorization': 'easy_nmr_129'}
                        response = requests.post('http://35.240.193.146:5010/api/stats/new', json=self.spo2_dataset,
                                                 headers=headers)
                        print('Response code: ' + response.status_code)
                        if response.status_code != 200:
                            for i in self.spo2_dataset:
                                r.publish('spo2', i)
                                print('Error in sending. Data was put back on redis queue')
                            self.spo2_dataset = []
                        else:
                            self.spo2_dataset = []
                    except Exception as e:
                        print(e)
                        for i in self.spo2_dataset:
                            r.publish('spo2', i)
                            print('Error in sending. Data was put back on redis queue')
                        self.spo2_dataset = []

        except Exception as e:
            print(e)

    def run(self):
        for item in self.pubsub.listen():
            self.work(item)
        if self.hr_dataset:
            headers = {'data_type': 'heart_rate'}
            requests.post('http://35.240.193.146:5010/api/stats/new', json=self.hr_dataset,
                          headers=headers)
        if self.hr_dataset:
            headers = {'data_type': 'spo2'}
            requests.post('http://35.240.193.146:5010/api/stats/new', json=self.spo2_dataset,
                          headers=headers)


if __name__ == "__main__":
    client = Listener(r, ['heart_rate', 'spo2'])
    client.start()
