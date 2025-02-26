import argparse
import json
import os

def print_pages_with_less_than_x_requests(file_path, number_of_requests=10):
    # remove the file pages_with_less_than_x_requests.json if it exists
    if os.path.exists('pages_with_less_than_' + str(number_of_requests) + '_requests.json'):
        os.remove('pages_with_less_than_' + str(number_of_requests) + '_requests.json')
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            for page in data.get('data', []):
                if page.get('totalNumberOfEndUserRequests', 0) < number_of_requests:
                    print(page)
                    # write addId to a file
                    with open('pages_with_less_than_' + str(number_of_requests) + '_requests.json', 'a') as output_file:
                        json.dump(page.get('addId'), output_file)
                        # add a new line to the file
                        output_file.write('\n')
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from the file {file_path}.")
    # convert the contents of pages_with_less_than_x_requests.json to a json list of integers
    pages_with_less_than_x_requests = []
    if os.path.exists('pages_with_less_than_' + str(number_of_requests) + '_requests.json'):
        with open('pages_with_less_than_' + str(number_of_requests) + '_requests.json', 'r') as file:
            pages_with_less_than_x_requests = file.readlines()
            try:
                pages_with_less_than_x_requests = [int(page.strip()) for page in pages_with_less_than_x_requests]
            except ValueError:
                print("Error converting page IDs to integers.")
    # output pages_with_less_than_' + str(number_of_requests) + '_requests to file
    with open('pages_with_less_than_' + str(number_of_requests) + '_requests.json', 'w') as file:
        json.dump(pages_with_less_than_x_requests, file)

def list_exclusion_values(file_path):
    out_file='./exclusion_values.txt'
    # remove the file pages_that_match_exclusions.json if it exists
    if os.path.exists(out_file):
        os.remove(out_file)
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            # json is in this format
            # [
            #   {
            #     "name": "kampyle.com",
            #     "matchOnMobileApplicationName": {
            #       "classType": "ajaxURLMatchCriteria",
            #       "type": null,
            #       "value": null,
            #       "httpMethods": null
            #     },
            #     "enabled": true,
            #     "priority": 0,
            #     "matchOnURL": {
            #       "classType": "ajaxURLMatchCriteria",
            #       "type": "CONTAINS",
            #       "value": "kampyle.com",
            #       "httpMethods": [
            #         "GET",
            #         "POST",
            #         "PUT",
            #         "DELETE"
            #       ]
            #     },

            # loop through each json object and get the value
            for exclusion in data:
                try:
                    print(exclusion.get('matchOnURL').get('value'))
                    with open(out_file, 'a') as output_file:
                        json.dump(exclusion.get('matchOnURL').get('value'), output_file)
                        # add a new line to the file
                        output_file.write('\n')
                except:
                    print(f"Error parsing exclusion {exclusion}")
    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from the file {file_path}.")

    return out_file

def print_pages_that_match_exclusions(file_path, pages_file_path):
    # remove the file pages_that_match_exclusions.json if it exists
    if os.path.exists('pages_that_match_exclusions.json'):
        os.remove('pages_that_match_exclusions.json')
    # get the exclusions
    exclusions = []
    with open(file_path, 'r') as file:
        exclusions = file.readlines()
        try:
            exclusions = [exclusion.strip() for exclusion in exclusions]
        except ValueError:
            print("Error converting page IDs to integers.")

    with open(pages_file_path, 'r') as file:
        data = json.load(file)
        for page in data.get('data', []):
            # check if anything in the exlcusions list is in the name
            for exclusion in exclusions:
                print(page.get('name'))
                # strip quotes from exclusion and print it
                print(exclusion.strip('\"'))
                if exclusion.strip('\"') in page.get('name'):
                    print(page)
                    # write addId to a file
                    with open('pages_that_match_exclusions.json', 'a') as output_file:
                        output_file.write(str(page.get('addId')))
                        # add a new line to the file
                        output_file.write('\n')
    
    # convert the contents of pages_that_match_exclusions.json to a json list of integers
    pages_that_match_exclusions = []
    if os.path.exists('pages_that_match_exclusions.json'):
        with open('pages_that_match_exclusions.json', 'r') as file:
            pages_that_match_exclusions = file.readlines()
            try:
                pages_that_match_exclusions = [int(page.strip()) for page in pages_that_match_exclusions]
            except ValueError:
                print("Error converting page IDs to integers.")
    
    # output pages_that_match_exclusions to file
    with open('pages_that_match_exclusions.json', 'w') as file:
        json.dump(pages_that_match_exclusions, file)
        
def extract_addid_from_mobile_network_requests(file_path):
    out_file = './NetworkRequests_Addid_TrafficZero.json'

    # Remove the existing output file if it exists
    if os.path.exists(out_file):
        os.remove(out_file)

    # List to collect all the addId values
    add_ids = []

    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            
            # Check if the JSON structure has the expected 'data' field
            if 'data' not in data:
                print("Error: 'data' field not found in the provided JSON.")
                return

            # Iterate over each entry in the 'data' and extract the 'addId'
            for entry in data.get('data', []):
                try:
                    addid = entry.get('addId')
                    if addid:
                        add_ids.append(addid)
                    else:
                        print("addId not found for an entry.")
                except Exception as e:
                    print(f"Error processing entry: {entry}. Error: {e}")

    except FileNotFoundError:
        print(f"The file {file_path} does not exist.")
    except json.JSONDecodeError:
        print(f"Error decoding JSON from the file {file_path}.")
    
    # Write the list of addIds to the output file in JSON array format
    with open(out_file, 'w') as output_file:
        json.dump(add_ids, output_file)

    return out_file
    
# parse arguments
parser = argparse.ArgumentParser(description='Print pages with less than x requests.')
parser.add_argument('--debug', action='store_true', help='Print debug information.')
# add a positional argument for the command name
subparsers = parser.add_subparsers(required=True, dest='command')
parser_filter_by_requests = subparsers.add_parser('filter_by_requests', help='Filter pages by number of requests.')
parser_filter_by_requests.add_argument('--file_path', type=str, help='The path to the file to read.', default='./pageList.json')
parser_filter_by_requests.add_argument('--number_of_requests', type=int, help='The number of requests to compare against.', default=3)
parser_list_pages_that_match_exclusions = subparsers.add_parser('list_pages_that_match_exclusions', help='List pages that match exclusions.')
parser_list_pages_that_match_exclusions.add_argument('--exclusions-file_path', type=str, help='The path to the file to read for exclusions.', default='./customNamingExcludeRules.json')
parser_list_pages_that_match_exclusions.add_argument('--pages-file-path', type=str, help='The path to the file to read for pages.', default='./pageList.json')
parser_extract_addid = subparsers.add_parser('extract_addid', help='Extract addId values from mobile network request list.')
parser_extract_addid.add_argument('--file_path', type=str, help='The path to the mobile network request JSON file.', default='./mobile_network_request_list.json')
args = parser.parse_args()
#customNamingExcludeRules.json

# if filter_by_requests is in the arguments, call print_pages_with_less_than_x_requests
if args.command == 'filter_by_requests':
    print_pages_with_less_than_x_requests(args.file_path, args.number_of_requests)
elif args.command == 'list_pages_that_match_exclusions':
    out_file = list_exclusion_values(args.exclusions_file_path)
    print_pages_that_match_exclusions(out_file, args.pages_file_path)
elif args.command == 'extract_addid':
    out_file = extract_addid_from_mobile_network_requests(args.file_path)
    print(f"Extracted the 'addId' values where their 'totalRequests' is '0' and saved to: {out_file}")
