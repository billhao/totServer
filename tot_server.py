#!/usr/bin/env python
#
# Copyright 2013 TOT-USC
#
#

import markdown
import os.path
import re
import torndb
import tornado.auth
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import unicodedata
import logging
import datetime
import uuid
import base64
import functools

from passlib.hash import pbkdf2_sha256

#### user-defined packages
import smtp_client
import tot_util

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="database host")
#####
#define("mysql_database", default="tot_user", help="tot database name")
#define("mysql_user", default="totdev", help="database username")
#define("mysql_password", default="totdev", help="database password")
##### EC2 db login
define("mysql_database", default="tot_db", help="tot database name")
define("mysql_user", default="root", help="database username")
define("mysql_password", default="", help="database password")


response_code = {'login_success': 0, 'login_unmatch': 1, 'login_no_usr': 2,
                 'reg_success': 0, 'reg_usr_exist': 11,
                 'reset_success': 0, 'reset_old_pc_wrong': 21, 'reset_no_usr': 22,
                 'retrieve_link_snd': 0, 'retrieve_fail': 31}

# HTTP Basic Authentication decorator
def httpBA(method):
    @functools.wraps(method)
    def wrapper(self, *args, **kwargs):
        #error_authentication = self.application.settings.get('error_auth')
        auth_header = self.request.headers.get('Authorization', None)
        
        if auth_header is None:
            logging.getLogger("tornado.general").info("httpBA: not pass")
            return self.write("HTTP BA not pass")
        
        s, base64string = authorization_header.split()
        username, password = base64.decodestring(base64string).split(':')
        
        if password != 0000:
            logging.getLogger("tornado.general").info("httpBA: not pass")
            return self.write("HTTP BA not pass")

        return method(self, *args, **kwargs)
    return wrapper


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),
            (r"/register", RegisterHandler),
            (r"/deleteacct", DeleteAcctHandler),
            (r"/forgetpassword", ForgetPasswordHandler),
            (r"/resetpasswordtoken", ResetPasswordWithTokenHandler),
            (r"/m/login", AppAuthLoginHandler),
            (r"/m/reg", AppRegisterHandler),
            (r"/m/reset", AppResetPasswordHandler),
            (r"/m/forget", AppForgetPasswordHandler)
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            #ui_modules={"Entry": EntryModule},
            xsrf_cookies=False,
            cookie_secret="19850116",
            login_url="/auth/login",
            debug=True,
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        # Have one global connection to the blog DB across all handlers
        self.db = torndb.Connection(
            host=options.mysql_host, database=options.mysql_database,
            user=options.mysql_user, password=options.mysql_password)

################################
##   BaseHandler
################################
class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        logging.getLogger("tornado.general").info("BaseHandler::get_current_user...")
        user_id = self.get_secure_cookie("email")
        if not user_id: return None
        return self.get_secure_cookie("email")
        #return self.db.get("SELECT * FROM authors WHERE id = %s", int(user_id))

################################
##   HomeHandler
################################
class HomeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        user_id = self.get_secure_cookie("user")
        self.render("tothome.html", uname=str(user_id))
        return

################################
##   AuthLoginHandler
################################
class AuthLoginHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        logging.getLogger("tornado.general").info("AuthLoginHandler::get...")
        self.render("login.html", login_msg="")

    def post(self):
        logging.getLogger("tornado.general").info("AuthLoginHandler::post...")
        email = self.get_argument("email")
        passcode = self.get_argument("passcode")
        logging.getLogger("tornado.general").info("Email:" + email)
        logging.getLogger("tornado.general").info("Passcode:" + passcode)
	# find a match in the db
        user_db = self.db.get("SELECT * FROM users WHERE email = %s", str(email))
        if not user_db:
            self.render("login.html", login_msg="User not found!")
            return
        
        #if user_db.passcode != passcode:
        if not pbkdf2_sha256.verify(str(passcode), user_db.passcode):
            #login_response = {
            #    'error': True,
            #    'msg': 'Thank You.'
            #}
            #self.write(login_response)
            self.render("login.html", login_msg="Email and password not match. Please try again.")
            return

        self.set_secure_cookie("user", user_db.uname)
        self.set_secure_cookie("passcode", user_db.passcode)
        self.set_secure_cookie("email", user_db.email)
        self.redirect("/")

