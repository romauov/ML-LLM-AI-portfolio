import json
import requests
from requests.auth import HTTPBasicAuth

def post_request():
    url = "{{API_URL}}/get_qr/"
    with open('example.json', 'r') as file:
        data = json.load(file)

    headers = {
        "Content-Type": "application/json"
    }
    auth = HTTPBasicAuth('api_user', 'V7INZ7e_rO')
    response = requests.post(url, json=data, headers=headers, auth=auth, timeout=60)
    return response

response = post_request()
print(response.json())