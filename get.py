import json, os, time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from dateutil import rrule
from tqdm import trange
from multiprocessing import Pool
from itertools import repeat

import log

userids = [] #Will contain all user objects after download
completed_users = []
initial_import_size = 0

def UserInList(user, userlist):
    for u in userlist:
        if (u['id'] == user['id']):
            return True
    return False

#Retrieves all download links for given keyword arguements and the next_page_token - called by this class only as it doesn't handle much more than that and it is used for pagination.
def PageDLLinks(kw_args, token, user, client, dt, statsObject):
    bulk_recordings = []
    recordings_response = client.recording.list(**kw_args, next_page_token=token) #Get the next page using the given args.
    recordings = json.loads(recordings_response.content) #Load into a json object
    
    try: #mainly in a try/catch statement as it will throw a KeyError if there is no 'next_page_token' attribute.
        for meeting in recordings['meetings']:
            bulk_recordings.append(meeting)
    
        if(recordings['next_page_token'] != ""): #since we're not handling pagination for the moment, if there is a next page token then post the warning.
            to_date = dt + relativedelta(months=+1)
            log.LogWarn(user['first_name'] + " " + user['last_name'] + " has more than 300 recordings for the time period of " + str(dt.year) + '-' + str(dt.month) + '-' + str(dt.day) + " to " + str(to_date.year) + '-' + str(to_date.month) + '-' + str(to_date.day) +"! This script does not support more than 300 recordings in a month!")
            next_recordings = PageDLLinks(kw_args, recordings['next_page_token'], user, client, dt, statsObject)
            for recording in next_recordings:
                bulk_recordings.append(recording)
            
    except KeyError:
        log.LogError("KeyError with GET request!", statsObject) #this was a debug line for catching when the token has expired (if the token is expired it returns a completely different json). In general this catches when the returned json isn't what was expected - check keyerror.json
        log.ExportToFile("keyerror.json", recordings)
    
    return bulk_recordings
    
#This function downloads the files for a given user in a given one month time period.
def GetDLLinks(dt, user, client, statsObject):
    bulk_recordings = []

    to_date = dt + relativedelta(months=+1) #calculate the end date
    kw_args = {'user_id' : user['id'], 'page_size' : '300', 'from' : str(dt.year) + '-' + str(dt.month) + '-' + str(dt.day), 'to': str(to_date.year) + '-' + str(to_date.month) + '-' + str(to_date.day)} #formulate the keyword arguments.
    done = False
    count = 0
    while(not done):
        try:
            recordings_response = client.recording.list(**kw_args) #Make the call
            done = True
        except:
            time.sleep(0.5)
            count = count + 1
            if (count == 4):
                log.LogError("Failed to download user recording data! Rerun for this user or manually download for the following user: " + user['first_name'] + " " + user['last_name'], statsObject)
                done = True
                return []
    recordings = json.loads(recordings_response.content) #Load into JSON object
        
    try: #In a try/catch as any of the below ['whatever'] calls will throw an exception if they don't exist (token expiration, http error, etc)
        for meeting in recordings['meetings']:
            bulk_recordings.append(meeting)
    
        if(recordings['next_page_token'] != ""): #check if we have a next page token (i.e. more than 300 recordings and needs another API call)
            log.LogOK(user['first_name'] + " " + user['last_name'] + " has more than 300 recordings for the time period of " + str(dt.year) + '-' + str(dt.month) + '-' + str(dt.day) + " to " + str(to_date.year) + '-' + str(to_date.month) + '-' + str(to_date.day) +"!")
            next_recordings = PageDLLinks(kw_args, recordings['next_page_token', user, client, dt], statsObject) #passes the call over to the recursive function to handle.
            for recording in next_recordings:
                bulk_recordings.append(recording)
            
    except KeyError:
        log.LogError("KeyError with GET request!", statsObject) #this was a debug line for catching when the token has expired. In general this catches when the returned json isn't what was expected - check keyerror.json
        log.ExportToFile("keyerror.json", recordings)
    return bulk_recordings

