import re
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


def main():
    # if len(sys.argv) < 2:
    #    print('missing MAC address')
    #    exit(0)
    print('starting queue scanner...')

    # deviceID = sys.argv[1]
    deviceID = 'D0:2B:91:3E:5B:D0'
    deviceNAME = 'OX'.encode('utf-8').hex().upper()

    # Start a new session when device start
    current_date = datetime.now()
    sessionID = deviceID + '_' + current_date.strftime('%Y%m%d%H%M')
    session_info = {
        'deviceID': deviceID,
        'sessionID': sessionID,
        'date': str(current_date)
    }

    # Create a new session
    new_session = requests.post('http://35.240.193.146:5010/api/session/new', json=session_info)

    scanner = BLEScanner()
    scanner.start()

    data = None
    i = 0

    while True:
        for line in scanner.get_lines():
            if line:
                found_mac = line[14:][:12]
                reversed_mac = ''.join(reversed([found_mac[i:i + 2] for i in range(0, len(found_mac), 2)]))
                mac = ':'.join(a + b for a, b in zip(reversed_mac[::2], reversed_mac[1::2]))
                data = line[26:]
                if mac == deviceID:
                    # print(mac, data)
                    if deviceNAME in data:
                        data2 = data[20:24]
                        # print(data2)
                        HR = int(data2[0:2], 16)
                        OX = int(data2[2:4], 16)
                        print("HeartRate=", HR, "SpO2=", OX)
                        if HR != 255:
                            Heart_Rate = {"stats": HR, "type": 'hr', 'sessionID': sessionID,
                                          "dateTime": str(datetime.now()), 'deviceID': deviceID}
                            r.publish('heart_rate', json.dumps(Heart_Rate))
                            i += 1
                        if OX != 255:
                            SpO2 = {"stats": OX, "type": 'spo2', 'sessionID': sessionID,
                                    "dateTime": str(datetime.now()), 'deviceID': deviceID}
                            r.publish('spo2', json.dumps(SpO2))
                            i += 1
        print(i)
        scanner.stop()
        exit(0)


if __name__ == '__main__':
    main()
