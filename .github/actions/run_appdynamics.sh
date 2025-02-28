#!/bin/bash

# Run the Python script with the provided parameters
echo "Running AppDynamics API script for app: $APP_NAME with transaction: $TRANSACTION_NAME..."

# Ensure the correct values are being passed to the Python script
python appdynamics_api.py --cred .github/actions/credentials.ini --debug "5" --output "json" --app "Patient_Online_Services_Portal_Test" --transaction "all_business_transactions_list"

# Optionally list contents of the temp directory
ls -l ./temp
