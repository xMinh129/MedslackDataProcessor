import threading
import json
import requests
from flask import json
from cryptography.fernet import Fernet

import redis

config = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

r = redis.StrictRedis(**config)

file = open('.secret/secret.json').read()
DATA_ENCRYPT_KEY = json.loads(file)['DATA_ENCRYPT_KEY']  # The key will be type bytes
DEVICE_AUTH_CODE = json.loads(file)['DEVICE_AUTH_CODE']


def _encrypt_data(data):
    f = Fernet(DATA_ENCRYPT_KEY)
    encrypted_data = f.encrypt(json.dumps(data).encode())
    return encrypted_data


class Listener(threading.Thread):
    def __init__(self, r, channels):
        threading.Thread.__init__(self)
        self.redis = r
        self.pubsub = self.redis.pubsub()
        self.pubsub.subscribe(channels)
        self.hr_dataset = []
        self.spo2_dataset = []
        self.temp_dataset = []

    def work(self, item):
        try:
            data_from_queue = json.loads(item['data'].decode('utf-8'))
            print(data_from_queue)

            if item['channel'].decode("utf-8") == 'heart_rate':
                self.hr_dataset.append(data_from_queue)
                # Sending data in chunks of 100 data points per API request
                if len(self.hr_dataset) >= 20:
                    try:
                        headers = {'data_type': 'heart_rate', 'Authorization': DEVICE_AUTH_CODE}
                        response = requests.post('http://35.247.135.116:5010/api/stats/new',
                                                 data=_encrypt_data(self.hr_dataset),
                                                 headers=headers)
                        print('Response code: ' + str(response.status_code))
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
                if len(self.spo2_dataset) >= 20:
                    try:
                        headers = {'data_type': 'spo2',  'Authorization': DEVICE_AUTH_CODE}
                        response = requests.post('http://35.247.135.116:5010/api/stats/new',
                                                 data=_encrypt_data(self.spo2_dataset),
                                                 headers=headers)
                        print('Response code: ' + str(response.status_code))
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

            elif item['channel'].decode("utf-8") == 'temperature':
                self.temp_dataset.append(data_from_queue)
                # Sending data in chunks of 100 data points per API request
                if len(self.temp_dataset) >= 20:
                    try:
                        headers = {'data_type': 'temperature', 'Authorization': DEVICE_AUTH_CODE}
                        response = requests.post('http://35.247.135.116:5010/api/stats/new',
                                                 data=_encrypt_data(self.temp_dataset),
                                                 headers=headers)
                        print('Response code: ' + str(response.status_code))
                        if response.status_code != 200:
                            for i in self.temp_dataset:
                                r.publish('temperature', i)
                                print('Error in sending. Data was put back on redis queue')
                            self.temp_dataset = []
                        else:
                            self.temp_dataset = []
                    except Exception as e:
                        print(e)
                        for i in self.temp_dataset:
                            r.publish('temperature', i)
                            print('Error in sending. Data was put back on redis queue')
                        self.temp_dataset = []

        except Exception as e:
            print(e)

    def run(self):
        i = 0
        for item in self.pubsub.listen():
            self.work(item)
            i += 1
        print("All data in queue are clear")
        print(i)


if __name__ == "__main__":
    client = Listener(r, ['heart_rate', 'spo2', 'temperature'])
    client.start()
