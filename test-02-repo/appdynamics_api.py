#!/usr/bin/env python3

import os
import shutil
import sys
import getopt
import platform
import subprocess
import argparse
import errno
#import monsollib
import configparser
import datetime
from enum import Enum
import requests
import urllib3
import json
import csv
from dateutil import relativedelta

# or if this does not work with the previous import:
# from requests.packages import urllib3  

# Suppress only the single warning from urllib3.
urllib3.disable_warnings(category=urllib3.exceptions.InsecureRequestWarning)

eventtypelist = [
    "ACTIVITY_TRACE",
#    "ADJUDICATION_CANCELLED",
#    "AGENT_ADD_BLACKLIST_REG_LIMIT_REACHED",
#    "AGENT_ASYNC_ADD_REG_LIMIT_REACHED",
    "AGENT_CONFIGURATION_ERROR",
    "APPLICATION_CRASH",
#    "AGENT_DIAGNOSTICS",
#    "AGENT_ERROR_ADD_REG_LIMIT_REACHED",
    "AGENT_EVENT",
#    "AGENT_METRIC_BLACKLIST_REG_LIMIT_REACHED",
#    "AGENT_METRIC_REG_LIMIT_REACHED",
    "AGENT_STATUS",
#    "ALREADY_ADJUDICATED",
#    "APPDYNAMICS_DATA",
#    "APPDYNAMICS_INTERNAL_DIAGNOSTICS",
    "APPLICATION_CONFIG_CHANGE",
    "APPLICATION_DEPLOYMENT",
    "APPLICATION_DISCOVERED",
    "APPLICATION_ERROR",
    "APP_SERVER_RESTART",
#    "AZURE_AUTO_SCALING",
    "BACKEND_DISCOVERED",
#    "BT_DISCOVERED",
    "BUSINESS_ERROR",
    "CLR_CRASH",
#    "CONTROLLER_AGENT_VERSION_INCOMPATIBILITY",
#    "CONTROLLER_ASYNC_ADD_REG_LIMIT_REACHED",
#    "CONTROLLER_COLLECTIONS_ADD_REG_LIMIT_REACHED",
#    "CONTROLLER_ERROR_ADD_REG_LIMIT_REACHED",
#    "CONTROLLER_EVENT_UPLOAD_LIMIT_REACHED",
#    "CONTROLLER_MEMORY_ADD_REG_LIMIT_REACHED",
#    "CONTROLLER_METADATA_REGISTRATION_LIMIT_REACHED",
#    "CONTROLLER_METRIC_DATA_BUFFER_OVERFLOW",
#    "CONTROLLER_METRIC_REG_LIMIT_REACHED",
#    "CONTROLLER_PSD_UPLOAD_LIMIT_REACHED",
#    "CONTROLLER_RSD_UPLOAD_LIMIT_REACHED",
#    "CONTROLLER_SEP_ADD_REG_LIMIT_REACHED",
#    "CONTROLLER_STACKTRACE_ADD_REG_LIMIT_REACHED",
#    "CONTROLLER_TRACKED_OBJECT_ADD_REG_LIMIT_REACHED",
    "CUSTOM",
    "CUSTOM_ACTION_END",
    "CUSTOM_ACTION_FAILED",
    "CUSTOM_ACTION_STARTED",
    "CUSTOM_EMAIL_ACTION_END",
    "CUSTOM_EMAIL_ACTION_FAILED",
    "CUSTOM_EMAIL_ACTION_STARTED",
#    "DB_SERVER_PARAMETER_CHANGE",
    "DEADLOCK",
#    "DEV_MODE_CONFIG_UPDATE",
#    "DIAGNOSTIC_SESSION",
    "DISK_SPACE",
    "EMAIL_ACTION_FAILED",
#    "EMAIL_SENT",
#    "EUM_CLOUD_BROWSER_EVENT",
#    "EUM_CLOUD_SYNTHETIC_BROWSER_EVENT",
#    "EUM_INTERNAL_ERROR",
#    "HTTP_REQUEST_ACTION_END",
#    "HTTP_REQUEST_ACTION_FAILED",
    "HTTP_REQUEST_ACTION_STARTED",
#    "INFO_INSTRUMENTATION_VISIBILITY",
#    "INTERNAL_UI_EVENT",
#    "JIRA_ACTION_END",
#    "JIRA_ACTION_FAILED",
#    "JIRA_ACTION_STARTED",
#    "LICENSE",
#    "MACHINE_AGENT_LOG",
#    "MACHINE_DISCOVERED",
    "MEMORY",
#    "MEMORY_LEAK_DIAGNOSTICS",
#    "MOBILE_CRASH_IOS_EVENT",
#    "MOBILE_CRASH_ANDROID_EVENT",
    "NETWORK",
    "NODE_DISCOVERED",
#    "NORMAL",
#    "OBJECT_CONTENT_SUMMARY",
#    "POLICY_CANCELED_CRITICAL",
#    "POLICY_CANCELED_WARNING",
#    "POLICY_CLOSE_CRITICAL",
#    "POLICY_CLOSE_WARNING",
#    "POLICY_CONTINUES_CRITICAL",
#    "POLICY_CONTINUES_WARNING",
#    "POLICY_DOWNGRADED",
    "POLICY_OPEN_CRITICAL",
    "POLICY_OPEN_WARNING",
    "POLICY_UPGRADED",
    "RESOURCE_POOL_LIMIT",
#    "RUNBOOK_DIAGNOSTIC SESSION_END",
#    "RUNBOOK_DIAGNOSTIC SESSION_FAILED",
#    "RUNBOOK_DIAGNOSTIC SESSION_STARTED",
#    "RUN_LOCAL_SCRIPT_ACTION_END",
#    "RUN_LOCAL_SCRIPT_ACTION_FAILED",
#    "RUN_LOCAL_SCRIPT_ACTION_STARTED",
#    "SERVICE_ENDPOINT_DISCOVERED",
    "SLOW",
    "SMS_SENT",
    "STALL",
    "SYSTEM_LOG",
#    "THREAD_DUMP_ACTION_END",
#    "THREAD_DUMP_ACTION_FAILED",
#    "THREAD_DUMP_ACTION_STARTED",
    "TIER_DISCOVERED",
    "VERY_SLOW"
#    "WARROOM_NOTE",
]

class CallType(Enum):
    GET = "GET"
    PUT = "PUT"
    POST = "POST"
    CLASS = "CLASS"
class AuthType(Enum):
    BASIC = "BASIC"
    OAUTH = "OAUTH"
class ReturnType(Enum):
    JSON = "JSON"
    XML = "XML"
    TEXT = "TEXT"
class OutputFormat(Enum):
    TEXT = "TEXT"
    JSON = "JSON"
    CSV = "CSV"
    XML = "XML"

timeparams = {
    "startdate": "",
    "enddate": "",
    "startepochsecs": "",
    "startepochmillies": "",
    "endepochsecs": "",
    "endepochmillies": "",
    "durationinmins": "",
}
options = {"outputformat": OutputFormat.TEXT}
debuglevel = 0
ApplicationList = None

def DEBUGOUT (level, message, args):
    if debuglevel >= level:
        if not args:
            print (message)
        else:
            print (message % args)

class Authentication:
    credinfo = {}
    authinfo = {}

    def __init__ (self, credinfo):
        self.credinfo = credinfo

    def initoauth(self):
        if not "token" in self.authinfo:
            DEBUGOUT (7, "initoauth: Getting Token with client %s", (credinfo["clientsecret"]))
        url = self.credinfo['hosturl'] + self.credinfo['authuri']
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {"grant_type": "client_credentials",
                   "client_id": credinfo['username'],
                   "client_secret": credinfo['clientsecret']}

        DEBUGOUT (9, "initoauth: Sending OAuth request: url: %s headers: %s data %s", (url, str(headers), str(payload)))
        result = requests.post (url, headers=headers, data=payload, verify=False)

        DEBUGOUT (9, "initoauth: OAuth result:%s", (str(result)))
        if not result.ok:
            print ("oauth request result: " + str(result) + " " + result.reason)
            exit (1)

        jsondata = result.json()
        self.authinfo['token'] = jsondata['access_token']

        return self.authinfo['token']

#
# Base class for doing an API call, parsing and outputting the result
#
# Use in combination with the array 'commandlist'.
#
# For "simple" commands, this base class will implement with no further modifications.
# For "complex" operations, some of the methods of this class may need to be overridden.  Often the "parse_results" method.
# Simple in this case means:
#
#   * A basic HTTP GET api call, which returns JSON
#   * The returned JSON has a top level array, with each array object being a simple JSON object containing no sub-arrays
#     OR
#   * returns a blob of XML or JSON to be output as a blob with no formatting

class API_Call:
    flags = {}      # flag for each URI placeholder var needed, e.g. "needs_appid", "needs_account", "needs_tier"
    uri = ""        # URI, with placeholders for e.g. {appid}
    calltype = CallType.GET      # Should be CallType.GET or CallType.POST
    authtype = AuthType.OAUTH    # Should be AuthType.BASIC or AuthType.OAUTH
    authentication = {}          # If OAUTH, object with session token, etc
    credinfo = {}
    callresult = {}
    commandinfo = {}
    returntype = ReturnType.JSON
    params = {'accountid': "", 'appid': "", 'appname': "", 'tiername': "", 'entityname': "", 'mobileappid': ""}
    
    def __init__ (self, commandinfo, credinfo, options, ApplicationList):

        DEBUGOUT (4, "API_Call:__init__: command %s", {commandinfo['uri']})

        self.commandinfo = commandinfo
        self.calltype = commandinfo['type']
        # self.authtype =
        if "authtype" in commandinfo:
            self.authtype = commandinfo['authtype']
        if "returntype" in commandinfo:
            self.returntype = commandinfo['returntype']
        else:
            commandinfo['returntype'] = ReturnType.JSON
            self.returntype = ReturnType.JSON
        self.credinfo = credinfo
        # self.globals = globals
        self.options = options

        self.authentication = Authentication (credinfo)
        if self.authtype == AuthType.OAUTH:
            self.authentication.initoauth()

        if "application" in options:
            self.params['appname'] = options['application']

        if "flags" in commandinfo:
            commandflags = commandinfo["flags"]
            if "needs_appid" in commandflags:
                self.params['appid'] = ApplicationList.get_appid_by_name (options['application'])
                DEBUGOUT (6, "API_call.__init__: appname %s getting appid %d", (self.params['appname'], self.params['appid']))
                if self.params['appid'] == -1:
                    print ("Application name " + self.params['appname'] + " not found")
                    print (usage)
                    exit (1)
            if "needs_accountid" in commandflags:
                commandinfo = commandlist['myaccount']
                accountinfo = commandinfo['Class'](commandinfo, credinfo, options, ApplicationList)
                self.params['accountid'] = accountinfo.get_accountid()
            if "needs_tiername" in commandflags:
                self.params['tiername'] = options['tier']
            if "needs_entity" in commandflags:
                if not "entityname" in options:
                    print ("Requires entity name --entity")
                    print (usage)
                    exit (1)
                self.params['entityname'] = options['entityname']
            if "needs_mobileappid" in commandflags:
                try:
                    self.params['mobileappid'] = options['mobileappid']
                except:
                    print ("Requires mobile app id --mobileappid\n\nFind the app ID by navigating to the UI getting it from the URL\n\n")
                    print (usage)
                    exit (1)
            if "needs_input_file" in commandflags:
                try:
                    self.params['inputfile'] = options['inputfile']
                except:
                    print ("Requires input file --inputfile\n\n")
                    print (usage)
                    exit (1)

    def get_headers (self):

        global options
        headers = []
        
        headers = self.commandinfo["headers"]

        return headers
                
    def get_resultrow_lens (self, result_table):

        resultrowlensbyheader = {}
        
        for resulttextrow in result_table:
            resultcounter = 0
            for header in self.get_headers():
                datum = ""
                if resultcounter < len (resulttextrow):
                    datum = str(resulttextrow[resultcounter])

                if not header in resultrowlensbyheader:
                    resultrowlensbyheader[header] = len(datum)
                elif len(datum) > resultrowlensbyheader[header]:
                    resultrowlensbyheader[header] = len(datum)
                resultcounter = resultcounter+1

        return resultrowlensbyheader
            
    def str_table (self, result):
        DEBUGOUT (4, "print_table:", ())

        sep = " | "
        frmt = "%s-0%ds"
        resulttext = ""
        resultrowlens = []

        resultrowlensbyheader = self.get_resultrow_lens (result)

        for header in self.get_headers():
            resultrowlens.append(frmt % ('%', resultrowlensbyheader[header]))

        formatstr = sep.join (resultrowlens)

        for resulttextrow in result:
            if len (resulttextrow) > 0:
                DEBUGOUT (7, "Applications.__str__: %s", (str(resulttextrow)))
                rowtext = formatstr % tuple(resulttextrow)
                resulttext = resulttext + rowtext + '\n'

        return resulttext

    def str_csv (self, result):
        DEBUGOUT (4, "print_csv:", ())

        sep = ","
        frmt = "%s"
        resulttext = ""
        resultrowlens = []

        resultrowlensbyheader = self.get_resultrow_lens (result)

        for header in self.get_headers():
            resultrowlens.append(frmt)

        formatstr = sep.join (resultrowlens)

        for resulttextrow in result:
            if len (resulttextrow) > 0:
                DEBUGOUT (7, "Applications.__str__: %s", (str(resulttextrow)))
                rowtext = formatstr % tuple(resulttextrow)
                resulttext = resulttext + rowtext + '\n'

        return resulttext
                
    def str_other (self, result):
        DEBUGOUT (4, "print_other:", ())

        resulttext = result.replace('\\n', '\n')
        return resulttext

    def __str__ (self):
        DEBUGOUT (4, "__str__:", ())
        resulttext = ""

        result = self.parse_results ()
        
        if self.options['outputformat'] == OutputFormat.TEXT:
            if "headers" in self.commandinfo:
                resulttext = self.str_table(result)
            else:
                resulttext = self.str_other(result)
        elif self.options['outputformat'] == OutputFormat.CSV:
            resulttext = self.str_csv(result)
        elif self.options['outputformat'] == OutputFormat.JSON:
            resulttext = json.dumps(self.callresult.json(), indent=4) #str (self.callresult.content)
        else:
            print ("Unknown output format")
            exit (1)

        return resulttext

    def expandvars (self, inputstring):
        global timeparams
        DEBUGOUT (6, "expandvars:", [str(inputstring)])

        account = self.params['accountid']
        appid = self.params['appid']
        appname = self.params['appname']
        tiername = self.params['tiername']
        accountid = self.params['accountid']
        entityname = self.params['entityname']

        startdate = timeparams['startdate']
        enddate = timeparams['enddate']
        startepochsecs = timeparams['startepochsecs']
        startepochmillies = timeparams['startepochmillies']
        durationinmins = timeparams['durationinmins']
        
        outputstring = inputstring.format(**locals())        
        #url = url.format(**globals())

        DEBUGOUT (5, "expandvars: %s", {outputstring})
        
        return outputstring
        
    def urlparse (self, url, uri):
        DEBUGOUT (5, "urlparse:", ())

        url = url + self.expandvars(uri) #requests.utils.quote (uri)

        DEBUGOUT (4, "urlparse: Parsed URL: %s", {url})
        
        return url
    
    def sendcall (self, params):
        result = {}
        url = self.urlparse (self.credinfo['hosturl'], self.commandinfo['uri'])
        headers = {}
        
        DEBUGOUT (3, "sendcall: method %s authtype %s calling %s", (self.calltype, self.authtype, url))

        request = requests.Session()
        if self.authtype == AuthType.BASIC:
            request.auth (self.credinfo['username'], self.credinfo['password'])
        else:
            headers = {'Authorization': 'Bearer ' + self.authentication.authinfo['token']}

        if self.calltype == CallType.GET:
            result = requests.get (url, headers=headers, verify=False)
        elif self.calltype == CallType.POST:
            payload = {}
            if "payload" in self.commandinfo:
                payload = self.expandvars(self.commandinfo['payload'])
            result = requests.post (url, headers=headers, json=payload, verify=False)
        elif self.calltype == CallType.PUT:
            payload = {}
            if "payload" in self.commandinfo:
                payload = self.expandvars(self.commandinfo['payload'])
            result = requests.put (url, headers=headers, json=payload, verify=False)

        if not result.ok:
            print ("query " + url + " result: " + str(result) + " " + result.reason)
            if not "allapmapps" in self.options:
                exit (1)
        else:
            print(result.text)
        DEBUGOUT (8, "sendcall result: %s", (result.text))
        
        self.callresult = result
        return result

    def parse_results (self):
        DEBUGOUT (4, "parse_results:", ())

        global options
        result = {}
        result_table = []

        if "headers" in self.commandinfo:
            result_table = [self.get_headers()]

        if not self.callresult.ok:
            return result

        if self.returntype == ReturnType.JSON:
            if self.options['outputformat'] == OutputFormat.TEXT or self.options['outputformat'] == OutputFormat.CSV:
                resultarray = self.callresult.json()
                for entry in resultarray:
                    thisrecord = []
                    for header in self.get_headers():
                        if header in entry:
                            thisrecord.append(entry[header])
                        else:
                            thisrecord.append("")
                    result_table.append(thisrecord)
                result = result_table
            else:
                if self.callresult.text and self.callresult.text.strip():
               	    result = str (self.callresult.json())

        else:
            result = str (self.callresult.content)

        return result

    def add_app_results (self, appname, results):
        DEBUGOUT (4, "add_app_results: app %s", {appname})

        for row in results:
            row.insert(appname)

        self.allresults.update(results)

