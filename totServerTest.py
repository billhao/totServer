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
		
def SendDiagnosisEmail(msg_str, recipients, code):
	sender = 'totdevteam@gmail.com'
	#receiver = dest
   	msg = MIMEText(msg_str)
	if code != 0:
		msg['Subject'] = '[URGENT] tot server experiences problems'
	else:
		msg['Subject'] = '[RELAX] tot server is online'
	msg['From'] = sender
	msg['To'] = ", ".join(recipients)	

	## Setup SMTP server
        smtp_server = 'email-smtp.us-east-1.amazonaws.com'
        smtp_user = 'AKIAJBMUQEV5LF7GWJQA'
        smtp_password = 'Am2tNXv7h3w/2ko7FJNEYMynUHv+r9DvM5s5vvB1FGyw'

	## Connect to server
	smtp = smtplib.SMTP()
	smtp.connect(smtp_server)
	smtp.starttls()
	smtp.login(smtp_user, smtp_password)
	smtp.sendmail(sender, recipients, msg.as_string())
	smtp.quit()

	return	

def TestServer():
	# Probe server for its status
	ret_code = SendReqToServer()
	msg_str = ''
	if ret_code == 0:
		msg_str='Server OK\nUsage Summary:\n'
	elif ret_code == 1:
		msg_str='Server down\n\n'
	elif ret_code == 2:
		msg_str='Server OK but Databse down\n\n'
	
	# Process log file for stats
	stats_list = tot_stats.processStats("/home/ec2-user/code-github/totServer/nohup.out")
	for stat in stats_list:
		msg_str = msg_str + stat.to_str()
	
	#print msg_str
	
	# Send email to dev team
	receivers = ['billhao@gmail.com', 'zcjsword@gmail.com', 'lxhuang1984@gmail.com', 'lihangzhao@gmail.com']
	#for dest in receivers:	
	SendDiagnosisEmail(msg_str, receivers, ret_code)

	return


if __name__ == "__main__":
	TestServer()
