import re
import sys
import os
#import urllib2
from datetime import datetime
import subprocess
import json
import redis

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

        subprocess.call('sudo hciconfig hci0 reset', shell = True, stdout = DEVNULL)
        self.hcitool = subprocess.Popen(['sudo', '-n', 'hcitool', 'lescan', '--duplicates'], stdout = DEVNULL)
        self.hcidump = subprocess.Popen(['sudo', '-n', 'hcidump', '--raw'], stdout=subprocess.PIPE)

    def stop(self):
        print('Stop receiving broadcasts')
        subprocess.call(['sudo', 'kill', str(self.hcidump.pid), '-s', 'SIGINT'])
        subprocess.call(['sudo', '-n', 'kill', str(self.hcitool.pid), '-s', "SIGINT"])

    def get_lines(self):
        data = None
        try:
            print("reading hcidump...\n")
            #for line in hcidump.stdout:
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
    #if len(sys.argv) < 2:
    #    print('missing MAC address')
    #    exit(0)
    print('starting...')

    #deviceID = sys.argv[1]
    deviceID = 'E5:B0:E7:54:53:86'
    #deviceNAME = u'4F58494D45544552'
    deviceNAME = 'OX'.encode('utf-8').hex().upper()
    #TODO: PASS A SESSION ID VIA THE SENSOR
    scanner = BLEScanner()
    scanner.start()

    data = None
    while True:
        for line in scanner.get_lines():
            if line:
                found_mac = line[14:][:12]
                reversed_mac = ''.join(reversed([found_mac[i:i+2] for i in range(0, len(found_mac), 2)]))
                mac = ':'.join (a+b for a,b in zip(reversed_mac[::2], reversed_mac[1::2]))
                data = line[26:]
                if mac == deviceID:
                    #print(mac, data)
                    if deviceNAME in data:
                        data2 = data[20:24]
                        #print(data2)
                        HR = int(data2[0:2], 16)
                        OX = int(data2[2:4], 16)
                        Heart_Rate = {"stats": HR, "type": 'hr', 'sessionID': '12345678', "dateTime": str(datetime.now())}
                        SpO2 = {"stats": OX, "type": 'spo2', 'sessionID': '12345678',  "dateTime": str(datetime.now())}
                        r.publish('heart_rate', json.dumps(Heart_Rate))
                        r.publish('spo2', json.dumps(SpO2))
        scanner.stop()
        exit(0)


if __name__ == '__main__':
    main()
