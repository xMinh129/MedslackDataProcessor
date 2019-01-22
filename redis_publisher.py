from configs.redis_config import r
import json
import os
import datetime
import requests
from random import randint
from configs.device_config import DEVICE

os.environ['NO_PROXY'] = '127.0.0.1'


# def add_stat_session(session_ID, headers):
#     starting_time = str(datetime.datetime.now())
#     new_stats_data = {
#         "sessionID": session_ID,
#         'start': starting_time
#     }
#     try:
#         new_stats_session = requests.post("http://127.0.0.1:5010/api/session/new", json=new_stats_data, headers=headers)
#         current_stats_session = str(json.loads(new_stats_session.content)['data'])
#     except:
#         current_stats_session = False
#
#     return current_stats_session


def add_vital_data_to_queue(stats_session, vital):
    queue_data = {
        "sessionID": stats_session,
        "dateTime": str(datetime.datetime.now()),
        "stats": vital,
        "patientID": "G109876R"
    }
    r.publish('spo2', json.dumps(queue_data))


if __name__ == '__main__':
    status = True

    # headers = {'deviceID': DEVICE['deviceID'], 'password': DEVICE['password']}
    # # Create a new stat session whenever this script is run
    # current_stats_session = add_stat_session('77777', headers)

    # Add vital data to queue
    # TODO to change the stats session id
    while status:
        add_vital_data_to_queue("1234", randint(0, 90))
