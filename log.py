import json
from pathlib import Path
from datetime import datetime

logs_DIRECTORY = "Logs" #The name/directory of the logs folder

DEBUG = False

#Prints the given line to console with a timestamp
def PrintOK(line):
    dt_string = datetime.now().strftime("%Y/%m/%d-%H:%M:%S") #Get current time
    print(dt_string + ": " + line)

#Basic Log function - designed to be wrapped and not really for use outside of this class
def Log(filepath, line):
    Path(logs_DIRECTORY).mkdir(parents=True, exist_ok=True) #Create Logs Directory if doesn't exist

    dt_string = datetime.now().strftime("%Y/%m/%d-%H:%M:%S") #Get current time
    
    with open(filepath, "a", encoding="utf-8") as logfile:
        logfile.write(dt_string + ": " + line + '\n') #Append line to end of log file along with the timestamp

def LogWarn(line): #Wrapper for Log()
    line = "WARNING: " + line
    
    PrintOK(line)
    Log(logs_DIRECTORY + "/warnings.txt", line)

def LogError(line, statsObject): #Wrapper for Log()
    line = "ERROR: " + line
    statsObject.IncrementErrorsCount()
    
    PrintOK(line)
    Log(logs_DIRECTORY + "/errors.txt", line)

def LogOK(line): #Wrapper for Log()
    Log(logs_DIRECTORY + "/log.txt", line)
    
def LogDebug(line):
    line = "DEBUG: " + line
    
    if(DEBUG):
        PrintOK(line)
    Log(logs_DIRECTORY + "/debug.txt", line)

#Generic Logging/Debugging Function that posts the content to a file - does not handle creating a directory for file_name
def ExportToFile(file_name, content):
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(content, f, ensure_ascii=False, indent=4)