################################
##   RegisterHandler
################################
class RegisterHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        logging.getLogger("tornado.general").info("RegisterHandler::get...")
        self.render("register.html")

    def post(self):
        logging.getLogger("tornado.general").info("RegisterHandler::post...")
        username = self.get_argument("name")
        email = self.get_argument("email")
        passcode0 = self.get_argument("passcode0")
        passcode1 = self.get_argument("passcode1")
        if passcode0 != passcode1 :
            self.render("register.html", reg_msg="Two passcodes must match! Please re-fill the info.")
            return
        # check if the username has been used
        email_db = self.db.get("SELECT * FROM users WHERE email = %s", str(email))
        if email_db:
            self.render("register.html", reg_msg="Email address already used! You may want to log in.")
            return
        # hash the passcode
        hash_pw = pbkdf2_sha256.encrypt(str(passcode0), rounds=1000, salt_size=6)
        # create a new user if email addr not found in db
        self.db.execute(
            "INSERT INTO users (email, uname, passcode) VALUES (%s, %s, %s)",
            str(email), str(username), str(hash_pw))
        self.set_secure_cookie("user", username)
        self.set_secure_cookie("passcode", passcode0)
        self.set_secure_cookie("email", email)
        # send confirmation email
        smtp_client.send_mail('./templates/welcome.txt', email, username)
        # redirect to home page
        self.redirect("/")

################################
##    AuthLogoutHandler
################################
class AuthLogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.clear_cookie("passcode")
        self.clear_cookie("email")
        self.redirect("/")

################################
##    DeleteAcctHandler
################################
class DeleteAcctHandler(BaseHandler):
    @httpBA
    def get(self):
        user_email = self.get_secure_cookie("email")
        if not user_email:
            self.clear_cookie("user")
            self.clear_cookie("passcode")
            self.clear_cookie("email")
            self.redirect("/")
            return
        # delete the db entries of this user
        the_user = self.db.get("SELECT * FROM users WHERE email = %s", str(user_email))
        if the_user:
            the_entries = self.db.get("SELECT * FROM entries WHERE uid = %s", int(the_user.uid))
            if the_entries:
                delete_entries = self.db.execute("DELETE FROM entries WHERE uid = %s", int(the_user.uid))
            delete_user = self.db.execute("DELETE FROM users WHERE email = %s", str(user_email))
        # redirect to home
        self.clear_cookie("user")
        self.clear_cookie("passcode")
        self.clear_cookie("email")
        self.redirect("/")

################################
##    AppAuthLoginHandler
##    - app login
################################
class AppAuthLoginHandler(BaseHandler):
    @tornado.web.asynchronous
    def post(self):
        logging.getLogger("tornado.general").info("MobileAuthLoginHandler::post...")
        email = self.get_argument("email")
        passcode = self.get_argument("passcode")
        logging.getLogger("tornado.general").info("Email:" + email)
        logging.getLogger("tornado.general").info("Passcode:" + passcode)
        # find a match in the db
        user_db = self.db.get("SELECT * FROM users WHERE email = %s", str(email))
        if not user_db:
            self.write(str(response_code['login_no_usr']))
            self.finish()
            return
        #if user_db.passcode != passcode:
        if not pbkdf2_sha256.verify(str(passcode), user_db.passcode):    
            self.write(str(response_code['login_unmatch']))
            self.finish()
            return

        self.write(str(response_code['login_success']))
        self.finish()

