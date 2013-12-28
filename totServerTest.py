import requests
import smtplib, sys, optparse, urllib
import tot_stats

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
	## Setup SMTP server
	username = 'totdevteam'
	password = 'totusc'
	sender = 'totdevteam@163.com'
	server = smtplib.SMTP()
	server.connect('smtp.163.com')
	server.login(username, password)
	
	## Setup mail content
	msg_mime = MIMEText(msg_str)
	if code != 0:
		msg_mime['Subject'] = '[URGENT] tot server experiences problems'
	else:
		msg_mime['Subject'] = '[RELAX] tot server is online'
	msg_mime['From'] = sender
	msg_mime['To'] = dest
	
	## Send the mail
	server.sendmail(sender, dest, msg_mime.as_string())
	
	#print 'done!'
	server.quit()
	return	

def TestServer():
	ret_code = SendReqToServer()
	msg_str = ''
	if ret_code == 0:
		msg_str='Server OK\n\n'
	elif ret_code == 1:
		msg_str='Server down\n\n'
	elif ret_code == 2:
		msg_str='Server OK but Databse down\n\n'
	
	stats_list = tot_stats.processStats("/home/ec2-user/code-github/totServer/nohup.out")
	msg_str = msg_str + "++++++++++++++++++++++++++++++++\ntot server stats:\n++++++++++++++++++++++++++++++++\n"
	for stat in stats_list:
		msg_str = msg_str + stat.to_str()
	
	#print msg_str
	#return
	receivers = ['lihangzhao@gmail.com', 'billhao@gmail.com', 'lxhuang1984@gmail.com', 'zcjsword@gmail.com']
	for dest in receivers:
		SendDiagnosisEmail(msg_str, dest, ret_code)

	return


if __name__ == "__main__":
	TestServer()