#Top level function for getting the download links for download files for a user.
def GetDownloadLinks(user, client, statsObject):
    start_date = datetime(2019,8,1) #This is the earliest date I could find a recording for on the Knox Zoom Organisation. If this script is being used for a different org/account, it may need to be changed. It is important that this is rather accurate, as added months will slow the program down a lot. 1 extra month = 1 extra HTTP GET request per person
    end_date = datetime.today() #End date is obvs today.

    log.PrintOK("Fetching recordings info for user '" + user['id'] + ": " + user['first_name'] + " " + user['last_name'] + "'")
    log.LogOK("Fetching recordings info for user ID '" + user['id'] + ": " + user['first_name'] + " " + user['last_name'] + "'")
    
    
    dt_list = []
    for dt in rrule.rrule(rrule.MONTHLY, dtstart=start_date, until=end_date): #this setup iterates through a time period by 1 month at a time. Zoom API restricts recording lists to 1 month time periods max 
        dt_list.append(dt) #put each date into the list
    recordings = []
    concur_dls = 5 #be careful modifying how many concurrent downloads are allowed, as I found some issues occuring around integrity and/or simply freezing up (or even maximum recursion errors once! scary)
    for i in trange(int(len(dt_list) // concur_dls) + 1): #iterate over each month in the list
        with Pool() as pool:
            cur_dts = []
            for j in range(concur_dls):
                if(i*concur_dls+j < len(dt_list)): #setup the cur_dts list for the amount of concur downloads.
                    cur_dts.append(dt_list[i*concur_dls+j])
            rec = pool.starmap(GetDLLinks, zip(cur_dts, repeat(user), repeat(client), repeat(statsObject))) #start the concurrent downloads with a starmap for multiple arguments.
            for re in rec:
                if(not len(re) == 0): #remove all empty recordings list - this is a by-product of how it appends things above.
                    recordings.append(re)
    final_recordings = []
    for r in recordings:
        for meeting in r: #removes a layer of encapsulation - not entirely sure why this comes about but it does, and it needs to be handled.
            final_recordings.append(meeting)
    return final_recordings

#Imports the users from the user_cache.json file at the root. Performs no other checks!
def ImportUsers(): 
    with open('user_cache.json') as json_file:
        data = json.load(json_file)
    data['created'] = datetime.strptime(data['created'], "%Y-%m-%dT%H:%M:%S.%f")
    log.PrintOK("User(s) imported from user_cache.json")
    log.LogOK("User(s) imported from user_cache.json")
    return data
    
def ImportCompleted():
    with open('completed_users.json') as json_file:
        data = json.load(json_file)
    log.PrintOK( str(len(data)) + " User(s) imported from completed_users.json")
    log.LogOK( str(len(data)) + " User(s) imported from completed_users.json")
    return data
    
def ExportCompleted():
    log.ExportToFile("completed_users.json", completed_users)
    log.PrintOK( str(len(completed_users)) + " User(s) exported to completed_users.json")
    log.LogOK( str(len(completed_users)) + " User(s) exported to completed_users.json")
    
#Exports the userids variable to the user_cache.json file - does not delete it, make sure it is deleted before calling. Also adds in the creation date for validating the info.
def ExportUsers(users):
    data = {}
    data['created'] = datetime.now().isoformat()
    data['users'] = users
    log.ExportToFile("user_cache.json", data)
    log.PrintOK("Users exported to user_cache.json")
    log.LogOK("Users exported to user_cache.json")

#Recursive function to loop through all pages and present them into the userid global list
def GetNextUsers(client, token): #token here refers to the next_page_token not the client token.
    if(token == ""): #if this is the first request, no token is provided, but the arguement must be met cause im too lazy to make a different signature for the function.
        user_list_response = client.user.list(page_size=300) #page_size 300 is the max as specified in the Zoom API. this is maximum amount we an pull in one request.
    else:
        user_list_response = client.user.list(page_size=300, next_page_token=token) #passes the token with the request i.e. the next page
    user_list = json.loads(user_list_response.content) #load it into a json object
    
    for user in user_list['users']: #this was the simpliest way to put all the json objects into a list. (could be wrong but it works and its 2 lines so w/e)
        userids.append(user)
    
    log.PrintOK("Pulled " + str(len(user_list['users'])) + " users, cumulatively at " + str(len(userids)) + " users")
    log.LogOK("Pulled " + str(len(user_list['users'])) + " users, cumulatively at " + str(len(userids)) + " users")
    if(user_list['next_page_token'] != ""):
        GetNextUsers(client, user_list['next_page_token']) #if this isn't the last page, call this method again with the next page token from the response we got.
        #note that there is no return of data. Since we appended the data to the userids variable, no return is necessary.

#This method starts the download of users and then exports them to the user cache file.
def StartUserDownload(client):
    log.PrintOK("Starting download of user list")
    log.LogOK("Starting download of user list")
    
    GetNextUsers(client, "") #Empty token is provided as there isn't a next_page_token to give - this will pull the first page of the user list.
    
    log.PrintOK('Downloaded ' + str(len(userids)) + ' users')
    log.LogOK('Downloaded ' + str(len(userids)) + ' users')
    ExportUsers(userids) #export the users to the user cache file so that we can run commands today in quick succession - don't need to spend 30 seconds pulling down the userlist.

def UserCompleted(user):
    if not UserInList(user, completed_users):
        completed_users.append(user)
        ExportCompleted()

#Gets all the users for an organisation given a logged in client object (either from a valid cache of users or from the Zoom API, it will decide)
def GetUsers(client):
    try:
        user_import = ImportUsers() #tries to import the users.
        
        if(user_import['created'] + timedelta(days=1) < datetime.now()): #check if the user cache was made in the last 24 hours, and if not, redownload the user list. If it is current it puts the data into the userids global variable.
            log.PrintOK("User Cache is out of date, redownloading...")
            log.LogOK("User Cache is out of date, redownloading...")
            os.remove("user_cache.json")
            StartUserDownload(client) #exporting of users is done in this method and does not need to be considered here.
            
        else:
            for user in user_import['users']:
                userids.append(user)
    except: #this catches any invalid file name exceptions (i.e. no user cache exists) errors and just starts the download of users.
        StartUserDownload(client)
        
def ContGetUsers(client):
    GetUsers(client)
    try:
        user_import = ImportCompleted()
        
        for user in user_import:
            if not UserInList(user, completed_users):
                completed_users.append(user)
    except FileNotFoundError:
        ExportCompleted()