################################
##   AppRegisterHandler
##   - register new user from within the app
################################
class AppRegisterHandler(BaseHandler):
    @tornado.web.asynchronous
    def post(self):
        logging.getLogger("tornado.general").info("RegisterHandler::post...")
        username = self.get_argument("name")
        email = self.get_argument("email")
        passcode = self.get_argument("passcode")
        usr_db = self.db.get("SELECT * FROM users WHERE email = %s", str(email))
        # email exists in db
        if usr_db:
            self.write(str(response_code['reg_usr_exist']))
            self.finish()
            return
        # hash the passcode
        hash_pw = pbkdf2_sha256.encrypt(str(passcode), rounds=1000, salt_size=6)
        # create a new user
        self.db.execute(
            "INSERT INTO users (email, uname, passcode) VALUES (%s, %s, %s)",
            str(email), str(username), str(hash_pw))
        # send confirmation email
        smtp_client.send_mail('./templates/welcome.txt', email, username)
        # send response to app
        self.write(str(response_code['reg_success']))
        self.finish()

################################
##   AppResetPasswordHandler
##   - reset password from within the app
################################
class AppResetPasswordHandler(BaseHandler):
    @tornado.web.asynchronous
    def post(self):
        logging.getLogger("tornado.general").info("MobileResetPasswordHandler::post...")
        email = self.get_argument("email")
        old_passcode = self.get_argument("old_passcode")
        new_passcode = self.get_argument("new_passcode")
        # authenticate old passcode
        usr_db = self.db.get("SELECT * FROM users WHERE email = %s", str(email))
        if not usr_db :
            self.write(str(response_code['reset_no_usr']))
            self.finish()
            return
        #if old_passcode != usr_db.passcode :
        if not pbkdf2_sha256.verify(str(old_passcode), user_db.passcode): 
            self.write(str(response_code['reset_old_pc_wrong']))
            self.finish()
            return
        # hash the passcode
        hash_pw = pbkdf2_sha256.encrypt(str(new_passcode), rounds=1000, salt_size=6)
        # set new passcode for user
        self.db.execute(
            "UPDATE users set passcode=%s WHERE email=%s", str(hash_pw), str(email))

        # send notification email
        # smtp_client.send_mail('welcome.txt', email, username)

        # send response to app
        self.write(str(response_code['reset_success']))
        self.finish()

################################
##   AppForgetPasswordHandler
##   - request reset password token from within the app b/c usr forgets password
################################
class AppForgetPasswordHandler(BaseHandler):
    @tornado.web.asynchronous
    def post(self):
        logging.getLogger("tornado.general").info("AppForgetPasswordHandler::post...")
        email = self.get_argument("email")
        # check whether the email is registered
        usr_db = self.db.get("SELECT * FROM users WHERE email = %s", str(email))
        if not usr_db :
            self.write(str(response_code['retrieve_fail']))
	    self.finish()
            return
        # create expiration date and uuid for the user
        expire_date = datetime.datetime.now() + datetime.timedelta(days=1) # 24-hour expiration period
        str_expire_date = expire_date.strftime('%Y-%m-%d %H:%M:%S')
        token = tot_util.rnd_str_generator()
        # update database with the expiration date and uuid
        forgetPasswordUser_db = self.db.get("SELECT * FROM ForgetPasswordUsers WHERE email = %s", str(email))
        if not forgetPasswordUser_db:
            self.db.execute(
                "INSERT INTO ForgetPasswordUsers (email, PasswordResetToken, PasswordResetExpiration) VALUES (%s, %s, %s)",
                str(email), token, str_expire_date )
        else:
            self.db.execute(
                "UPDATE ForgetPasswordUsers SET PasswordResetToken=%s, PasswordResetExpiration=%s WHERE email=%s", token, str_expire_date, str(email))
        # send an email with a reset password link
        smtp_client.send_forgetpassword_mail(email, usr_db.uname, token, email)
	
	# send response to app
        self.write(str(response_code['retrieve_link_snd']))
        self.finish()


