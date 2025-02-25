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

timeparams = {
    "startdate": "",
    "enddate": "",
    "startepochsecs": "",
    "startepochmillies": "",
    "durationinmins": "",
}
options = {"outputformat": OutputFormat.TEXT}
debuglevel = 0
ApplicationList = None

def DEBUGOUT (level, message, args):
    if debuglevel >= level:
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
    params = {'accountid': "", 'appid': "", 'appname': "", 'tiername': "", 'entityname': ""}
    
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
            result = requests.put (url, headers=headers, verify=False)

        if not result.ok:
            print ("query " + url + " result: " + str(result) + " " + result.reason)
            if not "allapmapps" in self.options:
                exit (1)

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
        "returntype": ReturnType.XML,
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

    timeparams['startepochmillies'] = timeparams['startepochsecs'] * 1000
    enddate = datetime.datetime.fromtimestamp (timeparams['startepochsecs'] + (timeparams['durationinmins'] * 60))
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
                                    "date=",
                                    "start=",
                                    "duration=",
                                    "mins=",
                                    "output=",
                                    "format=",
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
