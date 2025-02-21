#!/usr/bin/env python

import argparse
import configparser
import requests
import urllib3

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

        print(f"initoauth: Sending OAuth request: url: {url} headers: {headers} data: {payload}")

        # Sending the request to get the token
        try:
            result = requests.post(url, headers=headers, data=payload, verify=False)  # Disable SSL/TLS certificates verification
        except requests.exceptions.RequestException as e:
            print(f"Error sending OAuth request: {e}")
            exit(1)

        print(f"initoauth: OAuth result: {result}")

        if not result.ok:
            print(f"OAuth request failed: {result} {result.reason}")
            exit(1)

        jsondata = result.json()
        self.authinfo['token'] = jsondata['access_token']

        print("Successfully authenticated")
        return self.authinfo['token']

# Command-line argument parsing
def parse_arguments():
    parser = argparse.ArgumentParser(description='Authenticate with AppDynamics API using credentials from a file.')
    parser.add_argument('--creds', required=True, help='Path to the credentials .ini file')
    return parser.parse_args()

# Load credentials from the .ini file
def load_credentials(filepath):
    config = configparser.ConfigParser()
    config.read(filepath)

    # Assuming the .ini file has these sections/keys
    creds = {
        "hosturl": config.get('credentials', 'hosturl'),
        "authuri": config.get('credentials', 'authuri'),
        "username": config.get('credentials', 'username'),
        "clientsecret": config.get('credentials', 'clientsecret'),
        "accountid": config.get('credentials', 'accountid')
    }
    return creds

if __name__ == "__main__":
    # Parse command-line arguments
    args = parse_arguments()

    # Load credentials from the provided .ini file
    creds = load_credentials(args.creds)

    # Authenticate using the loaded credentials
    auth = Authentication(creds)
    token = auth.initoauth()
    print("Token obtained: ", token)
