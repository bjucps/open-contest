#!/usr/bin/python

import smtplib
from email.message import EmailMessage
from email.headerregistry import Address
from email import encoders
from email.utils import make_msgid
import os
import os.path
import sys
import getpass
import csv



gmail_user = sys.argv[1]
gmail_pwd = getpass.getpass("Enter gmail password for " + gmail_user + ":")
subject = "Programming Contest Login Credentials"
msg = """
Here are your login credentials for the programming contest:

Username: {USERNAME}
Password: {PASSWORD}

Access the system: https://contest.bjucps.dev/
"""


def mail(to, subject, text, attach=None):
   msg = EmailMessage()

   msg['From'] = gmail_user
   msg['To'] = to
   msg['Subject'] = subject

   msg.set_content(text)

   mailServer = smtplib.SMTP("smtp.gmail.com", 587)
   mailServer.ehlo()
   mailServer.starttls()
   mailServer.ehlo()
   mailServer.login(gmail_user, gmail_pwd)
   mailServer.sendmail(gmail_user, to, msg.as_string())
   # Should be mailServer.quit(), but that crashes...
   mailServer.close()


count = 0
f = open('users.csv')
reader = csv.reader(f, delimiter=',', quotechar='"')
for entry in reader:
    username = entry[0]
    full_name = entry[1]
    password = entry[2]
    emailTo = entry[3]
    if not emailTo:
        continue
    print('Emailing: ', emailTo)
    theMsg = msg.format(USERNAME=username, PASSWORD=password)
    mail(emailTo, subject, theMsg, None)
    count += 1


                    
print( "\nSent " + str(count) + " items." )
