#!/usr/bin/env python

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
    creds = load_credentials('credentials.ini')  # Adjust the path to the credentials file as needed
    auth = Authentication(creds)
    token = auth.initoauth()
    print(f"Generated Token: {token}")
