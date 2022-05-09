import download, log, get, client, sess, stats, emails
import sys , os, traceback
from multiprocessing import freeze_support

#prints the help info.
def PrintHelp():
    print("----------------------------------------------------------------------------------------------")
    print("This script provides functionality for downloading recordings in bulk from a Zoom organisation")
    print("----------------------------------------------------------------------------------------------")
    print("USAGE:")
    print(" - As is, no arguments - will download all recordings for all users")
    print(" - 'user' <username> - will download all recordings for specific username [ensure this is correct as it will take some time to figure out if its wrong]")
    print(" - 'cont' - will recover from a crash/freeze and continue from where it left off last")
    print(" - Appending the '-NoEmail' tag will not send an email report")

def GetSession():
    return sess.globalSess

#the main function - this is the entry point for the program.
def main():
    sess.CreateSession()
    client.CreateZoomClient()
    
    #Changing the local working directory to the QNAP - modify as needed
    os.chdir(r"")
    log.LogOK("Current working directory: {0}".format(os.getcwd()))
    
    no_email_flag = False

    global statsObject
    statsObject = stats.Stats()
    #Argument handling
    args = sys.argv[1:]
    if(len(args) > 0):
        for arg in args:
            if (arg == "-NoEmail"):
                no_email_flag = True
        match args[0]:
            case "user": #For the 'user' argument
                get.GetUsers(client.zoom_client) #download/update user list
                download.DownloadRecordingsForUsername(args[1], client.zoom_client, statsObject) #download the recordings for the specified username
                statsObject.SetEndTime()
                report = statsObject.GenerateReport()
                print(report)
                log.LogOK(report)
                if(not no_email_flag):
                    emails.SendReport(report)
                    pass
            case "help": #Help print
                PrintHelp()
            case "cont":
                get.ContGetUsers(client.zoom_client)
                download.DownloadAllRecordings(client.zoom_client, statsObject)
                statsObject.SetEndTime()
                report = statsObject.GenerateReport()
                print(report)
                log.LogOK(report)
                if(not no_email_flag):
                    emails.SendReport(report)
                    pass
            case "-NoEmail":
                get.GetUsers(client.zoom_client) #download/update user list
                download.DownloadAllRecordings(client.zoom_client, statsObject) #download the meetings for entire org
                statsObject.SetEndTime()
                report = statsObject.GenerateReport()
                print(report)
                log.LogOK(report)
            case _:
                log.PrintOK("Unknown argument '" + args[0] + "', use the 'help' argument for help")
    else: #If no arguments, proceed as normal
        get.GetUsers(client.zoom_client) #download/update user list
        download.DownloadAllRecordings(client.zoom_client, statsObject) #download the meetings for entire org
        statsObject.SetEndTime()
        report = statsObject.GenerateReport()
        print(report)
        log.LogOK(report)
        if(not no_email_flag):
            emails.SendReport(report)

#this is a necessary addition in order to be able to handle multi-processing. It's also why there is a main function to begin with.
if __name__=="__main__":
    freeze_support()
    try:
        main()
    except Exception as err:
        log.LogError(traceback.format_exc(), statsObject)