class Applications(API_Call):

    applicationlist = None
    apmapplicationlist = None
    
    def __init__ (self, commandinfo, credinfo, options, ApplicationList):
        super().__init__ (commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET

    def parse_sub_results (self, type, resultarray):
        DEBUGOUT (5, "Applications.parse_sub_results (%s)", (type))

        result = {}
        result_table = []

        if len(resultarray) == 0 or resultarray[0] == None:
            return result_table
        
        for entry in resultarray:
            thisresult = []
            for header in self.get_headers():
                datum = ""
                if header == "type":
                    datum = entry['applicationTypeInfo']['applicationTypes'][0]
                elif header == "createdOn" or header == "modifiedOn":
                    datum = datetime.datetime.fromtimestamp(entry[header] / 1000).strftime('%Y-%m-%d %H:%M:%S.%f %Z')
                else:
                    datum = entry[header]
                thisresult.append(str(datum))
            result_table.append (thisresult)

        rowlength = 0
        if len(result_table) > 0:
            rowlength = len(result_table[0])

        DEBUGOUT (6, "Applications.parse_sub_results: %d results row len %d", (len(result_table), rowlength))
        return result_table

    def parse_results (self):
        DEBUGOUT (4, "Applications.parse_results:", ())

        result_table = [self.get_headers()]

        rows = self.parse_sub_results ("apm", self.callresult.json()["apmApplications"])
        if (len(rows) > 0):
            result_table = result_table + rows
        rows = self.parse_sub_results ("eumWeb", self.callresult.json()["eumWebApplications"])
        if (len(rows) > 0):
            result_table = result_table + rows
        rows = self.parse_sub_results ("dbMon", [self.callresult.json()["dbMonApplication"]])
        if (len(rows) > 0):
            result_table = result_table + rows
        rows = self.parse_sub_results ("overage", [self.callresult.json()["overageMonitoringApplication"]])
        if (len(rows) > 0):
            result_table = result_table + rows
        rows = self.parse_sub_results ("sim", [self.callresult.json()["simApplication"]])
        if (len(rows) > 0):
            result_table = result_table + rows
        rows = self.parse_sub_results ("analytics", [self.callresult.json()["analyticsApplication"]])
        if (len(rows) > 0):
            result_table = result_table + rows
        rows = self.parse_sub_results ("mobile", self.callresult.json()["mobileAppContainers"])
        if (len(rows) > 0):
            result_table = result_table + rows
        rows = self.parse_sub_results ("iot", self.callresult.json()["iotApplications"])
        if (len(rows) > 0):
            result_table = result_table + rows
        rows = self.parse_sub_results ("cloudMonitoring", [self.callresult.json()["cloudMonitoringApplication"]])
        if (len(rows) > 0):
            result_table = result_table + rows
        rows = self.parse_sub_results ("apiMonitoring", self.callresult.json()["apiMonitoringApplications"])
        if (len(rows) > 0):
            result_table = result_table + rows
        #rows = self.parse_sub_results ("coreWebVitals", [self.callresult.json()["coreWebVitalsApplication"]])
        #if (len(rows) > 0):
        #    result_table = result_table + rows

        return result_table
            
    def __str__ (self):
        DEBUGOUT (4, "Applications:__str__:", ())
        resulttext = ""
        result = self.parse_results()

        if self.options['outputformat'] == OutputFormat.TEXT:
            resulttext = self.str_table(result)
        elif self.options['outputformat'] == OutputFormat.JSON:
            resulttext = json.dumps(self.callresult.json(), indent=4) #str (self.callresult.content
        elif self.options['outputformat'] == OutputFormat.CSV:
            resulttext = self.str_csv(result)
        else:
            print ("Unknown output format")
            exit (1)

        return resulttext

    def applist_to_dict (self, applist, section):
        appdict = {}

        if section in applist:
            if not applist[section] is None and "id" in applist[section]:
                appdict[applist[section]['name']] = applist[section]
            elif hasattr(applist[section], "__len__"):
                if len(applist[section]) > 0 and applist[section] != None:
                    for app in applist[section]:
                        appdict[app['name']] = app

        return appdict

    def get_all_appids (self):
        if not self.callresult:
            self.sendcall ({})

        if self.applicationlist == None:

            self.applicationlist = {}
            
            applist = self.callresult.json()

            sections = ['cloudMonitoringApplication',
                        'analyticsApplication',
                        'simApplication',
                        'overageMonitoringApplication',
                        'dbMonApplication',
                        'apmApplications',
                        'eumWebApplications',
                        'mobileAppContainers',
                        'iotApplications',
                        'apiMonitoringApplications']

            for section in sections:
                self.applicationlist.update (self.applist_to_dict (applist, section))

        return self.applicationlist

    def get_all_apmappids (self):
        if not self.callresult:
            self.sendcall ({})

        if self.apmapplicationlist == None:

            self.apmapplicationlist = {}

            applist = self.callresult.json()

            sections = ['apmApplications']

            for section in sections:
                self.apmapplicationlist.update (self.applist_to_dict (applist, section))
                
        return self.apmapplicationlist

    def get_apmappid_by_name (self, appname):
        if not self.callresult:
            self.sendcall ({})

        self.get_all_apmappids()

        return self.apmapplicationlist[appname]['id']

    def get_appid_by_name (self, appname):
        if not self.callresult:
            self.sendcall ({})

        self.get_all_appids()

        return self.applicationlist[appname]['id']
	    
class OutputFormat:
    JSON = 'json'
    TEXT = 'text'
    CSV = 'csv'  # Add the CSV option

class MobileNetworkRequestList(API_Call): 
    
    def __init__(self, commandinfo, credinfo, options, ApplicationList):
        super().__init__(commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.POST

    def parse_results(self):
        result = self.callresult.content
        return result

    def expandvars(self, inputstring):
        # Check if inputstring is a string or json
        if isinstance(inputstring, str):
            global timeparams
            DEBUGOUT(6, "expandvars:", [str(inputstring)])

            account = self.params['accountid']
            appid = self.params['appid']
            appname = self.params['appname']
            tiername = self.params['tiername']
            accountid = self.params['accountid']
            entityname = self.params['entityname']

            startdate = timeparams['startdate']
            enddate = timeparams['enddate']
            startepochsecs = timeparams['startepochsecs']
            startepochmillies = timeparams['startepochmillies']
            durationinmins = timeparams['durationinmins']

            outputstring = inputstring.format(**locals())
            DEBUGOUT(5, "expandvars: %s", [outputstring])
            return outputstring
        
        elif isinstance(inputstring, dict):
            outputstring = inputstring
            outputstring['requestFilter']['applicationId'] = self.params['appid']
            outputstring['requestFilter']['mobileApplicationId'] = self.params['mobileappid']
            DEBUGOUT(5, "expandvars: " + str(outputstring), None)
            return outputstring

    def __str__(self):
        DEBUGOUT(4, "Applications:__str__:", ())

        resulttext = ""
        result = self.parse_results()

        # Handle output format JSON
        if self.options['outputformat'] == OutputFormat.JSON:
            json_data = self.callresult.json()
            resulttext = json.dumps(json_data, indent=4)

            # Try to save the JSON data into a file
            try:
                with open('mobile_network_request_list.json', 'w') as f:
                    json.dump(json_data, f, indent=4)
                    print("JSON file 'mobile_network_request_list.json' has been created successfully.")
            except Exception as e:
                print(f"Error occurred while writing JSON file: {e}")
                return ""

            # Call the method to save separate JSON files
            self.save_separate_json_files('mobile_network_request_list.json')

        else:
            print("Error: Data is not in the expected format for JSON.")
            return ""

        return resulttext

    def save_separate_json_files(self, input_file):
        """ Extract and save data from the JSON to separate JSON files. """
        try:
            with open(input_file, 'r') as file:
                data = json.load(file)

            # Assuming the key 'data' holds the list of network requests
            if "data" not in data:
                raise ValueError("The JSON does not contain the 'data' key.")
            
            network_requests = data["data"]

            # Check if the list is empty
            if not network_requests:
                print("The 'data' list is empty.")
                return

            # Define the CSV output file path
            csv_file = "Networkrequest_Name_Addid_Traffic.csv"
            fieldnames = ["name", "totalRequests", "addId"]

            # Write the selected data to the CSV file
            try:
                with open(csv_file, mode='w', newline='') as file:
                    writer = csv.DictWriter(file, fieldnames=fieldnames)

                    # Write the header row
                    writer.writeheader()

                    # Write the selected data rows
                    for entry in network_requests:
                        # Select only the fields "name", "totalRequests", and "addId"
                        filtered_entry = {key: entry[key] for key in fieldnames if key in entry}
                        writer.writerow(filtered_entry)

                print(f"CSV file '{csv_file}' has been created successfully.")

            except Exception as e:
                print(f"An error occurred while writing the CSV: {e}")
                return ""

        except json.JSONDecodeError:
            print("Error decoding JSON. Please check the JSON file format.")
        except FileNotFoundError:
            print(f"The file '{input_file}' was not found.")
        except ValueError as e:
            print(e)
	
class PageList(API_Call):
        
    def __init__(self, commandinfo, credinfo, options, ApplicationList):
        super().__init__(commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.POST

    def parse_results(self):
        result = self.callresult.content
        return result

    def expandvars(self, inputstring):
        if isinstance(inputstring, str):
            global timeparams
            DEBUGOUT(6, "expandvars:", [str(inputstring)])

            account = self.params['accountid']
            appid = self.params['appid']
            appname = self.params['appname']
            tiername = self.params['tiername']
            accountid = self.params['accountid']
            entityname = self.params['entityname']
            startdate = timeparams['startdate']
            enddate = timeparams['enddate']
            startepochsecs = timeparams['startepochsecs']
            startepochmillies = timeparams['startepochmillies']
            durationinmins = timeparams['durationinmins']

            outputstring = inputstring.format(**locals())
            DEBUGOUT(5, "expandvars: %s", {outputstring})
        elif isinstance(inputstring, dict):
            outputstring = inputstring
            outputstring['timeRangeStart'] = timeparams['startepochmillies']
            outputstring['timeRangeEnd'] = timeparams['endepochmillies']
            outputstring['requestFilter']['applicationId'] = self.params['appid']
            # outputstring['requestFilter']['mobileApplicationId'] = self.params['mobileappid']
            DEBUGOUT(5, "expandvars: " + str(outputstring), None)
        return outputstring

    def __str__(self):
        DEBUGOUT(4, "Applications:__str__:", ())
        resulttext = ""
        result = self.parse_results()

        if self.options['outputformat'] == OutputFormat.JSON:
            resulttext = json.dumps(self.callresult.json(), indent=4)
            # Save the full API result to a JSON file
            with open('pageList.json', 'w') as f:
                json.dump(self.callresult.json(), f, indent=4)

            # After saving the JSON, extract and save separate JSON files for Exclude and Include Rules
            # self.save_separate_json_files('pageList.json')
        else:
            print("Error: Data is not in the expected format for json")
            return ""

        return resulttext

class PageListExcludeRequests(API_Call):
        
    def __init__(self, commandinfo, credinfo, options, ApplicationList):
        super().__init__(commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.POST

    def parse_results(self):
        result = self.callresult.content
        return result

    def expandvars(self, inputstring):
        outputstring = inputstring
        if isinstance(inputstring, str):
            global timeparams

            account = self.params['accountid']
            appid = self.params['appid']
            appname = self.params['appname']
            tiername = self.params['tiername']
            accountid = self.params['accountid']
            entityname = self.params['entityname']
            startdate = timeparams['startdate']
            enddate = timeparams['enddate']
            startepochsecs = timeparams['startepochsecs']
            startepochmillies = timeparams['startepochmillies']
            durationinmins = timeparams['durationinmins']

            outputstring = inputstring.format(**locals())
            DEBUGOUT(5, "expandvars: %s", {outputstring})
        elif isinstance(inputstring, dict):
            outputstring = inputstring
            outputstring['timeRangeStart'] = timeparams['startepochmillies']
            outputstring['timeRangeEnd'] = timeparams['endepochmillies']
            outputstring['requestFilter']['applicationId'] = self.params['appid']
            # outputstring['requestFilter']['mobileApplicationId'] = self.params['mobileappid']
            DEBUGOUT(5, "expandvars: " + str(outputstring), None)
        elif isinstance(inputstring, list):
            # read in the inputfile
            with open(self.params['inputfile'], 'r') as file:
                data = json.load(file)
                outputstring = data

        return outputstring

    def __str__(self):
        DEBUGOUT(4, "Applications:__str__:", ())
        resulttext = ""
        result = self.parse_results()

        if self.options['outputformat'] == OutputFormat.JSON:
            resulttext = json.dumps(self.callresult.json(), indent=4)
            # Save the full API result to a JSON file
            with open('pageListExcludeRequests.json', 'w') as f:
                json.dump(self.callresult.json(), f, indent=4)

            # After saving the JSON, extract and save separate JSON files for Exclude and Include Rules
            # self.save_separate_json_files('pageListExcludeRequests.json')
        else:
            print("Error: Data is not in the expected format for json")
            return ""

        return resulttext

class BrowserRUMConfig_Exclude_Include_List(API_Call):
        
        def __init__(self, commandinfo, credinfo, options, ApplicationList):
            super().__init__(commandinfo, credinfo, options, ApplicationList)
            self.calltype = CallType.GET
    
        def parse_results(self):
            result = self.callresult.content
            return result
    
        def expandvars(self, inputstring):
            if isinstance(inputstring, str):
                global timeparams
                DEBUGOUT(6, "expandvars:", [str(inputstring)])
    
                account = self.params['accountid']
                appid = self.params['appid']
                appname = self.params['appname']
                tiername = self.params['tiername']
                accountid = self.params['accountid']
                entityname = self.params['entityname']
                startdate = timeparams['startdate']
                enddate = timeparams['enddate']
                startepochsecs = timeparams['startepochsecs']
                startepochmillies = timeparams['startepochmillies']
                durationinmins = timeparams['durationinmins']
    
                outputstring = inputstring.format(**locals())
                DEBUGOUT(5, "expandvars: %s", {outputstring})
            elif isinstance(inputstring, dict):
                outputstring = inputstring
                outputstring['requestFilter']['applicationId'] = self.params['appid']
                outputstring['requestFilter']['mobileApplicationId'] = self.params['mobileappid']
                DEBUGOUT(5, "expandvars: " + str(outputstring), None)
            return outputstring
    
        def __str__(self):
            DEBUGOUT(4, "Applications:__str__:", ())
            resulttext = ""
            result = self.parse_results()
    
            if self.options['outputformat'] == OutputFormat.JSON:
                resulttext = json.dumps(self.callresult.json(), indent=4)
                # Save the full API result to a JSON file
                with open('browserRUMConfig_Exclude_Include_List.json', 'w') as f:
                    json.dump(self.callresult.json(), f, indent=4)
    
                # After saving the JSON, extract and save separate JSON files for Exclude and Include Rules
                self.save_separate_json_files('browserRUMConfig_Exclude_Include_List.json')
            else:
                print("Error: Data is not in the expected format for json")
                return ""
    
            return resulttext
    
        def save_separate_json_files(self, input_file):
            """ Extract and save customNamingExcludeRules and customNamingIncludeRules to separate JSON files. """
            with open(input_file, 'r') as file:
                data = json.load(file)
    
            # Extract Exclude and Include Rules
            exclude_rules = data.get('customNamingExcludeRules', [])
            include_rules = data.get('customNamingIncludeRules', [])
    
            # Save exclude rules to a separate JSON file
            with open('customNamingExcludeRules.json', 'w') as f:
                json.dump(exclude_rules, f, indent=4)
            print(f"customNamingExcludeRules saved to 'customNamingExcludeRules.json'.")
    
            # Save include rules to a separate JSON file
            with open('customNamingIncludeRules.json', 'w') as f:
                json.dump(include_rules, f, indent=4)
            print(f"customNamingIncludeRules saved to 'customNamingIncludeRules.json'.")
            
            # After saving the separate JSON files for Exclude Rules, convert Exclude Rules to CSV
            self.process_json_to_csv('customNamingExcludeRules.json', 'customNamingExcludeRules.csv')

        def process_json_to_csv(self, input_file, output_file):
            """ Convert extracted JSON data for Exclude Rules to CSV. """
            with open(input_file, 'r') as file:
                data = json.load(file)
    
            csv_data = []
            for rule in data:
                name = rule.get('name')
                match_url_value = rule.get('matchOnURL', {}).get('value', '')
                if name and match_url_value:
                    csv_data.append([name, match_url_value])
    
            with open(output_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(['name', 'value'])
                writer.writerows(csv_data)
    
            print(f"CSV file '{output_file}' has been created.")

class All_Business_Transactions_List(API_Call):

    def __init__(self, commandinfo, credinfo, options, ApplicationList):
        super().__init__(commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET 

    def parse_results(self):
        result = self.callresult.content
        return result

    def expandvars(self, inputstring):
        # Check if inputstring is a string or dictionary
        if isinstance(inputstring, str):
            global timeparams
            DEBUGOUT(6, "expandvars:", [str(inputstring)])

            account = self.params.get('accountid', '')
            appid = self.params.get('appid', '')
            appname = self.params.get('appname', '')
            tiername = self.params.get('tiername', '')
            entityname = self.params.get('entityname', '')

            startdate = timeparams.get('startdate', '')
            enddate = timeparams.get('enddate', '')
            startepochsecs = timeparams.get('startepochsecs', '')
            startepochmillies = timeparams.get('startepochmillies', '')
            durationinmins = timeparams.get('durationinmins', '')

            outputstring = inputstring.format(**locals())
            DEBUGOUT(5, "expandvars: %s", [outputstring])
            return outputstring
        
        elif isinstance(inputstring, dict):
            inputstring['requestFilter']['applicationId'] = self.params.get('appid', '')
            inputstring['requestFilter']['mobileApplicationId'] = self.params.get('mobileappid', '')
            DEBUGOUT(5, "expandvars: " + str(inputstring), None)
            return inputstring

    def __str__(self):
        DEBUGOUT(4, "Applications:__str__:", ())

        resulttext = ""
        result = self.parse_results()

        # Handle output format JSON
        if self.options.get('outputformat') == OutputFormat.JSON:
            json_data = self.callresult.json()
            resulttext = json.dumps(json_data, indent=4)

            # Use appid from params to dynamically generate the file names
            appid = self.params.get('appid', 'unknown_appid')

            # Try to save the JSON data into a file
            try:
                json_file = f'Appid_{appid}_business_transactions_list.json'
                with open(json_file, 'w') as f:
                    json.dump(json_data, f, indent=4)
                    print(f"JSON file '{json_file}' has been created successfully.")
                
                # Create a new JSON output from filtered entries
                self.save_to_json(json_data, appid)
            
            except Exception as e:
                return ""

        else:
            print("Error: Data is not in the expected format for JSON.")
            return ""

        return resulttext

class HealthRules(API_Call):
    
    def __init__(self, commandinfo, credinfo, options, ApplicationList):
        super().__init__(commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET 

    def parse_results(self):
        result = self.callresult.content
        return result

    def expandvars(self, inputstring):
        # Check if inputstring is a string or dict
        if isinstance(inputstring, str):
            global timeparams
            DEBUGOUT(6, "expandvars:", [str(inputstring)])

            account = self.params['accountid']
            appid = self.params['appid']
            appname = self.params['appname']
            tiername = self.params['tiername']
            accountid = self.params['accountid']
            entityname = self.params['entityname']

            startdate = timeparams['startdate']
            enddate = timeparams['enddate']
            startepochsecs = timeparams['startepochsecs']
            startepochmillies = timeparams['startepochmillies']
            durationinmins = timeparams['durationinmins']

            outputstring = inputstring.format(**locals())
            DEBUGOUT(5, "expandvars: %s", [outputstring])
            return outputstring
        
        elif isinstance(inputstring, dict):
            outputstring = inputstring
            outputstring['requestFilter']['applicationId'] = self.params['appid']
            outputstring['requestFilter']['mobileApplicationId'] = self.params['mobileappid']
            DEBUGOUT(5, "expandvars: " + str(outputstring), None)
            return outputstring

    def json_to_xml(self, json_data):
        """
        Convert a JSON object to an XML string.
        Assumes json_data is a dictionary.
        """
        def dict_to_xml(tag, d):
            '''
            Converts a dictionary to an XML string.
            '''
            # Create the base element
            elem = ET.Element(tag)
            for key, value in d.items():
                if isinstance(value, dict):
                    elem.append(dict_to_xml(key, value))  # recursive call for nested dict
                else:
                    child = ET.SubElement(elem, key)
                    child.text = str(value)
            return elem
        
        # Convert the top level dictionary to XML
        root = dict_to_xml('root', json_data)
        return ET.tostring(root, encoding='unicode', method='xml')

    def __str__(self):
        DEBUGOUT(4, "Applications:__str__:", ())

        resulttext = ""
        result = self.parse_results()

        # Handle output format XML
        if self.options['outputformat'] == OutputFormat.XML:
            try:
                # Assuming callresult.content is JSON, convert it to dictionary
                json_data = self.callresult.json()

                # Convert the JSON to XML
                xml_data = self.json_to_xml(json_data)

                # Now save the XML data to a file
                appid = self.params.get('appid', 'unknown_appid')
                xml_file = f'Appid_{appid}_business_transactions_list.xml'
                with open(xml_file, 'w') as f:
                    f.write(xml_data)
                    print(f"XML file '{xml_file}' has been created successfully.")

            except Exception as e:
                print(f"Error occurred while converting to XML: {e}")
                return ""

            resulttext = xml_data

        else:
            print("Error: Data is not in the expected format for XML.")
            return ""

        return resulttext

class All_Health_Rules_List(API_Call):
    
    def __init__(self, commandinfo, credinfo, options, ApplicationList):
        super().__init__(commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET 

    def parse_results(self):
        result = self.callresult.content
        return result

    def expandvars(self, inputstring):
        # Check if inputstring is a string or dictionary
        if isinstance(inputstring, str):
            global timeparams
            DEBUGOUT(6, "expandvars:", [str(inputstring)])

            account = self.params['accountid']
            appid = self.params['appid']
            appname = self.params['appname']
            tiername = self.params['tiername']
            accountid = self.params['accountid']
            entityname = self.params['entityname']

            startdate = timeparams['startdate']
            enddate = timeparams['enddate']
            startepochsecs = timeparams['startepochsecs']
            startepochmillies = timeparams['startepochmillies']
            durationinmins = timeparams['durationinmins']

            outputstring = inputstring.format(**locals())
            DEBUGOUT(5, "expandvars: %s", [outputstring])
            return outputstring
        
        elif isinstance(inputstring, dict):
            outputstring = inputstring
            outputstring['requestFilter']['applicationId'] = self.params['appid']
            outputstring['requestFilter']['mobileApplicationId'] = self.params['mobileappid']
            DEBUGOUT(5, "expandvars: " + str(outputstring), None)
            return outputstring

    def __str__(self):
        DEBUGOUT(4, "Applications:__str__:", ())

        resulttext = ""
        result = self.parse_results()

        # Handle output format JSON
        if self.options['outputformat'] == OutputFormat.JSON:
            json_data = self.callresult.json()
            resulttext = json.dumps(json_data, indent=4)

            # Use appid from params to dynamically generate the file names
            appid = self.params.get('appid', 'unknown_appid')

            # Try to save the JSON data into a file
            try:
                json_file = f'Appid_{appid}_Health_Rules_List.json'
                with open(json_file, 'w') as f:
                    json.dump(json_data, f, indent=4)
                    print(f"JSON file '{json_file}' has been created successfully.")
                
                # Create a new JSON output from filtered entries
                self.save_to_json(json_data, appid)
            
            except Exception as e:
                print(f"Error occurred while writing JSON file: {e}")
                return ""

        else:
            print("Error: Data is not in the expected format for JSON.")
            return ""

        return resulttext

    def save_to_json(self, json_data, appid):
        """ Extract and save filtered data from JSON to a new JSON file. """
        try:
            # Assuming the JSON data is a list of business transactions
            if not isinstance(json_data, list):
                raise ValueError("JSON data is not in expected format, should be a list of transactions.")

            # Define the output JSON file path with dynamic appid in the filename
            output_json_file = f"Appid_{appid}_filtered_Health_Rules_List.json"

            # Prepare the filtered entries
            filtered_entries = []
            for entry in json_data:
                # Extract required fields from each entry
                filtered_entry = {
                    "Healthruleid": entry.get("id"),
                    "Health Rule Name": entry.get("name"),
                    "type": entry.get("type"),
                }
                filtered_entries.append(filtered_entry)

            # Write the filtered entries to the JSON file
            with open(output_json_file, 'w') as file:
                json.dump(filtered_entries, file, indent=4)

            print(f"Filtered JSON file '{output_json_file}' has been created successfully.")

        except Exception as e:
            print(f"An error occurred while writing the filtered JSON: {e}")


class All_Policies_List(API_Call):
    
    def __init__(self, commandinfo, credinfo, options, ApplicationList):
        super().__init__(commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET 

    def parse_results(self):
        result = self.callresult.content
        return result

    def expandvars(self, inputstring):
        # Check if inputstring is a string or dictionary
        if isinstance(inputstring, str):
            global timeparams
            DEBUGOUT(6, "expandvars:", [str(inputstring)])

            account = self.params.get('accountid', '')
            appid = self.params.get('appid', '')
            appname = self.params.get('appname', '')
            tiername = self.params.get('tiername', '')
            entityname = self.params.get('entityname', '')

            startdate = timeparams.get('startdate', '')
            enddate = timeparams.get('enddate', '')
            startepochsecs = timeparams.get('startepochsecs', '')
            startepochmillies = timeparams.get('startepochmillies', '')
            durationinmins = timeparams.get('durationinmins', '')

            outputstring = inputstring.format(**locals())
            DEBUGOUT(5, "expandvars: %s", [outputstring])
            return outputstring
        
        elif isinstance(inputstring, dict):
            inputstring['requestFilter']['applicationId'] = self.params.get('appid', '')
            inputstring['requestFilter']['mobileApplicationId'] = self.params.get('mobileappid', '')
            DEBUGOUT(5, "expandvars: " + str(inputstring), None)
            return inputstring

    def __str__(self):
        DEBUGOUT(4, "Applications:__str__:", ())

        resulttext = ""
        result = self.parse_results()

        # Handle output format JSON
        if self.options.get('outputformat') == OutputFormat.JSON:
            json_data = self.callresult.json()
            resulttext = json.dumps(json_data, indent=4)

            # Use appid from params to dynamically generate the file names
            appid = self.params.get('appid', 'unknown_appid')

            # Try to save the JSON data into a file
            try:
                json_file = f'Appid_{appid}_All_Policies_List.json'
                with open(json_file, 'w') as f:
                    json.dump(json_data, f, indent=4)
                    print(f"JSON file '{json_file}' has been created successfully.")
                
                # Create a new JSON output from filtered entries
                self.save_to_json(json_data, appid)
            
            except Exception as e:
                print(f"Error occurred while writing JSON file: {e}")
                return ""

        else:
            print("Error: Data is not in the expected format for JSON.")
            return ""

        return resulttext

    def save_to_json(self, json_data, appid):
        """ Extract and save filtered data from JSON to a new JSON file. """
        try:
            # Ensure the JSON data is a list or a dictionary
            if isinstance(json_data, list):
                # Prepare the filtered entries
                filtered_entries = []
                for entry in json_data:
                    if isinstance(entry, dict):
                        # Extract top-level fields
                        app_name = entry.get("applicationName", "N/A")
                        name = entry.get("name", "N/A")
                        enabled = entry.get("enabled", "N/A")
                        batch_actions_per_minute = entry.get("batchActionsPerMinute", "N/A")

                        # Extract "healthRuleNames" from eventFilterTemplate
                        health_rule_names = []
                        event_filter_template = entry.get("eventFilterTemplate", {})
                        health_rule_names_data = event_filter_template.get("healthRuleNames", [])
                        for rule in health_rule_names_data:
                            entity_name = rule.get("entityName", "")
                            if entity_name:
                                health_rule_names.append(entity_name)

                        # Extract "eventTypes" from eventFilterTemplate
                        event_types = event_filter_template.get("eventTypes", [])

                        # Extract "actionTag" from actionWrapperTemplates
                        action_tags = []
                        action_wrapper_templates = entry.get("actionWrapperTemplates", [])
                        for action in action_wrapper_templates:
                            action_tag = action.get("actionTag", "")
                            if action_tag:
                                action_tags.append(action_tag)

                        # Create the filtered entry with necessary fields
                        filtered_entry = {
                            "applicationName": app_name,
                            "Policy Name": name,
                            "enabled": enabled,
                            "batchActionsPerMinute": batch_actions_per_minute,
                            "Health Rule Names": health_rule_names,
                            "Event Types": event_types,
                            "Actions": action_tags
                        }

                        # Add filtered entry to the list
                        filtered_entries.append(filtered_entry)

                # Define the output JSON file path with dynamic appid in the filename
                output_json_file = f"Health_Rules_Map_To_Alerting_Policies_{appid}.json"
                
                # Write the filtered entries to the JSON file
                with open(output_json_file, 'w') as file:
                    json.dump(filtered_entries, file, indent=4)

                print(f"Filtered JSON file '{output_json_file}' has been created successfully.")

            else:
                print("Error: JSON data is not in expected list format.")

        except Exception as e:
            print(f"An error occurred while writing the filtered JSON: {e}")

class Health_Rules_Id(API_Call): 
    
    def __init__(self, commandinfo, credinfo, options, ApplicationList, timeparams=None):
        super().__init__(commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET
        self.timeparams = timeparams if timeparams else {}  # Use provided timeparams or an empty dictionary

    def parse_results(self):
        result = self.callresult.content
        return result

    def expandvars(self, inputstring):
        # Check if inputstring is a string or dict
        if isinstance(inputstring, str):
            DEBUGOUT(6, "expandvars:", [str(inputstring)])

            # Extract parameters from self.params
            accountid = self.params.get('accountid')
            appid = self.params.get('appid')
            appname = self.params.get('appname')
            tiername = self.params.get('tiername')
            entityname = self.params.get('entityname')

            # Extract time parameters from self.timeparams
            startdate = self.timeparams.get('startdate')
            enddate = self.timeparams.get('enddate')
            startepochsecs = self.timeparams.get('startepochsecs')
            startepochmillies = self.timeparams.get('startepochmillies')
            durationinmins = self.timeparams.get('durationinmins')

            # Format the string with the local variables
            outputstring = inputstring.format(**locals())
            DEBUGOUT(5, "expandvars:", [outputstring])
            return outputstring
        
        elif isinstance(inputstring, dict):
            # Update requestFilter fields in the dictionary
            inputstring['requestFilter']['applicationId'] = self.params.get('appid')
            inputstring['requestFilter']['mobileApplicationId'] = self.params.get('mobileappid')
            DEBUGOUT(5, "expandvars:", [str(inputstring)])
            return inputstring

    def append_to_combined_json(self, filtered_data, appid, entityname):
        combined_json_file = f'Appid_{appid}_filtered_Business_Transactions_List.json'  # Fixed f-string

        try:
            # Check if the file exists and read its current contents
            if os.path.exists(combined_json_file):
                with open(combined_json_file, 'r') as f:
                    combined_data = json.load(f)
            else:
                combined_data = {}

            # Create or append the data for the given entityname (Healthruleid)
            healthruleid = str(entityname)  # Make sure Healthruleid is a string
            if healthruleid not in combined_data:
                combined_data[healthruleid] = []
            
            # Append the filtered data to the relevant healthruleid list
            combined_data[healthruleid].extend(filtered_data)

            # Write the updated combined data back to the file
            with open(combined_json_file, 'w') as f:
                json.dump(combined_data, f, indent=4)
                print(f"Appended filtered data to '{combined_json_file}'")
        
        except Exception as e:
            print(f"Error occurred while appending to the combined JSON file: {e}")
            return ""

    def create_filtered_json(self, entityname):
        # Construct the filename for the original JSON file
        json_file = f'Health_Rules_Id_{entityname}.json'
        
        try:
            # Load the original JSON file
            with open(json_file, 'r') as f:
                original_data = json.load(f)

            # Prepare the filtered data (assuming 'name' and 'tierName' are in the original JSON structure)
            filtered_data = []
            for item in original_data:
                # Check if 'name' and 'tierName' exist in the item
                if 'name' in item and 'tierName' in item:
                    # Modify 'name' to 'BusinessTransactionsName'
                    filtered_item = {
                        'BusinessTransactionsName': item['name'],  # Changed 'name' to 'BusinessTransactionsName'
                        'TierName': item['tierName'],
                        'Healthruleid': f"{entityname}"  # Set Healthruleid to the value of entityname
                    }
                    filtered_data.append(filtered_item)

            # Append to the combined JSON file
            appid = self.params.get('appid')  # Need to get appid
            self.append_to_combined_json(filtered_data, appid, entityname)

            # Delete the filtered JSON file after appending
            if os.path.exists(json_file):
                os.remove(json_file)  # Delete the file
                print(f"Deleted file: {json_file}")
            
        except Exception as e:
            print(f"Error occurred while processing the JSON file: {e}")
            return ""

    def __str__(self):
        DEBUGOUT(4, "Health_Rules_Id:__str__:", ())

        resulttext = ""
        result = self.parse_results()

        # Handle output format JSON
        if self.options.get('outputformat') == OutputFormat.JSON:
            json_data = self.callresult.json()
            resulttext = json.dumps(json_data, indent=4)

            # Use appid from params to dynamically generate the file names
            appid = self.params.get('appid', 'unknown_appid')
            entityname = self.params.get('entityname')

            # Try to save the JSON data into a file with updated name
            try:
                json_file = f'Health_Rules_Id_{entityname}.json'
                with open(json_file, 'w') as f:
                    json.dump(json_data, f, indent=4)
                    print(f"JSON file '{json_file}' has been created successfully.")
                
                # Now, create a new filtered JSON file with 'BusinessTransactionsName', 'tierName', and 'Healthruleid'
                self.create_filtered_json(entityname)
            
            except Exception as e:
                print(f"Error occurred while writing JSON file: {e}")
                resulttext = ""  # Return empty string in case of error

        else:
            print("Error: Data is not in the expected format for JSON.")
            resulttext = ""  # Ensure that an empty string is returned if the format is incorrect.

        return resulttext

class ViolationsIncidentsList(API_Call):

    def __init__(self, commandinfo, credinfo, options, ApplicationList):
        super().__init__(commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET 

    def parse_results(self):
        result = self.callresult.content
        return result

    def expandvars(self, inputstring):
        # Check if inputstring is a string or dictionary
        if isinstance(inputstring, str):
            global timeparams
            DEBUGOUT(6, "expandvars:", [str(inputstring)])

            account = self.params.get('accountid', '')
            appid = self.params.get('appid', '')
            appname = self.params.get('appname', '')
            tiername = self.params.get('tiername', '')
            entityname = self.params.get('entityname', '')

            startdate = timeparams.get('startdate', '')
            enddate = timeparams.get('enddate', '')
            startepochsecs = timeparams.get('startepochsecs', '')
            startepochmillies = timeparams.get('startepochmillies', '')
            durationinmins = timeparams.get('durationinmins', '')

            outputstring = inputstring.format(**locals())
            DEBUGOUT(5, "expandvars: %s", [outputstring])
            return outputstring
        
        elif isinstance(inputstring, dict):
            inputstring['requestFilter']['applicationId'] = self.params.get('appid', '')
            inputstring['requestFilter']['mobileApplicationId'] = self.params.get('mobileappid', '')
            DEBUGOUT(5, "expandvars: " + str(inputstring), None)
            return inputstring

    def __str__(self):
        DEBUGOUT(4, "Applications:__str__:", ())

        resulttext = ""
        result = self.parse_results()

        # Handle output format JSON
        if self.options.get('outputformat') == OutputFormat.JSON:
            json_data = self.callresult.json()
            resulttext = json.dumps(json_data, indent=4)

            # Use appid from params to dynamically generate the file names
            appid = self.params.get('appid', 'unknown_appid')

            # Try to save the JSON data into a file
            try:
                json_file = f'Appid_{appid}_Violations_incidents_list.json'
                with open(json_file, 'w') as f:
                    json.dump(json_data, f, indent=4)
                    print(f"JSON file '{json_file}' has been created successfully.")
                
                # Create a new JSON output from filtered entries
                self.save_to_json(json_data, appid)
            
            except Exception as e:
                return ""

        else:
            print("Error: Data is not in the expected format for JSON.")
            return ""

        return resulttext

class NotificationActions(API_Call):

    def __init__(self, commandinfo, credinfo, options, ApplicationList):
        super().__init__(commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET 

    def parse_results(self):
        """Handle API result and return content, even in case of a 500 error"""
        result = self.callresult.content

        # If there's a 500 error, try to extract partial data from the response
        if self.callresult.status_code == 500:
            print("Server error (500) encountered. Attempting to process available data.")
            try:
                data = result.json()  # Try parsing JSON response if present
                return data
            except ValueError:
                print("Error parsing the response body as JSON.")
                return result  # Return raw content if parsing fails
        else:
            return result

    def expandvars(self, inputstring):
        """Handle variable expansion in strings or dictionaries"""
        if isinstance(inputstring, str):
            global timeparams
            DEBUGOUT(6, "expandvars:", [str(inputstring)])

            # Fetch parameters from self.params and timeparams
            account = self.params.get('accountid', '')
            appid = self.params.get('appid', '')
            appname = self.params.get('appname', '')
            tiername = self.params.get('tiername', '')
            entityname = self.params.get('entityname', '')

            startdate = timeparams.get('startdate', '')
            enddate = timeparams.get('enddate', '')
            startepochsecs = timeparams.get('startepochsecs', '')
            startepochmillies = timeparams.get('startepochmillies', '')
            durationinmins = timeparams.get('durationinmins', '')

            # Format the string with variables
            outputstring = inputstring.format(**locals())
            DEBUGOUT(5, "expandvars: %s", [outputstring])
            return outputstring
        
        elif isinstance(inputstring, dict):
            inputstring['requestFilter']['applicationId'] = self.params.get('appid', '')
            inputstring['requestFilter']['mobileApplicationId'] = self.params.get('mobileappid', '')
            DEBUGOUT(5, "expandvars: " + str(inputstring), None)
            return inputstring

    def __str__(self):
        DEBUGOUT(4, "Applications:__str__:", ())

        resulttext = ""
        result = self.parse_results()

        # Handle output format JSON
        if self.options.get('outputformat') == OutputFormat.JSON:
            if isinstance(result, dict):  # Ensure the result is a JSON object
                resulttext = json.dumps(result, indent=4)

                appid = self.params.get('appid', 'unknown_appid')

                try:
                    # Attempt to save the JSON data into a file
                    json_file = f'Appid_{appid}_notification_actions.json'
                    with open(json_file, 'w') as f:
                        json.dump(result, f, indent=4)
                        print(f"JSON file '{json_file}' has been created successfully.")

                    # Create a new JSON output from filtered entries
                    self.save_to_json(result, appid)
                
                except Exception as e:
                    print(f"Error saving JSON file: {str(e)}")
                    return ""
            else:
                print("Error: Result is not in the expected format for JSON.")
                return ""

        else:
            print("Error: Unsupported output format.")
            return ""

        return resulttext
    
class NetworkRequests_Exclude_Include_List(API_Call):
    
    def __init__(self, commandinfo, credinfo, options, ApplicationList):
        super().__init__(commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET
    
    def parse_results(self):
        result = self.callresult.content
        return result

    def expandvars(self, inputstring):
        if isinstance(inputstring, str):
            global timeparams
            DEBUGOUT(6, "expandvars:", [str(inputstring)])

            account = self.params['accountid']
            appid = self.params['appid']
            appname = self.params['appname']
            tiername = self.params['tiername']
            accountid = self.params['accountid']
            entityname = self.params['entityname']
            startdate = timeparams['startdate']
            enddate = timeparams['enddate']
            startepochsecs = timeparams['startepochsecs']
            startepochmillies = timeparams['startepochmillies']
            durationinmins = timeparams['durationinmins']

            outputstring = inputstring.format(**locals())
            DEBUGOUT(5, "expandvars: %s", {outputstring})
        elif isinstance(inputstring, dict):
            outputstring = inputstring
            outputstring['requestFilter']['applicationId'] = self.params['appid']
            outputstring['requestFilter']['mobileApplicationId'] = self.params['mobileappid']
            DEBUGOUT(5, "expandvars: " + str(outputstring), None)
        return outputstring

    def __str__(self):
        DEBUGOUT(4, "Applications:__str__:", ())
        resulttext = ""
        result = self.parse_results()

        if self.options['outputformat'] == OutputFormat.JSON:
            resulttext = json.dumps(self.callresult.json(), indent=4)
            # Save the full API result to a JSON file
            with open('networkRequests_Ex_In_List.json', 'w') as f:
                json.dump(self.callresult.json(), f, indent=4)

            # After saving the JSON, extract and save separate JSON files for Exclude and Include Rules
            self.save_separate_json_files('networkRequests_Ex_In_List.json')
        else:
            print("Error: Data is not in the expected format for json")
            return ""

        return resulttext
    
    def save_separate_json_files(self, input_file):
        """ Extract and save customNamingExcludeRules and customNamingIncludeRules to separate JSON files. """
        with open(input_file, 'r') as file:
            data = json.load(file)

        # Extract Exclude and Include Rules
        exclude_rules = data.get('customNamingExcludeRules', [])
        include_rules = data.get('customNamingIncludeRules', [])

        # Save exclude rules to a separate JSON file
        with open('customNamingExcludeRules.json', 'w') as f:
            json.dump(exclude_rules, f, indent=4)
        print(f"customNamingExcludeRules saved to 'customNamingExcludeRules.json'.")

        # Save include rules to a separate JSON file
        with open('customNamingIncludeRules.json', 'w') as f:
            json.dump(include_rules, f, indent=4)
        print(f"customNamingIncludeRules saved to 'customNamingIncludeRules.json'.")
        
        # After saving the separate JSON files for Exclude Rules, convert Exclude Rules to CSV
        self.process_json_to_csv('customNamingExcludeRules.json', 'customNamingExcludeRules.csv')

    def process_json_to_csv(self, input_file, output_file):
        """ Convert extracted JSON data for Exclude Rules to CSV. """
        with open(input_file, 'r') as file:
            data = json.load(file)

        csv_data = []
        for rule in data:
            name = rule.get('name')
            match_url_value = rule.get('matchOnURL', {}).get('value', '')
            if name and match_url_value:
                csv_data.append([name, match_url_value])

        with open(output_file, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['name', 'value'])
            writer.writerows(csv_data)

        print(f"CSV file '{output_file}' has been created.")

class UpdateNetworkRequestExcludeList(API_Call):

        def __init__(self, commandinfo, credinfo, options, ApplicationList):
            super().__init__(commandinfo, credinfo, options, ApplicationList)
            self.calltype = CallType.PUT

        def expandvars (self, inputstring):

            if isinstance(inputstring, str):

                global timeparams
                DEBUGOUT (6, "expandvars:", [str(inputstring)])

                account = self.params['accountid']
                appid = self.params['appid']
                appname = self.params['appname']
                tiername = self.params['tiername']
                accountid = self.params['accountid']
                entityname = self.params['entityname']

                startdate = timeparams['startdate']
                enddate = timeparams['enddate']
                startepochsecs = timeparams['startepochsecs']
                startepochmillies = timeparams['startepochmillies']
                durationinmins = timeparams['durationinmins']
                
                outputstring = inputstring.format(**locals())        
                #url = url.format(**globals())

                DEBUGOUT (5, "expandvars: %s", {outputstring})
            elif isinstance(inputstring, dict):
                outputstring = inputstring
                # outputstring['requestFilter']['applicationId'] = self.params['appid']
                # outputstring['requestFilter']['mobileApplicationId'] = self.params['mobileappid']
                # outputstring['requestFilter']['mobileApplicationId'] = self.params['appid']
                # outputstring['timeRangeStart'] = timeparams['startepochmillies']
                # outputstring['timeRangeEnd'] = self.params['endepochmillies']
                DEBUGOUT (5, "expandvars: " + str(outputstring), None)
            return outputstring

        def __str__(self):
            DEBUGOUT(4, "Applications:__str__:", ())
            resulttext = ""
            result = self.parse_results()

            # Handle TEXT output format
            if self.options['outputformat'] == OutputFormat.TEXT:
                with open('CreateNetworkRequestExcludeList.txt', 'w') as f:
                    # Dumping JSON into a text file (just as string)
                    json.dump(self.callresult.json(), f)

            # Handle JSON output format
            elif self.options['outputformat'] == OutputFormat.JSON:
                resulttext = json.dumps(self.callresult.json(), indent=4)  # Pretty print the JSON
                with open('CreateNetworkRequestExcludeList.json', 'w') as f:
                    json.dump(self.callresult.json(), f, indent=4)  # Write pretty JSON to a file

            # Handle CSV output format
            elif self.options['outputformat'] == OutputFormat.CSV:
                data = self.callresult.json()  # Assuming it's a list of dictionaries
                if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
                    with open('CreateNetworkRequestExcludeList.csv', 'w', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=data[0].keys())  # Use the keys of the first dict as headers
                        writer.writeheader()  # Write the header
                        writer.writerows(data)  # Write the data rows
                else:
                    print("Error: Data is not in the expected format for CSV.")
                    return ""

            else:
                print("Unknown output format")
                exit(1)

            return resulttext
        
class ExcludeNetworkRequestTrafficZero(API_Call):

    def __init__(self, commandinfo, credinfo, options, ApplicationList):
        super().__init__(commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.POST

    def parse_results(self):
        return self.callresult.content

    def expandvars(self, inputstring):
        if isinstance(inputstring, str):
            # Using locals() to inject local variables into the string
            try:
                account = self.params['accountid']
                appid = self.params['appid']
                appname = self.params['appname']
                tiername = self.params['tiername']
                entityname = self.params['entityname']
                startdate = self.params.get('startdate', '')
                enddate = self.params.get('enddate', '')
                startepochmillies = self.params.get('startepochmillies', '')
                durationinmins = self.params.get('durationinmins', '')

                outputstring = inputstring.format(**locals())
                DEBUGOUT(5, "expandvars: %s", outputstring)
            except KeyError as e:
                DEBUGOUT(1, f"KeyError: Missing key {e} in self.params")
                raise

        elif isinstance(inputstring, dict):
            try:
                outputstring = inputstring
                # Assuming timeparams is a valid dictionary in self.params
                outputstring['timeRangeStart'] = self.params.get('startepochmillies', '')
                outputstring['timeRangeEnd'] = self.params.get('endepochmillies', '')
                outputstring['requestFilter']['applicationId'] = self.params['appid']
                # outputstring['requestFilter']['mobileApplicationId'] = self.params.get('mobileappid', None)
                DEBUGOUT(5, "expandvars: " + str(outputstring), None)
            except KeyError as e:
                DEBUGOUT(1, f"KeyError: Missing key {e} in inputstring or self.params")
                raise

        elif isinstance(inputstring, list):
            # read in the inputfile
            try:
                with open(self.params['inputfile'], 'r') as file:
                    data = json.load(file)
                    outputstring = data
            except KeyError as e:
                DEBUGOUT(1, f"KeyError: Missing 'inputfile' in self.params")
                raise
            except FileNotFoundError as e:
                DEBUGOUT(1, f"FileNotFoundError: The file {self.params['inputfile']} was not found")
                raise
            except json.JSONDecodeError as e:
                DEBUGOUT(1, f"JSONDecodeError: Failed to decode JSON from the file {self.params['inputfile']}")
                raise

        return outputstring

class DeletePageListRequestsConfirm(API_Call):
    
        def __init__(self, commandinfo, credinfo, options, ApplicationList):
            super().__init__(commandinfo, credinfo, options, ApplicationList)
            self.calltype = CallType.POST
    
        def parse_results(self):
            return self.callresult.content
    
        def expandvars(self, inputstring):
            outputstring = inputstring
            if isinstance(inputstring, str):
                # Using locals() to inject local variables into the string
                account = self.params['accountid']
                appid = self.params['appid']
                appname = self.params['appname']
                tiername = self.params['tiername']
                entityname = self.params['entityname']
                startdate = timeparams.get('startdate', '')
                enddate = timeparams.get('enddate', '')
                startepochmillies = timeparams.get('startepochmillies', '')
                durationinmins = timeparams.get('durationinmins', '')
    
                # Format the input string using the above local variables
                outputstring = inputstring.format(**locals())
                return outputstring
            elif isinstance(inputstring, dict):
                # If it's a dictionary, you can expand specific values here
                # Example of adding more processing if necessary
                return inputstring
            elif isinstance(inputstring, list):
                # read in the inputfile
                with open(self.params['inputfile'], 'r') as file:
                    # {"applicationId":580,"synthetic":false,"addIds":[2863110],"confirm":true}
                    data = json.load(file)
                    outputstring = {}
                    outputstring['applicationId'] = self.params['appid']
                    outputstring['addIds'] = data
                    outputstring['synthetic'] = False
                    outputstring['confirm'] = False

            return outputstring

class DeleteNetworkRequestTrafficZero(API_Call):

    def __init__(self, commandinfo, credinfo, options, ApplicationList):
        super().__init__(commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.POST

    def parse_results(self):
        return self.callresult.content

    def expandvars(self, inputstring):
        if isinstance(inputstring, str):
            # Using locals() to inject local variables into the string
            try:
                account = self.params['accountid']
                appid = self.params['appid']
                appname = self.params['appname']
                tiername = self.params['tiername']
                entityname = self.params['entityname']
                startdate = self.params.get('startdate', '')
                enddate = self.params.get('enddate', '')
                startepochmillies = self.params.get('startepochmillies', '')
                durationinmins = self.params.get('durationinmins', '')

                outputstring = inputstring.format(**locals())
                DEBUGOUT(5, "expandvars: %s", outputstring)
            except KeyError as e:
                DEBUGOUT(1, f"KeyError: Missing key {e} in self.params")
                raise

        elif isinstance(inputstring, dict):
            try:
                outputstring = inputstring
                # Assuming timeparams is a valid dictionary in self.params
                outputstring['timeRangeStart'] = self.params.get('startepochmillies', '')
                outputstring['timeRangeEnd'] = self.params.get('endepochmillies', '')
                outputstring['requestFilter']['applicationId'] = self.params['appid']
                # outputstring['requestFilter']['mobileApplicationId'] = self.params.get('mobileappid', None)
                DEBUGOUT(5, "expandvars: " + str(outputstring), None)
            except KeyError as e:
                DEBUGOUT(1, f"KeyError: Missing key {e} in inputstring or self.params")
                raise

        elif isinstance(inputstring, list):
            # read in the inputfile
            try:
                with open(self.params['inputfile'], 'r') as file:
                    data = json.load(file)
                    outputstring = data
            except KeyError as e:
                DEBUGOUT(1, f"KeyError: Missing 'inputfile' in self.params")
                raise
            except FileNotFoundError as e:
                DEBUGOUT(1, f"FileNotFoundError: The file {self.params['inputfile']} was not found")
                raise
            except json.JSONDecodeError as e:
                DEBUGOUT(1, f"JSONDecodeError: Failed to decode JSON from the file {self.params['inputfile']}")
                raise

        return outputstring

class ITOCDashBoard(API_Call):
    dashboardId = 0

    def __init__ (self, commandinfo, credinfo, options, ApplicationList):
        super().__init__ (commandinfo, credinfo, options, ApplicationList)
        dashboardId = 0

class LicenseUsage (API_Call):

    def __init__ (self, commandinfo, credinfo, options, ApplicationList):
        super().__init__ (commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET

    def parse_results (self):
        result = []
        row = []

        result.append (self.get_headers())
        jsondata = self.callresult.json()
        for jsonrow in jsondata['usages']:
            row = []
            for header in self.get_headers():
                row.append(jsonrow[header])
            result.append(row)

        return result

class Roles(API_Call):

    def __init__ (self, commandinfo, credinfo, options, ApplicationList):
        super().__init__ (commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET

    def parse_results (self):
        result = []
        row = []

        result.append (self.get_headers())
        jsondata = self.callresult.json()
        for jsonrow in jsondata['roles']:
            row = []
            for header in self.get_headers():
                row.append(jsonrow[header])
            result.append(row)

        return result
        

class AppReport(API_Call):
    dummy = ""

    def __init__ (self, commandinfo, credinfo, options, ApplicationList):
        super().__init__ (commandinfo, credinfo, options, ApplicationList)
        dummy = ""

class MyAccount(API_Call):

    def __init__ (self, commandinfo, credinfo, options, ApplicationList):
        super().__init__ (commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET

    def parse_results (self):
        global options
        result = []
        row = []

        result.append (self.get_headers())
        jsondata = self.callresult.json()
        for header in self.get_headers():
            row.append(jsondata[header])
        result.append(row)

        return result

    def get_accountid (self):
        if not self.callresult:
            self.sendcall ({})

        accountjson = self.callresult.json()

        return accountjson['id']

class AppInfo(API_Call):

    def __init__ (self, commandinfo, credinfo, options, ApplicationList):
        super().__init__ (commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET

    def parse_results (self):
        global options
        result = []
        row = []

        result.append (self.get_headers)
        jsondata = self.callresult.json()
        for header in self.get_headers():
            if header == "createdOn" or header == "modifiedOn":
                row.append (datetime.datetime.fromtimestamp(jsondata[header] / 1000).strftime('%Y-%m-%d %H:%M:%S.%f %Z'))
            else:
                row.append(jsondata[header])
        result.append(row)

        return result

    def add_app_results (self, appname, results):
        DEBUGOUT (4, "add_app_results: app %s", {appname})

        self.allresults.update(row)



class Actions(API_Call):

    def __init__ (self, commandinfo, credinfo, options, ApplicationList):
        super().__init__ (commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET

    def parse_results (self):
        global options
        result = []
        row = []

        result.append (self.get_headers())

        jsondata = self.callresult.json()
        for row in jsondata:
            entrydata = []
            entrydata.append(row["name"])
            entrydata.append(row["actionType"])
            entrydata.append(row["priority"])

            if "httpRequestActionPlanName" in row:
                entrydata.append(row["httpRequestActionPlanName"])
            elif "toAddress" in row:
                entrydata.append(row["toAddress"])
            else:
                entrydata.append("")

            if "customProperties" in row and "CI_ID" in row["customProperties"]:
                entrydata.append(row["customProperties"]["CI_ID"])
            elif "subject" in row:
                entrydata.append(row["subject"])
            else:
                entrydata.append("")
                
            result.append(entrydata)

        return result

class Policies(API_Call):

    def __init__ (self, commandinfo, credinfo, options, ApplicationList):
        super().__init__ (commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.GET

    def parse_results (self):
        global options
        result = []
        row = []

        result.append (self.get_headers())

        jsondata = self.callresult.json()
        for jsonrow in jsondata:
            healthrules = []
            actions = []
            entrydata = []
            if 'eventFilterTemplate' in jsonrow \
               and 'healthRuleNames' in jsonrow['eventFilterTemplate'] \
               and type(jsonrow['eventFilterTemplate']['healthRuleNames']) == list: 
                for healthrule in jsonrow['eventFilterTemplate']['healthRuleNames']:
                    healthrules.append(healthrule['entityName'])
            if 'actionWrapperTemplates' in jsonrow:
                for action in jsonrow['actionWrapperTemplates']:
                    actions.append (action['actionTag'])
            for header in self.get_headers():
                if header == "healthrules":
                    entrydata.append("; ".join(healthrules))
                elif header == "actions":
                    entrydata.append("; ".join(actions))
                else:
                    entrydata.append(jsonrow[header])
            result.append (entrydata)

        return result

class MobileAppCrash(API_Call):
    

    def __init__ (self, commandinfo, credinfo, options, ApplicationList):
        super().__init__ (commandinfo, credinfo, options, ApplicationList)
        self.calltype = CallType.POST

    def parse_results (self):
        result = self.callresult.content
        return result

        
#
# The API commands this script can run.  Each entry in this array dictionary is indexed by the
# command name, as given on the command line as a parameter, and each entry is itself a dict with the following
# required and optional entries:
#
#   "type":     required, one of CallType.CLASS, GET, or PUT/POST
#   "Class":    required when "type" is CallType.CLASS - reference to class inheriting from "API_Call" 
#   "uri":      required, the uri of the REST endpoint, must be http encoded.  allows templated parts as follows:
#
#               entity and app identification fields:
#               {appid}      - the appdynamics id of the target application, if required.  requires "-app" option be given
#               {tiername}   - name of application's tier, if required
#               {entityname} - e.g. health rule name, policy name, etc if required
#               {accountid}  - controller account id, auto-retreived when required, see "flags" below
#
#               time fields in several formats for queries with a time parameter: 
#               {startepochmillies} - start time for query, in epoch milliseconds
#               {durationinmins}  - duration of query from start time, in minutes
#               {startdate}  - start datetime of query
#               {enddate}    - end datetime of query
#
#   "flags":    optional, may contain the following settings
#               needs_appid  - command must be given the "-app" option identifying an app to target for the query
#               needs_entity - command must be given the "-entity" option id'ing the entity to target, e.g. health rule
#               needs_accountid - causes program to send query to retrieve account id from controller
#
#   "returntype": optional - specifies if call returns JSON, XML.  Set by ReturnType.JSON or XML
#               Sometimes needed if "standard" API_Call and want to process without creating inherited class instead.
#
#   "headers":  optional - list of JSON vars to extract from JSON result, and also names of headers for outputting results.
#               Does not need if outputting a blob or no output expected.

# https://mayo.saas.appdynamics.com/controller/restui/mobile/networkrequestlist
# {"requestFilter":{"applicationId":579,"mobileApplicationId":3},"resultColumns":["NETWORK_REQUEST_NAME","NETWORK_REQUEST_ORIGINAL_NAME","TOTAL_REQUESTS","NETWORK_REQUEST_TIME"],"offset":0,"limit":-1,"searchFilters":[],"columnSorts":[{"column":"TOTAL_REQUESTS","direction":"DESC"}],"timeRangeStart":1733258319643,"timeRangeEnd":1734467919643}
# /controller/restui/mobileRequestListUiService/excludeRequests
# [2351878]
# /controller/restui/mobileRUMConfig/networkRequestsConfig/579

# Function to read the CSV file and generate customNamingExcludeRules and customNamingIncludeRules
def generate_rules_from_csv(csv_file):
    custom_naming_exclude_rules = []

    # Read CSV and populate the exclude rules
    with open(csv_file, mode='r', newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row['name']
            value = row['value']
            custom_naming_exclude_rules.append({
                "enabled": True,
                "name": name,
                "priority": 0,
                "matchOnURL": {
                    "type": "CONTAINS",
                    "value": value,
                    "classType": "urlMatchCriteria"
                }
            })

    # Return the populated list of exclude rules
    return custom_naming_exclude_rules

# Generate rules from the CSV file
csv_file = 'customNamingExcludeRules.csv'
#ustom_naming_exclude_rules = generate_rules_from_csv(csv_file)
try:
    custom_naming_exclude_rules = generate_rules_from_csv(csv_file)
except FileNotFoundError:
    custom_naming_exclude_rules = []

# Attempt to read the JSON file
try:
    with open('customNamingIncludeRules.json', 'r') as file:
        data = json.load(file)
except FileNotFoundError:
    print("Error: The file 'customNamingIncludeRules.json' was not found.")
    data = []
except json.JSONDecodeError:
    print("Error: There was an issue decoding the JSON file.")
    data = []

# Ensure customNamingIncludeRules exists in the data
custom_naming_include_rules = data if data else [] 

commandlist = {
    "myaccount" : {
        "type": CallType.CLASS,
        "Class": MyAccount,
        "uri": '/api/accounts/myaccount',
        "headers": ["id", "name"]
    },
    "applications" : {
        "type": CallType.CLASS,
        "Class": Applications,
        "uri": '/restui/applicationManagerUiBean/getApplicationsAllTypes?output=JSON',
        "flags": {},
	"headers": ["type", "name", "id", "description", "createdBy", "createdOn", "modifiedBy", "modifiedOn"]
    },
    "mobile_network_request_list": {
        "type": CallType.CLASS,
        "Class": MobileNetworkRequestList,
        "uri": '/restui/mobile/networkrequestlist',
        "flags": {
            "needs_appid": 1,
            "needs_mobileappid": 1,
            "needs_startepochmillies": 1
        },
        "payload": {"requestFilter":{"applicationId":579,"mobileApplicationId":3},"resultColumns":["NETWORK_REQUEST_NAME","NETWORK_REQUEST_ORIGINAL_NAME","TOTAL_REQUESTS","NETWORK_REQUEST_TIME"],"offset":0,"limit":-1,"searchFilters":[],"columnSorts":[{"column":"TOTAL_REQUESTS","direction":"DESC"}],"timeRangeStart":1733258319643,"timeRangeEnd":1734467919643}
        # {"requestFilter":{"applicationId":{appid},"mobileApplicationId":3},"resultColumns":["NETWORK_REQUEST_NAME","NETWORK_REQUEST_ORIGINAL_NAME","TOTAL_REQUESTS","NETWORK_REQUEST_TIME"],"offset":0,"limit":-1,"searchFilters":[],"columnSorts":[{"column":"TOTAL_REQUESTS","direction":"DESC"}],"timeRangeStart":{startepochmillies},"timeRangeEnd":{startepochmillies}}
    },
    "page_list": {
        "type": CallType.CLASS,
        "Class": PageList,
        "uri": '/controller/restui/web/pagelist',
        "flags": {
            "needs_appid": 1,
            "needs_startepochmillies": 1
        },
        "payload": {"requestFilter":{"applicationId":24097,"fetchSyntheticData":False},"resultColumns":["PAGE_TYPE","PAGE_NAME","TOTAL_REQUESTS","END_USER_RESPONSE_TIME","VISUALLY_COMPLETE_TIME"],"offset":0,"limit":-1,"searchFilters":[],"columnSorts":[{"column":"TOTAL_REQUESTS","direction":"DESC"}],"timeRangeStart":timeparams["startepochmillies"],"timeRangeEnd":timeparams["endepochmillies"]}
    },
    "exclude_page": {
        "type": CallType.CLASS,
        "Class": PageListExcludeRequests,
        "uri": '/controller/restui/pageList/excludeRequests',
        "flags": {
            "needs_input_file": 1
        },
        "payload": [0]
    },
    "delete_page": {
        "type": CallType.CLASS,
        "Class": DeletePageListRequestsConfirm,
        "uri": '/controller/restui/pageList/deleteRequestsConfirm',
        "flags": {
            "needs_input_file": 1,
            "needs_appid": 1
        },
        "payload": [0]
    },
    "exclude_network_request_traffic_zero": {
        "type": CallType.CLASS,
        "Class": ExcludeNetworkRequestTrafficZero,
        "uri": "/controller/restui/mobileRequestListUiService/excludeRequests",
        "flags": {
            "needs_input_file": 1
        },
        "payload": [0]
    },
    "delete_network_request_traffic_zero": {
        "type": CallType.CLASS,
        "Class": DeleteNetworkRequestTrafficZero,
        "uri": "/controller/restui/mobileRequestListUiService/deleteRequests",
        "flags": {
            "needs_input_file": 1
        },
        "payload": [0]
    },
    "browser_rum_config_exclude_include_list": {
        "type": CallType.CLASS,
        "Class": BrowserRUMConfig_Exclude_Include_List,
        "uri": '/controller/restui/browserRUMConfig/getAJAXConfig/{appid}',
        "flags": {
            "needs_appid": 1
        }
    },
    "network_requests_exclude_include_list": {
        "type": CallType.CLASS,
        "Class": NetworkRequests_Exclude_Include_List,
        "uri": '/controller/restui/mobileRUMConfig/networkRequestsConfig/{appid}',
        "flags": {
            "needs_appid": 1
        }
    },
    "update_network_request_exclude_list": {
        "type": CallType.CLASS,
        "Class": UpdateNetworkRequestExcludeList,
        "uri": '/controller/restui/mobileRUMConfig/networkRequestsConfig/{appid}',
        "flags": {
            "needs_appid": 1,
            "needs_mobileappid": 1,
            "needs_startepochmillies": 1
        },
        "payload": {
            "customNamingIncludeRules": custom_naming_include_rules,
            "customNamingExcludeRules": custom_naming_exclude_rules,
            "eventServiceIncludeRules": [],
            "eventServiceExcludeRules": []
        } 
    },
    "all_business_transactions_list": {
        "type": CallType.CLASS,
        "Class": All_Business_Transactions_List,
        "uri": '/controller/rest/applications/{appid}/business-transactions?output=JSON',
        "flags": {
            "needs_appid": 1,
        },
        "returntype": ReturnType.JSON,
        "headers": ["name","id","tierName","entryPointType"]
    },
    "all_healthrules_list" : {
        "type": CallType.CLASS,
        "Class": All_Health_Rules_List,
        "uri": '/controller/restui/policy2/policiesSummary/{appid}',
        "flags": {
            "needs_appid": 1,
        }
    },
    "all_policies_list" : {
        "type": CallType.CLASS,
        "Class": All_Policies_List,
        "uri": '/controller/policies/{appid}',
        "flags": {
            "needs_appid": 1,
        }
    },
    "healthrules_id" : {
        "type": CallType.CLASS,
        "Class": Health_Rules_Id,
        "uri": '/controller/restui/healthRules/getHealthRuleCurrentEvaluationStatus/app/{appid}/healthRuleID/{entityname}',
        "flags": {
            "needs_appid": 1,
            "needs_entity": 1
        }
    },        
    "violations_incidents_list": {
        "type": CallType.CLASS, 
        "Class": ViolationsIncidentsList, 
        "uri": '/controller/rest/applications/{appid}/problems/healthrule-violations?time-range-type=AFTER_TIME&start-time={startepochmillies}&duration-in-mins={durationinmins}&output=JSON',
        "flags": {
            "needs_appid": 1,
            "needs_startepochmillies": 1,
            "needs_duration": 1,
        },
        "headers": ["id", "name", "startTimeInMillies", "endTimeInMillies", "triggeredEntityDefinition.entityType", "triggeredEntityDefinition.name", "affectedEntityDefinition.entityType", "affectedEntityDefinition.name"]
    },        
    "get_actions_list": {
        "type": CallType.CLASS, 
        "Class": NotificationActions, 
        "uri": '/controller/restui/policy/getActionsListViewData/{appid}',
        "flags": {
            "needs_appid": 1
        },
    },     
    "healthrule" : {
        "type": CallType.CLASS, 
        "Class": HealthRules,
        "uri": '/controller/healthrules/{appid}',
        "flags": {
            "needs_appid": 1,
        },
        "returntype": ReturnType.TEXT,
        "headers": ["id","name","enabled","affectedEntityType"]
    },
    "appinfo" : {
        "type": CallType.CLASS,
        "Class": AppInfo,
        "uri": '/restui/allApplications/applicationById?applicationId={appid}',
        "flags": {
            "needs_appid": 1,
        },
        "headers": ["id", "name", "description", "active", "eumAppName", "createdBy", "createdOn", "modifiedBy", "modifiedOn"]
    },
    "snapshots" : {
        "type": CallType.GET,
        "uri": '/controller/rest/applications/{appid}/request-snapshots?output=JSON&time-range-type=AFTER_TIME&start-time={startepochmillies}&duration-in-mins={durationinmins}&maximum-results=10000&need-props=true',
        "flags": {
            "needs_appid": 1,
            "needs_startepochmillies": 1,
            "needs_duration": 1,
        },
        "headers": ["businessTransactionId", "applicationComponentId", "applicationComponentNodeId", "requireGUID", "userExperience", "URL", "summary"]
    },
    "tiers" : {
        "type": CallType.GET,
        "uri": '/controller/rest/applications/{appid}/tiers?output=JSON',
        "flags": {
            "needs_appid": 1,
        },
        "returntype": ReturnType.JSON,
        "headers": ["name","id","description","numberOfNodes","agentType","type"]
    },
    "nodes" : {
        "type": CallType.GET,
        "uri": '/controller/rest/applications/{appid}/nodes?output=JSON',
        "flags": {
            "needs_appid": 1
        },
        "returntype": ReturnType.JSON,
        "headers": ["machineName","machineOSType","tierName","name","agentType","appAgentVersion","machineAgentVersion"]
    },
    "nodesbytier" : {
        "type": CallType.GET,
        "uri": '/controller/rest/applications/{appid}/tiers/{tiername}/nodes?output=JSON',
        "flags": {
            "needs_appid": 1,
            "needs_tiername": 1,
        },
        "returntype": ReturnType.JSON,
        "headers": ["machineName","machineOSType","tierName","name","agentType","appAgentVersion","machineAgentVersion"]
    },
    "businesstransactions" : {
        "type": CallType.GET,
        "uri": '/controller/rest/applications/{appid}/business-transactions?output=JSON',
        "flags": {
            "needs_appid": 1,
        },
        "returntype": ReturnType.JSON,
        "headers": ["name","id","tierName","entryPointType"]
    },
    "snapshotsbytier": {
        "type": CallType.GET,
        "uri": "/controller/rest/applications/{appid}/request-snapshots?output=JSON&time-range-type=AFTER_TIME&start-time={startepochmillies}&duration-in-mins={durationinmins}&application-component-ids={entityname}",
        "flags": {
            "needs_appid": 1,
            "needs_entity": 1
        },
        "returntype": ReturnType.JSON,
        "headers": ["businessTransactionId", "threadName", "firstInChain", "serverStartTime", "localStartTime", "timeTakenInMilliSecs", "userExperience", "errorOccured", "requestGUID", "summary", "errorSummary", "snapshotExitSequence", "callChain"]
    },
    "bttraffic" : {
        "type": CallType.GET,
        #"uri": '/controller/rest/applications/{appid}/metric-data?output=JSON&metric-path=Business Transaction Performance|Business Transactions|*|*|Calls per Minute',
        "uri": '/controller/rest/applications/{appid}/metric-data?output=JSON&metric-path%3DBusiness%20Transaction%20Performance%7CBusiness%20Transactions%7C%2A%7C%2A%7CCalls%20per%20Minute&time-range-type=BEFORE_NOW&duration-in-mins={durationinmins}',
        "flags": {
            "needs_appid": 1,
        },
        "returntype": ReturnType.JSON,
        "headers": ["metricId", "metricName", "metricPath", "occurrences", "min", "max", "value"]

    },
    "healthrules" : {
        "type": CallType.GET,
        "uri": '/controller/healthrules/{appid}',
        "flags": {
            "needs_appid": 1,
        },
        "returntype": ReturnType.TEXT,
        "headers": ["id","name","enabled","affectedEntityType"]
    },
    "exportapp" : {
        "type": CallType.GET,
        "uri": '/controller/ConfigObjectImportExportServlet?applicationId={appid}',
        "returntype": ReturnType.XML,
        "flags": {
            "needs_appid": 1,
        }
    },
    "exporthealthrulesjson" : {
        "type": CallType.GET,
        "uri": '/controller/healthrules/{appid}?output=JSON',
        "returntype": ReturnType.XML,
        "flags": {
            "needs_appid": 1,
        }
    },
    "exporthealthrulesxml" : {
        "type": CallType.GET,
        "uri": '/controller/healthrules/{appid}',
        "returntype": ReturnType.XML,
        "flags": {
            "needs_appid": 1,
        }
    },
    "exporthealthrulexml" : {
        "type": CallType.GET,
        "uri": '/controller/healthrules/{appid}/?name={entityname}',
        "returntype": ReturnType.XML,
        "flags": {
            "needs_appid": 1,
            "needs_entity": 1
        }
    },
    "exporthealthrulejson" : {
        "type": CallType.GET,
        "uri": '/controller/alerting/rest/v1/applications/{appid}/health-rules/{entityname}?output=JSON',
        "flags": {
            "needs_appid": 1,
            "needs_entity": 1
        }
    },
    "importhealthrulesxml" : {
        "type": CallType.POST,
        "uri": '/controller/healthrules/{appid}/?overwrite=true',
        "flags": {
            "needs_appid": 1,
        }
    },
    "updatehealthrulejson" : {
        "type": CallType.POST,
        "uri": '/controller/alerting/rest/v1/applications/{appid}/health-rules/{entityname}',
        "flags": {
            "needs_appid": 1,
            "needs_entity": 1
        }
    },
    "createhealthrulejson" : {
        "type": CallType.POST,
        "uri": '/controller/alerting/rest/v1/applications/{appid}/health-rules',
        "flags": {
            "needs_appid": 1,
        }
    },
    "exportcustombtrulesxml" : {
        "type": CallType.GET,
        "uri": '/controller/transactiondetection/{appid}/Default Scope/custom',
        "returntype": ReturnType.XML,
        "flags": {
            "needs_appid": 1,
        }
    },
    "importcustombtrulesxml" : {
        "type": CallType.POST,
        "uri": '/controller/transactiondetection/{appid}/Default Scope/custom',
        "flags": {
            "needs_appid": 1,
        }
    },
    "backends" : {
        "type": CallType.GET,
        "uri": '/controller/rest/applications/{appid}/backends?output=JSON',
        "flags": {
            "needs_appid": 1,
        },
        "headers": ["id", "exitPointType", "name"]
    },
    "violations" : {
        "type": CallType.GET,
        "uri": '/controller/rest/applications/{appid}/problems/healthrule-violations?time-range-type=AFTER_TIME&start-time={startepochmillies}&duration-in-mins={durationinmins}&output=JSON',
        "flags": {
            "needs_appid": 1,
        },
        "headers": ["id", "name", "startTimeInMillies", "endTimeInMillies", "triggeredEntityDefinition.entityType", "triggeredEntityDefinition.name", "affectedEntityDefinition.entityType", "affectedEntityDefinition.name"]
    },
    "audit" : {
        "type": CallType.GET,
        "uri": '/controller/ControllerAuditHistory?startTime={startdate}&endTime={enddate}',
        "returntype": ReturnType.JSON,
	"headers": ["userName","apiKeyName","securityProviderType","auditDateTime","action","objectType","objectName","changes"]
    },
    "actions" : {
        "type": CallType.CLASS,
        "Class": Actions,
        "uri": '/controller/actions/{appid}/',
        "flags": {
            "needs_appid": 1,
        },
        "headers": ["name", "actionType", "priority", "httpAction_or_toAddr", "custom_or_subj"]
    },
    "policies" : {
        "type": CallType.CLASS,
        "Class": Policies,
        "uri": '/controller/policies/{appid}/',
        "flags": {
            "needs_appid": 1,
        },
        "headers": ["name", "enabled", "healthrules", "actions"]
    },
    "itocdashboard" : {
        "type": CallType.CLASS,
        "Class": ITOCDashBoard,
        "uri": '/controller/CustomDashboardImportExportServlet?dashboardId={itocdashid}',
    },
    # "licensemodules" : {
    #     "type": CallType.GET,
    #     "uri": '/api/accounts/{accountid}/licensemodules',
    #     "flags": {
    #         "needs_accountid": 1
    #     },
    # },
    "licenseusage" : {
        "type": CallType.CLASS,
        "Class": LicenseUsage,
        "uri": '/api/accounts/{accountid}/licensemodules/usages',
        "flags": {
            "needs_accountid": 1
        },
        "headers": ['createdOnIsoDate', 'agentType', 'avgUnitsUsed', 'minUnitsUsed',
                    'maxUnitsUsed']
    },
    "licenseusagejava" : {
        "type": CallType.CLASS,
        "Class": LicenseUsage,
        "uri": '/api/accounts/{accountid}/licensemodules/java/usages',
        "flags": {
            "needs_accountid": 1
        },
        "headers": ['createdOnIsoDate', 'agentType', 'avgUnitsUsed', 'minUnitsUsed',
                    'maxUnitsUsed']
    },
    "licenseusagedotnet" : {
        "type": CallType.CLASS,
        "Class": LicenseUsage,
        "uri": '/api/accounts/{accountid}/licensemodules/dot-net/usages',
        "flags": {
            "needs_accountid": 1
        },
        "headers": ['createdOnIsoDate', 'agentType', 'avgUnitsUsed', 'minUnitsUsed',
                    'maxUnitsUsed']
    },
    # "appreport" : {
    #     "type": CallType.CLASS,
    #     "Class": AppReport,
    #     "url": ""
    # },
    "roles" : {
        "type": CallType.CLASS,
        "Class": Roles,
        "uri": '/controller/api/rbac/v1/roles',
        "headers": ['id', 'name']
    },
    "hbevent" : {
        "type": CallType.POST,
        "uri": '/controller/rest/applications/{appid}/events?severity=INFO&summary=heartbeatevent&eventtype=CUSTOM&customeventtype=heartbeat' +
               '&propertynames=appname&propertyvalues={appname}' +
               '&propertynames=entityname&propertyvalues={entityname}',
        "flags": {
            "needs_appid": 1,
            "needs_entity": 1
        },
        "returntype": ReturnType.TEXT
    },
    "events" : {
        "type": CallType.GET,
        "uri": '/controller/rest/applications/{appid}/events?' +
               'time-range-type=AFTER_TIME&' +
               'start-time={startepochmillies}&' +
               'duration-in-mins={durationinmins}&' + 
#               'eventtype=APPLICATION_DEVELOPMENT&' +
               'event-types=' +  ",".join(eventtypelist) + 
               '&severities=INFO,WARN,ERROR&output=JSON',
        "flags": {
            "needs_appid": 1
        },
    }#,
    # "mobilecrashgroups" : {
    #     "type": CallType.CLASS,
    #     "Class": MobileAppCrash,
    #     "uri": "/events/query?limit=1000",
    #     "payload": [
    #         {"query": "SELECT * FROM mobile_crash_reports WHERE appkey = \"AD-AAB-ACD-HPK\""}
    #         ]
        # "uri":  "/controller/restui/analytics/searchJson/MOBILE_CRASH_REPORT",
        # "payload": {"query":
        #             {"filtered":
        #              {"query":
        #               {"bool":
        #                {"must":[{"match":{"appkey":{"query":"AD-AAB-ACD-HPK"}}},
        #                         {"match":{"mobileappname":{"query":"edu.mayo.patient"}}},
        #                         {"match":{"platform":{"query":"iOS"}}}
        #                         ]
        #                 }
        #                },
        #               "filter":
        #               {"bool":
        #                {"must":[{"range":{"eventTimestamp":{"from":1724939073408,"to":1725543873408}}},
        #                         {"match_all":{}}
        #                         ]
        #                 }
        #                }
        #               }
        #              },
        #             "size":1000,
        #             "from":0,
        #             "sort":[{"eventTimestamp":{"order":"desc"}}]
        #             }
    #}
}

usage = sys.argv[0] + """(-c|--cred|--credfile)=<filename> <command>
Other options:
    --app|-a=<appname>  or  --allapmapps  or  --allapps
    --tier|tiername=<tiername>
    --entity|entityname=<entityname>
    --file|filename=<filename>
    --debuglvl|debug|d=X
    --startdate|--date|--start=<YYYY-MM-DD:HH:MM:SS>
    --duration=<num_of_mins>
    --output|format|o=(text,csv,json)
    --cert|certfile=<file_with_ssl_cert>

Valid commands include: 
    """ + " | ".join(sorted(commandlist.keys()))


def gettimes ():
    timeparams = {}
    api_dt_format = "%Y-%m-%dT%H:%M:%S.000-0600"
    option_dt_format = "%Y-%m-%d:%H:%M:%S"

    now = datetime.datetime.now()
    if "duration" in options:
        timeparams['durationinmins'] = int(options['duration'])
    else:
        timeparams['durationinmins'] = 24 * 60

    if "startdate" in options:
        startdate = datetime.datetime.strptime (options['startdate'], option_dt_format)
        timeparams['startdate'] = startdate.strftime(api_dt_format)
        timeparams['startepochsecs'] = int (startdate.timestamp())
    else:
        timeparams['startepochsecs'] = int (now.timestamp() - (timeparams['durationinmins'] * 60))
        startdate = datetime.datetime.fromtimestamp (timeparams['startepochsecs'])
        timeparams['startdate'] = startdate.strftime (api_dt_format)

    enddate = now
    if "enddate" in options:
        enddate = datetime.datetime.strptime(options['enddate'], option_dt_format)
        timeparams['enddate'] = enddate.strftime (api_dt_format)
        timeparams['endepochsecs'] = int (enddate.timestamp())
    else:
        enddate = datetime.datetime.fromtimestamp(timeparams['startepochsecs'] + (timeparams['durationinmins'] * 60))
        timeparams['endepochsecs'] = int (now.timestamp())

    if "timeframe" in options:
        # convert "last x months" to startdate and enddate
        if "year" in options['timeframe'].lower():
            years = int(options['timeframe'].split()[1])
            startdate = enddate - relativedelta.relativedelta(years=years)
        elif "month" in options['timeframe'].lower():
            months = int(options['timeframe'].split()[1])
            startdate = enddate - relativedelta.relativedelta(months=months)
        elif "week" in options['timeframe'].lower():
            weeks = int(options['timeframe'].split()[1])
            startdate = enddate - relativedelta.relativedelta(weeks=weeks)
        elif "day" in options['timeframe'].lower():
            days = int(options['timeframe'].split()[1])
            startdate = enddate - relativedelta.relativedelta(days=days)
        else:
            print ("Error: unrecognized timeframe " + options['timeframe'])
            print (usage)
            sys.exit(1)
        timeparams['startdate'] = startdate.strftime(api_dt_format)
        timeparams['startepochsecs'] = int (startdate.timestamp())

    timeparams['startepochmillies'] = timeparams['startepochsecs'] * 1000
    timeparams['endepochmillies'] = timeparams['endepochsecs'] * 1000
    timeparams['enddate'] = enddate.strftime (api_dt_format)

    DEBUGOUT (6, "time params: %s", (str (timeparams)))

    return timeparams
    
def read_credfile (credfilename):
    credinfo = configparser.ConfigParser()
    credinfo.read(credfilename)
    DEBUGOUT (6, "read_credfile: credentials: %s", (list(credinfo.items())))
    if "credentials" in credinfo:
        DEBUGOUT (7, "read_credfile: credentials: %s", (list(credinfo['credentials'])))
        credinfo = credinfo['credentials']

    if not "hosturl" in credinfo \
       or not "username" in credinfo \
       or not "clientsecret" in credinfo \
       or not "authuri" in credinfo:
        print ("credfile requires 'hosturl', 'username', 'clientsecret', 'authuri'")
        sys.exit(1)
    return credinfo

def parse_arguments (options):
    global timeparams
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],"?hc:a:d:o:",
                                   ["help",
                                    "cred=",
                                    "creds=",
                                    "credfile=",
                                    "allapmapps",
                                    "allapps",
                                    "app=",
                                    "appname=",
                                    "mobileappid=",
                                    "application=",
                                    "tier=",
                                    "tiername=",
                                    "entity=",
                                    "entityname=",
                                    "file=",
                                    "filename=",
                                    "debuglevel=",
                                    "debuglvl=",
                                    "debug=",
                                    "startdate=",
                                    "enddate=",
                                    "timeframe=",
                                    "date=",
                                    "start=",
                                    "duration=",
                                    "mins=",
                                    "output=",
                                    "format=",
                                    "inputfile="
                                    ])
    except getopt.GetoptError:
        print (usage)
        sys.exit(2)
    for opt, arg in opts:
        if opt in ('-?', '-h', '--help'):
            print (usage)
            sys.exit()
        elif opt in ('-c', '--cred', '--creds', '--credfile'):
            options['credfile'] = arg
        elif opt in ('-a', '--app', '--appname', '--application'):
            options['application'] = arg
        elif opt in ('--mobileappid'):
            options['mobileappid'] = arg
        elif opt in ('--allapmapps'):
            options['allapmapps'] = True
        elif opt in ('--allapps'):
            options['allapps'] = True
        elif opt in ('--tier', '--tiername'):
            options['tier'] = arg
        elif opt in ('--entity', '--entityname'):
            options['entityname'] = arg
        elif opt in ('--file', '--filename'):
            options['filename'] = arg
        elif opt in ('-d', '--debug', '--debuglvl', '--debuglevel'):
            global debuglevel
            debuglevel = int(arg)
            options['debuglevel'] = arg
        elif opt in ('--startdate', '--date', '--start'):
            options['startdate'] = arg
        elif opt in ('--enddate'):
            options['enddate'] = arg
        elif opt in ('--timeframe'):
            options['timeframe'] = arg
        elif opt in ('--duration', '--mins'):
            options['duration'] = arg
        elif opt in ('-o', '--output', '--format'):
            if arg == "csv":
                options['outputformat'] = OutputFormat.CSV
            elif arg == "json":
                options['outputformat'] = OutputFormat.JSON
            elif arg == "text":
                options['outputformat'] = OutputFormat.TEXT
            else:
                print ("Error: unrecognized output format " + arg + ". must be one of json, csv, text")
                print (usage)
                sys.exit(1)
        elif opt in ('--inputfile'):
            options['inputfile'] = arg 

    command = ""
    if len(args) == 1:
        command = args[0]
    if not command in commandlist:
        print ("Error: no command given or command '" + command + "' not found in list")
        print (usage)
        sys.exit(1)

    if not "credfile" in options or not os.path.isfile(options["credfile"]):
        print ("Requires credential file")
        print (usage)
        sys.exit(1)


    timeparams = gettimes()
    if "inputfile" in options:
        if not os.path.isfile(options["inputfile"]):
            print ("Error: input file " + options["inputfile"] + " not found")
            sys.exit(1)
        
    return options, command

    
def docommand (options, command, credinfo, ApplicationList):

    commandinfo = commandlist[command]
    DEBUGOUT (2, "docommand: %s type: %s url: %s", (command, commandinfo["type"], commandinfo["uri"]))

    if commandinfo["type"] == CallType.CLASS:
        commandobj = commandinfo["Class"](commandinfo, credinfo, options, ApplicationList)
    else:
        commandobj = API_Call (commandinfo, credinfo, options, ApplicationList)

    result = commandobj.sendcall ({})

    print (str(commandobj))

def doallcommand (options, command, credinfo, ApplicationList):

    allresults = []
    commandinfo = commandlist[command]
    DEBUGOUT (2, "doallcommand: %s type: %s url: %s", (command, commandinfo["type"], commandinfo["uri"]))

    applist = ApplicationList.get_all_apmappids()
    for appname in applist.keys():
        DEBUGOUT (3, "doall: application %s", {appname})
        options['application'] = appname
        if commandinfo["type"] == CallType.CLASS:
            commandobj = commandinfo["Class"](commandinfo, credinfo, options, ApplicationList)
        else:
            commandobj = API_Call (commandinfo, credinfo, options, ApplicationList)
        result = commandobj.sendcall ({})

        if options['outputformat'] == OutputFormat.JSON:
            allresults.append ({"name": appname, "data": commandobj.callresult.json()})
        else:
            thisresult = commandobj.parse_results()
            if len(thisresult) > 0:
                thisresult.pop(0)
            allresults.append ({"name": appname, "data": thisresult})
            # allresults[appname] = thisresult

    allcommandobj = {}
    if commandinfo["type"] == CallType.CLASS:
        allcommandobj = commandinfo["Class"](commandinfo, credinfo, options, ApplicationList)
    else:
        allcommandobj = API_Call (commandinfo, credinfo, options, ApplicationList)
        
    if options['outputformat'] == OutputFormat.JSON:
        print (json.dumps(allresults, indent=4))
    else:
        headers = allcommandobj.get_headers()
        headers.insert (0, "application_name")
        result_table = [headers]
        for appinfo in allresults:
            appname = appinfo["name"]
            for row in appinfo["data"]:
                row.insert(0, appname)
                result_table.append(row)
        if options['outputformat'] == OutputFormat.CSV:
            print (allcommandobj.str_csv(result_table))
        else:
            print (allcommandobj.str_table(result_table))

options, command = parse_arguments(options)

DEBUGOUT (3, "options are: " + str(options), {})

credinfo = read_credfile (options['credfile'])

commandinfo = commandlist['applications']
ApplicationList = commandinfo['Class'](commandinfo, credinfo, options, {})

if "allapmapps" in options:
    doallcommand (options, command, credinfo, ApplicationList)
else:
    docommand (options, command, credinfo, ApplicationList)
