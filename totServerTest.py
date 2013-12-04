import requests
import smtplib, sys, optparse, urllib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

##
## Function: send a GET request to totServer
## Return: 0 - server is OK; 1 - server not OK; 2 - db not OK
##
def SendReqToServer():
	response = requests.get('https://gettot.com/test',verify=False)
	#print response.text
	if response.status_code != 200:
		return 1
	if response.text != '1':
		return 2
	return 0
		
def SendDiagnosisEmail(msg_str, dest, code):
	msg_mime = MIMEText(msg_str)
	if code != 0:
		msg_mime['Subject'] = '[URGENT] tot server experiences problems'
	else:
		msg_mime['Subject'] = '[RELAX] tot server runs well'
	msg_mime['From'] = 'totdevteam@gmail.com'
	msg_mime['To'] = dest

	## Setup SMTP server
    	gmail_user = 'totdevteam@gmail.com'
    	gmail_pwd = 'totdev2013'
    	sender_id = 'totdevteam@tot.com'
    	server = smtplib.SMTP('smtp.gmail.com',587)
    	server.ehlo()
    	server.starttls()
    	server.ehlo
    	server.login(gmail_user, gmail_pwd)
    	server.sendmail(sender_id, dest, msg_mime.as_string())  	
	#print 'done!'
    	server.quit()
    	return	

def TestServer():
	ret_code = SendReqToServer()
	msg_str = ''
	if ret_code == 0:
		msg_str='Server OK'
	elif ret_code == 1:
		msg_str='Server down'
	elif ret_code == 2:
		msg_str='Server OK but Databse down'
	
	receivers = ['lihangzhao@gmail.com', 'billhao@gmail.com', 'lxhung1984@gmail.com', 'zcjsword@gmail.com', 'lihangzhao@gmail.com']

	for dest in receivers:
		SendDiagnosisEmail(msg_str, dest, ret_code)

	return


if __name__ == "__main__":
	TestServer()
