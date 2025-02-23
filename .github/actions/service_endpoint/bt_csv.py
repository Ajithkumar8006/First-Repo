import json
import csv

# Function to read JSON data and write it into a CSV file
def json_to_csv(json_file, csv_file):
    # Open and load JSON data from the file
    with open(json_file, 'r') as f:
        data = json.load(f)

    # Extract the keys (headers) for the CSV file from the first item
    headers = data[0].keys()

    # Open CSV file in write mode and create a CSV writer object
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)

        # Write the headers to the CSV file
        writer.writeheader()

        # Write the rows from the JSON data to the CSV file
        writer.writerows(data)

    print(f"Data has been written to {csv_file}")

# Example usage
json_file = 'bt.json'  # Path to your JSON file
csv_file = './temp/bt.csv'    # Desired output CSV file

# Call the function to convert JSON to CSV
json_to_csv(json_file, csv_file)
