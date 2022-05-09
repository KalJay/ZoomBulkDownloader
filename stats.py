import os, log
from datetime import datetime
from tqdm.auto import tqdm

class Stats(object):

    def __init__(self):
        self.total_user_count = 0
        self.total_updated_users = 0

        self.startTime = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")
        self.endTime = ""

        self.total_download_size = 0
        self.total_downloads = 0

        self.total_errors = 0

    def GetFolderSize(self):
        log.PrintOK("Calculating total file size of backup...")
        log.LogOK("Calculating total file size of backup...")
        size = 0
        for path, dirs, files in tqdm(os.walk("Downloads")):
            for f in files:
                fp = os.path.join(path, f)
                size += os.path.getsize(fp)
        return self.format_bytes(size)

    def SetStartTime(self):
        self.startTime = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")

    def SetEndTime(self):
        self.endTime = datetime.now().strftime("%Y/%m/%d-%H:%M:%S")

    def format_bytes(self, size):
        power = 2**10
        n = 0
        power_labels = {0 : '', 1: 'k', 2: 'm', 3: 'G', 4: 'T', 5: 'P', 6: 'E'}
        while size > power:
            size /= power
            n += 1
        return str("{:.2f}".format(size)) + str(power_labels[n]+'b')

    def IncrementUserCount(self):
        self.total_user_count += 1

    def IncrementUpdatedUsers(self):
        self.total_updated_users += 1

    def AddDownloadSize(self, dlSize):
        self.total_download_size += dlSize
    
    def IncrementDownloadsCount(self):
        self.total_downloads += 1

    def IncrementErrorsCount(self):
        self.total_errors += 1
    
    def GetTotalDLSize(self):
        return self.format_bytes(self.total_download_size)

    def GenerateReport(self):
        report = '----------------------------------------\n\n'

        report += 'Zoom Bulk Download Report\n\n'

        report += 'Time Started: ' + str(self.startTime) + '\n'
        report += 'Time Finished: ' + str(self.endTime) + '\n\n'
        
        report += 'Total Errors: ' + str(self.total_errors) + '\n\n'

        report += 'Total Users Processed: ' + str(self.total_user_count) + '\n'
        report += 'Total Users Updated: ' + str(self.total_updated_users) + '\n\n'

        report += 'Total Data Downloaded: ' + str(self.GetTotalDLSize()) + '\n'
        report += 'Current Size of Local Data: ' + str(self.GetFolderSize()) + '\n'
        report += 'Total Downloaded Files: ' + str(self.total_downloads) + '\n\n'

        report += '----------------------------------------\n'
        return report
    


