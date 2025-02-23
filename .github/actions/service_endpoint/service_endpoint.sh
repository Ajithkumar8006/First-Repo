#!/bin/bash

# Define the base path for your GitHub repository (if necessary)
ACTION_PATH=".github/actions"
CREDENTIALS_TEST=".github/credentials.ini"
SERVICE_ENDPOINT="service_endpoint"

export ONLINE_SERVICE="578"
export MOBILE_SERVICE="591"


# Define the path to the Python script and credentials file
SE1="$ACTION_PATH/$SERVICE_ENDPOINT/test1.py"
SE2="$ACTION_PATH/$SERVICE_ENDPOINT/bt_csv.py"

# Check if the Python script and credentials file exist
if [ -f "$SE1" ]; then
    # Run the Python script with the specified arguments
    python3 "$SE1" --creds "$CREDENTIALS_TEST"
else
    echo "Error: Either $SE or $CREDENTIALS_TEST not found!"
fi

# Check if the Python script and credentials file exist
if [ -f "$SE3" ]; then
    # Run the Python script with the specified arguments
    python3 "$SE3" 
else
    echo "Error: Either $SE2 not found!"
fi
