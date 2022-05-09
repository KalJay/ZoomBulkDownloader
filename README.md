# ZoomBulkDownloader
Bulk downloads recordings from Zoom Cloud storage

The Zoom Bulk Download script provides tools to download recordings and other files from all or specific users in an organisation. It does so using the Zoom API and the zoomus python library.

Documentation
Arguments
If the script is run with no arguments, the script will attempt to run from the beginning and download the recording files for every user in the organisation. It will then print the report to the console, and email the specified emails.

If the script is run with the “user” argument and given a username after this argument, it will attempt to download the recording files for only that user. Please keep in mind that it will still have to download the user cache in its entirety to function correctly; this can take some time so please make sure the username is correct.

The script will record its progress when run normally. If it were to crash, freeze, or otherwise become unable to complete, the script can be rerun with the ‘cont’ argument and it will use the records it made in the ‘complete_users.json’ file to continue from where it left off.

If the flag “-NoEmail” is present in the arguments [anywhere], the script will not send any emails upon completion. This is useful for testing and not recommended for use on a live environment.

Logging
There are 4 log files that are used by the program. 

The standard log file provides a note of all successful operations, and is intended for tracking and confirming operation. 

The warnings log file (“warnings.log”) is intended to display information that could be useful in the event of unintended behaviour, and will note anything that didn’t stop operation of the script, but was unexpected or unusual. 

The errors log file (“errors.log”) is intended to give full stack traces when the program crashes or finds a major malfunction. It will also note anything of concern along with some information about the error if it is a known issue.

The debug log file (“debug.log”) is intended for placing debug information should anyone need to test/check/modify the script. It can be useful for dumping information throughout runtime that may help fix an issue. Keep in mind that the ‘DEBUG’ variable in log.py must be set to ‘TRUE’ for output to appear here.

Settings & Configuration
The behaviour of the script can be configured in various places in the script files.

Local Directory
The local directory can be changed in the main.py file, on line 36. This is logged on every run of the script to the log file.
