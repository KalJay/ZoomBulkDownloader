import shutil, traceback, functools, os
from pathlib import Path
from dateutil.relativedelta import relativedelta
from multiprocessing import Pool
from tqdm import trange
from itertools import repeat

import log, get, sess

#Downloads a file from a given url to a directory/name given by filedir (full path including name and extension) - this function is usually run by the script in a Pool for "multithreading" (read: multiprocessing)
def DownloadFile(url, filedir, statsObject):
    log.LogDebug("Opening session")
    
    try:
        r = sess.GetSession().get(url, stream=True, allow_redirects=True, timeout=240) #Open the file stream
    
        log.LogDebug("Session opened")
        
        if r.status_code != 200: #HTTP error handling
            r.raise_for_status()  # Will only raise for 4xx codes, so...
            raise RuntimeError(f"Request to {url} returned status code {r.status_code}")
        log.LogDebug("Starting download")
        r.raw.read = functools.partial(r.raw.read, decode_content=True)  # Decompress if needed
        with r.raw as r_raw:
            with open(filedir, 'wb') as out: #Open the file and write the contents of the file stream
                log.LogDebug("Downloading file")
                shutil.copyfileobj(r_raw, out)
        if(os.path.isfile(Path(filedir))):
            statsObject.AddDownloadSize(os.path.getsize(Path(filedir)))
    except:
        log.LogError("Error downloading the file at '" + url + "' to file/directory " + filedir, statsObject)
        log.LogError(traceback.format_exc(), statsObject) #This is only printed to the console if you try to Ctrl + C the process. If the program is hanging on downloads, Ctrl + C and this stack trace could provide hints to debug.

