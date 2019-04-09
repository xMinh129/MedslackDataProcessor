import sys
import os
from datetime import datetime
import subprocess
import json
import redis
import requests

config = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

r = redis.StrictRedis(**config)

secret_file = open('.secret/secret.json').read()
DEVICE_AUTH_CODE = json.loads(secret_file)['DEVICE_AUTH_CODE']
device_list = open('configs/device_list.json').read()
DEVICE_IDS = json.loads(device_list)['device_ids']
DEVICE_NAMES = [device.encode('utf-8').hex().upper() for device in json.loads(device_list)['device_names']]


class BLEScanner:
    hcitool = None
    hcidump = None

    def start(self):
        print('Start receiving broadcasts')
        DEVNULL = subprocess.DEVNULL if sys.version_info > (3, 0) else open(os.devnull, 'wb')

        subprocess.call('sudo hciconfig hci0 reset', shell=True, stdout=DEVNULL)
        self.hcitool = subprocess.Popen(['sudo', '-n', 'hcitool', 'lescan', '--duplicates'], stdout=DEVNULL)
        self.hcidump = subprocess.Popen(['sudo', '-n', 'hcidump', '--raw'], stdout=subprocess.PIPE)

    def stop(self):
        print('Stop receiving broadcasts')
        subprocess.call(['sudo', 'kill', str(self.hcidump.pid), '-s', 'SIGINT'])
        subprocess.call(['sudo', '-n', 'kill', str(self.hcitool.pid), '-s', "SIGINT"])

    def get_lines(self):
        data = None
        try:
            print("reading hcidump...\n")
            # for line in hcidump.stdout:
            while True:
                line = self.hcidump.stdout.readline()
                line = line.decode()
                if line.startswith('> '):
                    yield data
                    data = line[2:].strip().replace(' ', '')
                elif line.startswith('< '):
                    data = None
                else:
                    if data:
                        data += line.strip().replace(' ', '')
        except KeyboardInterrupt as ex:
            print("Key Board Interrupt")
            return
        except Exception as ex:
            print(ex)
            return


def create_new_data_session(device_id):
    # Start a new session when device start
    current_date = datetime.now()
    session_id = device_id + '_' + current_date.strftime('%Y%m%d%H%M')
    session_info = {
        'deviceID': device_id,
        'sessionID': session_id,
        'date': str(current_date)
    }
    headers = {"Authorization": DEVICE_AUTH_CODE}

    # Create a new session
    requests.post('http://35.240.193.146:5010/api/session/new', json=session_info, headers=headers)
    return session_id


# mac address: device ID, data contains device name
def is_device_authorised(mac, data):
    if mac in DEVICE_IDS:
        # print(mac, data)
        if DEVICE_NAMES[DEVICE_IDS.index(mac)] in data:
            return True
    return False


def main():
    print('starting queue scanner...')

    scanner = BLEScanner()
    scanner.start()

    data = None
    i = 0

    current_devices = []
    current_session_ids = []

    while True:
        for line in scanner.get_lines():
            if line:
                found_mac = line[14:][:12]
                reversed_mac = ''.join(reversed([found_mac[i:i + 2] for i in range(0, len(found_mac), 2)]))
                mac = ':'.join(a + b for a, b in zip(reversed_mac[::2], reversed_mac[1::2]))
                data = line[26:]
                # check if device is in the list of authorised device
                if is_device_authorised(mac, data):
                    # check if device is currently scanned
                    if mac not in current_devices:
                        session_id = create_new_data_session(mac)
                        current_devices.append(mac)
                        current_session_ids.append(session_id)
                    else:
                        session_id = current_session_ids[current_devices.index(mac)]
                    data2 = data[20:24]
                    # print(data2)
                    HR = int(data2[0:2], 16)
                    OX = int(data2[2:4], 16)
                    print("HeartRate=", HR, "SpO2=", OX)
                    if HR != 255:
                        heart_rate = {"stats": HR, "type": 'hr', 'sessionID': session_id,
                                      "dateTime": str(datetime.now()), 'deviceID': mac}
                        r.publish('heart_rate', json.dumps(heart_rate))
                        i += 1
                    if OX != 255:
                        spo2 = {"stats": OX, "type": 'spo2', 'sessionID': session_id,
                                "dateTime": str(datetime.now()), 'deviceID': mac}
                        r.publish('spo2', json.dumps(spo2))
                        i += 1
        print(i)
        scanner.stop()
        exit(0)


if __name__ == '__main__':
    main()
