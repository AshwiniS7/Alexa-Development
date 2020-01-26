#email.py
import traceback
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# AWS Config
EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'
EMAIL_HOST_USER = "" # Replace with your SMTP username
EMAIL_HOST_PASSWORD = "" # Replace with your SMTP password
EMAIL_PORT = 587

def send_it(html = 'holder', patientname="Patient", fromx='florence.nightingale.care@gmail.com', tox='kneecare.team@gmail.com'):
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Today's Info About %s" %(patientname)
    msg['From'] = fromx
    msg['To'] = tox

    #html = "yeah whatever "#open('index.html').read()

    mime_text = MIMEText(html, 'html')
    msg.attach(mime_text)

    s = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    s.starttls()
    s.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    s.sendmail(fromx,tox, msg.as_string())
    s.quit()

