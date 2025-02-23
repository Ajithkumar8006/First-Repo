#!/bin/bash

# Define the base path for your GitHub repository (if necessary)
ACTION_PATH=".github/actions"
CREDENTIALS_TEST="credentials.ini"
SERVICE_ENDPOINT="service_endpoint"

# Define the path to the Python script and credentials file
SE="$ACTION_PATH/$SERVICE_ENDPOINT/test1.py"

# Check if the Python script and credentials file exist
if [ -f "$SE" ]; then
    # Run the Python script with the specified arguments
    python3 "$SE" --creds "$CREDENTIALS_TEST"
else
    echo "Error: Either $SE or $CREDENTIALS_TEST not found!"
fi
