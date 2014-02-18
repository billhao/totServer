##
## simple smtp client using gmail smtp server - totdev - 08/07/2013
##

import smtplib, sys, optparse, urllib

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from string import Template

def send_mail(msg_file, dest, name):
    # Construct the message
    fp = open(msg_file, 'rb')
    msg = MIMEText('Dear parents' + ',\n\n' + fp.read())
    fp.close()
    msg['Subject'] = 'Welcome to tot'
    msg['From'] = 'totdevteam@gmail.com' # me
    msg['To'] = dest  # you
    sender = 'totdevteam@gmail.com'
    receiver = dest
    ## Setup SMTP server
    smtp_server = 'email-smtp.us-east-1.amazonaws.com'  
    smtp_user = 'AKIAJBMUQEV5LF7GWJQA'  
    smtp_password = 'Am2tNXv7h3w/2ko7FJNEYMynUHv+r9DvM5s5vvB1FGyw'
    ## Connect to SMTP server
    smtp = smtplib.SMTP()  
    smtp.connect(smtp_server)  
    smtp.starttls()
    smtp.login(smtp_user, smtp_password)  
    smtp.sendmail(sender, receiver, msg.as_string())  
    smtp.quit() 

    return

def send_forgetpassword_mail(dest, name, token, email):
    ## Construct the message
    email_encode = urllib.quote(email, '')
    msg = MIMEMultipart('alternative')
    msg['Subject'] = 'tot password request'
    msg['From'] = 'totdevteam@gmail.com' # me
    msg['To'] = dest  # you

    # set email content
    text = 'Dear tot user,\n\n' + 'We understand you would like to change your password. Just click the link below and follow the prompts. Please do not forget your password is case sensitive.\n'+ 'Click to reset tot password: https://www.gettot.com/resetpasswordtoken?token=' + token + '&email=' + email_encode + '\n\n'+ 'You are kindly reminded that this token expires in 24 hours\n\n' + 'Sincerely,\n'+ '-Your friends at tot\n'
    html = '''\
	<html>
   	<table background=http://2.bp.blogspot.com/-u7HB4nIOOaE/T4opljlXW1I/AAAAAAAAGCg/wLlOsHjsABs/s1600/Baby+Care++2.jpg>
	<body><p>
	<font size='3'>Hello {name_temp},<br><br>We understand you would like to change your password. Just click the link below and follow the prompts.<br><br>
	https://www.gettot.com/resetpasswordtoken?token={token_temp}&email={email_temp}<br><br>
	Sincerely,<br>
	Your friends at Team tot.<br><br></font>
	<font color="grey">If you haven't requested to reset your tot password, please email us at totdevteam@gmail.com</font>
	</p>
	</body>
	</html>'''.format(name_temp=name, token_temp=token, email_temp=email_encode)
    msg_txt = MIMEText(text, 'plain')
    msg_html = MIMEText(html, 'html')
    msg.attach(msg_txt)
    msg.attach(msg_html)    
	        
    #print msg.as_string()
    
    ## config sender & receiver
    sender = 'totdevteam@gmail.com'
    receiver = dest
    ## Setup SMTP server
    smtp_server = 'email-smtp.us-east-1.amazonaws.com'
    smtp_user = 'AKIAJBMUQEV5LF7GWJQA'
    smtp_password = 'Am2tNXv7h3w/2ko7FJNEYMynUHv+r9DvM5s5vvB1FGyw'
    ## Connect to SMTP server
    smtp = smtplib.SMTP()
    smtp.connect(smtp_server)
    smtp.starttls()
    smtp.login(smtp_user, smtp_password)
    smtp.sendmail(sender, receiver, msg.as_string())
    smtp.quit()

    return

def main(argv):
    parser = optparse.OptionParser()
    parser.add_option('-d', action="store", dest="dest", help="dest_email_addr", default="lihangzhao@gmail.com")
    parser.add_option('-m', action="store", dest="msg_file", help="msg_file", default="welcome.txt")
    parser.add_option('-u', action="store", dest="uname", help="user_name", default="Lihang")

    options, args = parser.parse_args()
    dest = options.dest
    msg_file = options.msg_file
    username = options.uname
    print dest
    print msg_file
    print username

    send_mail(msg_file, dest, username)

if __name__ == "__main__":
    main(sys.argv[1:])
