#!/usr/bin/env python
#
# python .\appD_02.py --creds credentials.ini

import argparse
import configparser
import requests
import urllib3
import json
import os
import sys

# Access environment variables
app_online = os.getenv('ONLINE_SERVICE')
app_mobile = os.getenv('MOBILE_SERVICE')
print(f"online app id: {app_online}")
print(f"mobile app id: {app_mobile}")

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

        # Sending the request to get the token
        try:
            result = requests.post(url, headers=headers, data=payload, verify=True)  # Avoid disabling SSL/TLS verification
        except requests.exceptions.RequestException as e:
            print(f"Error sending OAuth request: {e}")
            sys.exit(1)

        print(f"initoauth: OAuth result: {result}")

        if not result.ok:
            print(f"OAuth request failed: {result} {result.reason}")
            sys.exit(1)

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

        print(f"download_json: Sending GET request: url: {url} headers: {headers}")

        try:
            response = requests.get(url, headers=headers, verify=True)  # Avoid disabling SSL/TLS verification
        except requests.exceptions.RequestException as e:
            print(f"Error sending GET request: {e}")
            sys.exit(1)

        print(f"download_json: GET request result: {response}")

        if not response.ok:
            print(f"GET request failed: {response} {response.reason}")
            print(f"Response content: {response.content}")
            sys.exit(1)

        jsondata = response.json()
        print("Successfully downloaded JSON data")
        return jsondata

# Command-line argument parsing
def parse_arguments():
    parser = argparse.ArgumentParser(description='Authenticate with AppDynamics API using credentials from a file.')
    parser.add_argument('--creds', required=True, help='Path to the credentials .ini file')
    return parser.parse_args()

# Load credentials from the .ini file
def load_credentials(filepath):
    if not os.path.isfile(filepath):
        print(f"Error: The file {filepath} does not exist.")
        sys.exit(1)

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

    # Define the business transactions request
    businesstransactions = {
        "type": "GET",
        "uri": '/controller/restui/policy2/policiesSummary/591',
        "returntype": "JSON"
    }

    # Download JSON data from the specified URL (hosturl is now obtained from credentials)
    json_data = auth.download_json(creds['hosturl'] + businesstransactions['uri'])
    print("Downloaded JSON data: ", json.dumps(json_data, indent=4))

    # Save the downloaded JSON data to a file
    output_file_path = f".github/actions/service_endpoint/{app_online}_bt.json"
    with open(output_file_path, "w") as json_file:
        json.dump(json_data, json_file, indent=4)
    print(f"JSON data saved to {output_file_path}")
    print(f"online app id: {app_online}")
