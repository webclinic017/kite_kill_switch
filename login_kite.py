
import requests, json, pyotp
from kiteconnect import KiteConnect
from urllib.parse import urlparse
from urllib.parse import parse_qs
import os

import os
import traceback
import json

current_file_path = os.path.dirname(os.path.realpath(__file__))


def get_client_doc_from_json(client_id):
   try:
       json_file = os.path.join(current_file_path,'credentials.json')
       with open(json_file) as f:
           data = json.load(f)
           return data[client_id]
   except Exception as e:
       traceback.print_exc()

def login(client_id):
    user_doc = get_client_doc_from_json(client_id)
    api_key = user_doc['api_key']
    user_id = user_doc['client_id']
    user_password = user_doc['password']
    totp_key = user_doc['totp_key']
    api_secret = user_doc['secret_key']

    http_session = requests.Session()
    url = http_session.get(url='https://kite.trade/connect/login?v=3&api_key='+api_key).url
    response = http_session.post(url='https://kite.zerodha.com/api/login', data={'user_id':user_id, 'password':user_password})
    resp_dict = json.loads(response.content)
    http_session.post(url='https://kite.zerodha.com/api/twofa', data={'user_id':user_id, 'request_id':resp_dict["data"]["request_id"], 'twofa_value':pyotp.TOTP(totp_key).now()})
    url = url + "&skip_session=true"
    response = http_session.get(url=url, allow_redirects=True).url
    print(response)
    request_token = parse_qs(urlparse(response).query)['request_token'][0]

    kite = KiteConnect(api_key=api_key)
    data = kite.generate_session(request_token, api_secret=api_secret)
    access_token = data["access_token"]
    return access_token


