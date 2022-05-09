import smtplib, log, ssl

from email.message import EmailMessage


def SendReport(report):
    host = ""

    FROM = ""
    TO = ""
    CC = ""
    SUBJECT = "Subject: Zoom Bulk Download Report"

    msg = EmailMessage()
    msg.set_content(report)

    msg['Subject'] = SUBJECT
    msg['From'] = FROM
    msg['To'] = TO
    msg['Cc'] = CC

    server = smtplib.SMTP(host, 465)
    server.starttls()
    server.login('user', 'pass') #Only for DEV branch, will need valid credentials
    server.send_message(msg)
    server.quit()

    log.LogOK("Report email sent to " + TO + " and " + CC)
    log.PrintOK("Report email sent to " + TO + " and " + CC)
