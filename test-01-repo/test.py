#!/usr/bin/env python
# python .\appD_02.py --creds credentials.ini --uri /api/endpoint --output output.json

import argparse
import configparser
import requests
import urllib3
import json

# Suppress only the single warning from urllib3.
urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

class Authentication:
    def __init__(self, credinfo):
        self.credinfo = credinfo
        self.authinfo = {}

    def initoauth(self):
        if "token" not in self.authinfo:
            print(f"initoauth: Getting Token with client {self.credinfo['clientsecret']}")

        url = self.credinfo['hosturl'] + self.credinfo['authuri']
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {
            "grant_type": "client_credentials",
            "client_id": self.credinfo['username'],
            "client_secret": self.credinfo['clientsecret']
        }

        try:
            result = requests.post(url, headers=headers, data=payload, verify=False)
        except requests.exceptions.RequestException as e:
            print(f"Error sending OAuth request: {e}")
            exit(1)

        if not result.ok:
            print(f"OAuth request failed: {result.status_code} {result.reason}")
            exit(1)

        jsondata = result.json()
        self.authinfo['token'] = jsondata['access_token']

        print("Successfully authenticated")
        return self.authinfo['token']

    def download_json(self, url, headers=None):
        if headers is None:
            headers = {
                "Authorization": f"Bearer {self.authinfo['token']}",
                "Content-Type": "application/json"
            }
        else:
            headers["Authorization"] = f"Bearer {self.authinfo['token']}"

        try:
            response = requests.get(url, headers=headers, verify=False)
        except requests.exceptions.RequestException as e:
            print(f"Error sending GET request: {e}")
            exit(1)

        if not response.ok:
            print(f"GET request failed: {response.status_code} {response.reason}")
            print(f"Response content: {response.content}")
            exit(1)

        jsondata = response.json()
        print("Successfully downloaded JSON data")
        return jsondata

def parse_arguments():
    parser = argparse.ArgumentParser(description='Authenticate with AppDynamics API using credentials from a file.')
    parser.add_argument('--creds', required=True, help='Path to the credentials .ini file')
    parser.add_argument('--uri', required=True, help='Endpoint URI for the API request')
    parser.add_argument('--output', required=True, help='Output file for the JSON data')
    return parser.parse_args()

def load_credentials(filepath):
    config = configparser.ConfigParser()
    config.read(filepath)

    creds = {
        "hosturl": config.get('credentials', 'hosturl'),
        "authuri": config.get('credentials', 'authuri'),
        "username": config.get('credentials', 'username'),
        "clientsecret": config.get('credentials', 'clientsecret'),
        "accountid": config.get('credentials', 'accountid')
    }
    return creds

if __name__ == "__main__":
    args = parse_arguments()
    creds = load_credentials(args.creds)
    auth = Authentication(creds)
    token = auth.initoauth()
    json_data = auth.download_json(creds['hosturl'] + args.uri)
    print("Downloaded JSON data: ", json.dumps(json_data, indent=4))

    with open(args.output, "w") as json_file:
        json.dump(json_data, json_file, indent=4)
    print(f"JSON data saved to {args.output}")
