#!/bin/bash

# Define the base path for your GitHub repository (if necessary)
ACTION_PATH=".github/actions"

# Define the path to the Python script and credentials file
SCRIPT_PATH="$ACTION_PATH/service_endpoint/test1.py"
CREDENTIALS_FILE="$ACTION_PATH/credentials.ini"

# Check if the Python script and credentials file exist
if [ -f "$SCRIPT_PATH" ] && [ -f "$CREDENTIALS_FILE" ]; then
    # Run the Python script with the specified arguments
    python3 "$SCRIPT_PATH" --creds "$CREDENTIALS_FILE"
else
    echo "Error: Either $SCRIPT_PATH or $CREDENTIALS_FILE not found!"
fi