#This function takes a list of download links and file locations and names to download to and uses multiprocessing to concurrently download a specified amount of downloads.
def DownloadFiles(urls, filedirs, statsObject):
    concur_dls = 3 #be careful modifying how many concurrent downloads are allowed, as I found some issues occuring around integrity and/or simply freezing up (or even maximum recursion errors once! scary)
    if(len(urls) > 0):
        for i in trange(int(len(urls) // concur_dls) + 1): #math to iterate the correct amount of times
            with Pool() as pool: #Create the pool to start multiprocessing
                for j in range(concur_dls): #this is all constructing the lists of urls and download locations to pass into the "thread"
                    cur_urls = []
                    cur_filedirs = []
                    if(i*concur_dls+j < len(urls)):
                        cur_urls.append(urls[i*concur_dls+j])
                        cur_filedirs.append(filedirs[i*concur_dls+j])
                pool.starmap(DownloadFile, zip(cur_urls, cur_filedirs, repeat(statsObject))) #starmap is necessary to pass multiple arguements, rip TQDM progress bars working well with this

#This function exists to make sure that no file is skipped over for some reason. It does an integrity check and calls itself again if necessary.
def ReDownloadFiles(urls, dlpaths, statsObject):
    for i in trange(len(urls)):
        DownloadFile(urls[i], dlpaths[i], statsObject) #I decided to not bother with multiprocessing here as this shouldn't download too many, and if integrity is a concern here (which it is) then we don't want any issues that multiprocessing sometimes seemed to give.
    
    missingURLs = []
    missingDLPaths = []
    for i in range(len(urls)): #Iterate through the given list and check the files are there.
        if(Path(dlpaths[i]).is_file() == False):
            missingURLs.append(urls[i])
            missingDLPaths.append(dlpaths[i])
    if(len(missingURLs) > 0):
        log.LogWarn("Redownload missed " + str(len(missingURLs)) + " files, trying again")
        ReDownloadFiles(missingURLs, missingDLPaths) #if missing files found, recursively call this again with the files that were found missing. Pray that you don't get any max recursion errors.
    else:
        log.PrintOK("Integrity Check completed, no missing files")
        log.LogOK("Integrity Check completed, no missing files")

#Iterates over a list of meetings and downloads all the recording files to folders for the specified user.
def DownloadMeetings(user, meetings, client, statsObject):
    downloads = 0
    urls = []
    filedirs = []
    user_updated_flag = False
    for meeting in meetings: #iterate over each meeting
            for file in meeting['recording_files'] : #iterate over each file in said meeting
                folderdir = 'Downloads/' + (user['first_name'] + ' ' + user['last_name']).rstrip() + '/' + str(meeting['start_time']) + '-' + str(meeting['id'])
                dlpath = folderdir + '/' + str(file['recording_start']) + ' - ' + str(file['id']) + '.' + str(file['file_extension']).lower() #formulate the file paths and folder directories.
                folderdir = folderdir.replace(":", "-") #replace the colons in the start time with dashes, as colons are disallowed for file names in Windows.
                dlpath = dlpath.replace(":", "-")
                if(Path(dlpath).is_file() == False):
                    #Waits until the final check to make the directories/files - this means there are no empty directories, all directories created have files
                    Path(folderdir).mkdir(parents=True, exist_ok=True) #this is safe i.e. CREATE IF NOT EXISTS levels of safe
                    urls.append(file['download_url'] + "?access_token=" + client.config['token'])
                    filedirs.append(dlpath)
                    statsObject.IncrementDownloadsCount()
                    downloads = downloads + 1
                    if(not user_updated_flag):
                        user_updated_flag = True
                        statsObject.IncrementUpdatedUsers()
                else:
                    #Should only happen if you've run this multiple times - will not overwrite to save processing time - it is assumed that a specific recording does not change due to the naming format (uses the unique file identifier)
                    log.LogWarn(dlpath + " already exists!")
    DownloadFiles(urls, filedirs, statsObject)
    
    #this is all integrity checking from here.
    missingURLs = []
    missingFileDirs = []
    for meeting in meetings:
        for file in meeting['recording_files'] :
                folderdir = 'Downloads/' + (user['first_name'] + ' ' + user['last_name']).rstrip() + '/' + str(meeting['start_time']) + '-' + str(meeting['id'])
                dlpath = folderdir + '/' + str(file['recording_start']) + ' - ' + str(file['id']) + '.' + str(file['file_extension']).lower()
                folderdir = folderdir.replace(":", "-")
                dlpath = dlpath.replace(":", "-")
                if(Path(dlpath).is_file() == False): #if the file is found missing, add it to the lists.
                    missingURLs.append(file['download_url'] + "?access_token=" + client.config['token'])
                    missingFileDirs.append(dlpath)
                    log.LogWarn("Integrity check found the following file missing!")
                    log.LogWarn(dlpath)
                    
    if(len(missingFileDirs) > 0): #if we have missing files, start the redownload process, which tries to download the file and then performs an integrity check. If it is still missing, tries again, and again, and again, etc.
        log.LogWarn("Not all files were downloaded for user " + user['first_name'] + " " + user['last_name'] + ":" + str(user['id'] + ", trying again"))
        ReDownloadFiles(missingURLs, missingFileDirs, statsObject)
    else:
        log.PrintOK("Integrity Check completed, no missing files")
        log.LogOK("Integrity Check completed, no missing files")
    get.UserCompleted(user)
    statsObject.IncrementUserCount()
    return downloads

#Downloads all recordings for an organisation - this will catch pages for (rare) cases where staff members have more than 300 recordings in a month.
def DownloadAllRecordings(client, statsObject):
    Path('Downloads').mkdir(parents=True, exist_ok=True) #Make the downloads folder
    log.PrintOK("Directory 'Downloads' Created")
    log.LogOK("Directory 'Downloads' Created")
    log.PrintOK("Starting downloads of recordings")
    log.LogOK("Starting downloads of recordings")
    userCount = len(get.completed_users)
    downloads = 0
    

    for user in get.userids: #Iterates over all the users that we should already have downloaded/imported
        log.LogDebug("Is user" + user['first_name'] + " " + user['last_name'] + " in list? " + str(get.UserInList(user, get.completed_users)))
        statsObject.IncrementUserCount()
        if(not get.UserInList(user, get.completed_users)):
            meetings = get.GetDownloadLinks(user, client, statsObject)
            downloads = DownloadMeetings(user, meetings, client, statsObject) #Pass the information down the chain to start the downloads for the user
            userCount = userCount + 1
            log.PrintOK("Users Processed: " + str(userCount + get.initial_import_size) +", Recordings Downloaded: " + str(downloads) + ", Total Progress: " + str(round(userCount/len(get.userids)*100)) + "%")

#Downloads all recordings for a specific username - does need to download all users again to find the users ID
def DownloadRecordingsForUsername(username, client, statsObject):
    log.PrintOK("Searching for individual user '" + username + "'")
    log.LogOK("Searching for individual user '" + username + "'")

    userFound = False #flag for when user is found
    for user in get.userids: #Standard 'FIND' pattern
        if(user['email'].startswith(username)): #Once found
            log.PrintOK("Downloading recordings for user '" + username + "' with ID '" + str(user['id']) + "'")
            log.LogOK("Downloading recordings for user '" + username + "' with ID '" + str(user['id']) + "'")
            
            userFound = True #raise the flag
            meetings = get.GetDownloadLinks(user, client, statsObject) #dowload the list of meetings for the user
            
            Path(log.logs_DIRECTORY + "/Raw User Dumps").mkdir(parents=True, exist_ok=True) #create the directory to dump the user JSON info - for debugging or other use
            log.ExportToFile(log.logs_DIRECTORY + "/Raw User Dumps/" + username + ".json", meetings) #dump the info
            
            downloads = DownloadMeetings(user, meetings, client, statsObject) #download the meetings
            log.PrintOK("Downloaded " + str(downloads) + " files for " + username)
            log.LogOK("Downloaded " + str(downloads) + " files for " + username)
    if(userFound == False):            #catch when the username it isn't found in the org
        log.LogError("Username not found!", statsObject)