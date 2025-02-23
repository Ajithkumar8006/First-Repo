#!/bin/bash

# Define the base path for your GitHub repository (if necessary)
ACTION_PATH=".github/actions"
CREDENTIALS_TEST="credentials.ini"
SERVICE_ENDPOINT="service_endpoint"

# Define the path to the Python script and credentials file
SE1="test1.py"
SE2="bt_csv.py"

# Check if the Python script and credentials file exist
if [ -f "$SE1" ]; then
    # Run the Python script with the specified arguments
    python3 "$SE1" --creds ".github/actions/$CREDENTIALS_TEST"
else
    echo "Error: Either $SE1 or $CREDENTIALS_TEST not found!"
fi

# Check if the Python script and credentials file exist
if [ -f "$SE2" ]; then
    # Run the Python script with the specified arguments
    python3 "$SE2" --creds ".github/actions/$CREDENTIALS_TEST"
else
    echo "Error: Either $SE2 or $CREDENTIALS_TEST not found!"
fi
