#!/bin/bash

# Ensure all required variables are set
if [ -z "$CRED_FILE" ]; then
  echo "Error: CRED_FILE is not set!"
  exit 1
fi

if [ -z "$APP_NAME" ]; then
  echo "Error: APP_NAME is not set!"
  exit 1
fi

if [ -z "$TRANSACTION_NAME" ]; then
  echo "Error: TRANSACTION_NAME is not set!"
  exit 1
fi

# Run the Python script with the provided parameters
echo "Running AppDynamics API script for app: $APP_NAME with transaction: $TRANSACTION_NAME..."

python appdynamics_api.py --cred "$CRED_FILE" --debug "$DEBUG_LEVEL" --output "$OUTPUT_FORMAT" --app "$APP_NAME" "$TRANSACTION_NAME"

python appdynamics_api.py --cred credentials.ini --debug 5 --output json --app "Patient_Online_Services_Portal_Test"   all_business_transactions_list