################################
##   ForgetPasswordHandler
##   - request reset password from web b/c usr forgets password
##   - create a db entry recording the expiration and token
##   - send token to usr email
################################
class ForgetPasswordHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
         logging.getLogger("tornado.general").info("ForgetPasswordHandler::get...")
         self.render("forgetpassword.html", login_msg="")

    def post(self):
        logging.getLogger("tornado.general").info("ForgetPasswordHandler::post...")
        email = self.get_argument("email")
        # check whether the email is registered
        usr_db = self.db.get("SELECT * FROM users WHERE email = %s", str(email))
        if not usr_db :
            self.render("forgetpassword.html", msg="Email not found.")
            return
        # create expiration date and uuid for the user
        expire_date = datetime.datetime.now() + datetime.timedelta(days=1) # 24-hour expiration period
        str_expire_date = expire_date.strftime('%Y-%m-%d %H:%M:%S')
        token = tot_util.rnd_str_generator()
        # update database with the expiration date and uuid
        forgetPasswordUser_db = self.db.get("SELECT * FROM ForgetPasswordUsers WHERE email = %s", str(email))
        if not forgetPasswordUser_db:
            self.db.execute(
                "INSERT INTO ForgetPasswordUsers (email, PasswordResetToken, PasswordResetExpiration) VALUES (%s, %s, %s)",
                str(email), token, str_expire_date )
        else:
            self.db.execute(
                "UPDATE ForgetPasswordUsers SET PasswordResetToken=%s, PasswordResetExpiration=%s WHERE email=%s", token, str_expire_date, str(email))
        # send an email with a reset password link
        smtp_client.send_forgetpassword_mail(email, usr_db.uname, token, email)

        # print msg
        self.redirect("/")

################################
##  ResetPasswordWithTokenHandler
##  - check token and expiration date
##  - sanity check of the new password
##  - reset passcode
##  - send confirm email?
################################
class ResetPasswordWithTokenHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        logging.getLogger("tornado.general").info("ResetPasswordWithTokenHandler::get...")
        token_in = self.get_argument("token")
	email_in = self.get_argument("email")
	msg_in = ''
	forgetPasswordUser_db = self.db.get("SELECT * FROM ForgetPasswordUsers WHERE email = %s", str(email_in) )
        if not forgetPasswordUser_db:
	    msg_in = "Email not found"
	    self.render("resetpasswordwithtoken.html", msg=msg_in, token=token_in, email=email_in)
	    return
	now_date = datetime.datetime.now()
        expire_date = forgetPasswordUser_db.PasswordResetExpiration
	if ( now_date - expire_date > datetime.timedelta(days = 1) ):
	    msg_in = "Token expired!"
	self.render("resetpasswordwithtoken.html", msg=msg_in, token=token_in, email=email_in)
     
    def post(self):
        logging.getLogger("tornado.general").info("ResetPasswordWithTokenHandler::post...")
        # check token and expiration
        email = self.get_argument("email")
        token = self.get_argument("token_in")
        forgetPasswordUser_db = self.db.get("SELECT * FROM ForgetPasswordUsers WHERE email = %s", str(email) )
        if not forgetPasswordUser_db:
            self.render("resetpasswordwithtoken.html", msg="Did you request to reset the password?")
            return
        if not token == forgetPasswordUser_db.PasswordResetToken:
            self.render("resetpasswordwithtoken.html", msg="Invalid token")
            return
        now_date = datetime.datetime.now()
        expire_date = forgetPasswordUser_db.PasswordResetExpiration
        if ( now_date - expire_date > datetime.timedelta(days = 1) ):
            self.render("resetpasswordwithtoken.html", msg="Token expires.")
            return
        logging.getLogger("tornado.general").info("ResetPasswordWithTokenHandler::post...02")
        # reset the password
        new_password = self.get_argument("password")
        new_password_again = self.get_argument("password_again")
        if new_password != new_password_again:
            self.render("resetpasswordwithtoken.html", msg="Two passwords do not match.")
            return
        # hash the passcode
        hash_pw = pbkdf2_sha256.encrypt(str(new_password), rounds=1000, salt_size=6)
        # update db
        self.db.execute(
            "UPDATE users set passcode=%s WHERE email=%s", str(hash_pw), str(email) )
        self.db.execute(
            "DELETE from ForgetPasswordUsers WHERE email = %s", str(email) )
        self.redirect("/")
        return


################################
##    main
################################
def main():
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    main()
