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

import smtp_client

from tornado.options import define, options

define("port", default=8888, help="run on the given port", type=int)
define("mysql_host", default="127.0.0.1:3306", help="blog database host")
define("mysql_database", default="tot_user", help="tot database name")
define("mysql_user", default="totdev", help="database username")
define("mysql_password", default="totdev", help="database password")

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/", HomeHandler),
            (r"/auth/login", AuthLoginHandler),
            (r"/auth/logout", AuthLogoutHandler),
            (r"/register", RegisterHandler),
            (r"/deleteacct", DeleteAcctHandler),
            (r"/m/auth/login", MobileAuthLoginHandler),
            (r"/m/register", MobileRegisterHandler)
            #(r"/archive", ArchiveHandler),
            #(r"/feed", FeedHandler),
            #(r"/entry/([^/]+)", EntryHandler),
            #(r"/compose", ComposeHandler),
        ]
        settings = dict(
            blog_title=u"Tornado Blog",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            ui_modules={"Entry": EntryModule},
            xsrf_cookies=True,
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
        user_id = self.get_secure_cookie("user")
        if not user_id: return None
        return self.get_secure_cookie("user")
        #return self.db.get("SELECT * FROM authors WHERE id = %s", int(user_id))

################################
##   HomeHandler
################################
class HomeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        #self.write("hello world")
        user_id = self.get_secure_cookie("user")
        self.render("tothome.html", uname=str(user_id))
        return
        entries = self.db.query("SELECT * FROM entries ORDER BY published "
                                "DESC LIMIT 5")
        if not entries:
            self.redirect("/compose")
            return
        self.render("home.html", entries=entries)

################################
##   EntryHandler (not called)
################################
class EntryHandler(BaseHandler):
    def get(self, slug):
        entry = self.db.get("SELECT * FROM entries WHERE slug = %s", slug)
        if not entry: raise tornado.web.HTTPError(404)
        self.render("entry.html", entry=entry)

################################
##   ArchiveHandler (not called)
################################
class ArchiveHandler(BaseHandler):
    def get(self):
        entries = self.db.query("SELECT * FROM entries ORDER BY published "
                                "DESC")
        self.render("archive.html", entries=entries)

################################
##   FeedHandler (not called)
################################
class FeedHandler(BaseHandler):
    def get(self):
        entries = self.db.query("SELECT * FROM entries ORDER BY published "
                                "DESC LIMIT 10")
        self.set_header("Content-Type", "application/atom+xml")
        self.render("feed.xml", entries=entries)

################################
##   ComposeHandler (not called)
################################
class ComposeHandler(BaseHandler):
    @tornado.web.authenticated
    def get(self):
        id = self.get_argument("id", None)
        entry = None
        if id:
            entry = self.db.get("SELECT * FROM entries WHERE id = %s", int(id))
        self.render("compose.html", entry=entry)

    @tornado.web.authenticated
    def post(self):
        id = self.get_argument("id", None)
        title = self.get_argument("title")
        text = self.get_argument("markdown")
        html = markdown.markdown(text)
        if id:
            entry = self.db.get("SELECT * FROM entries WHERE id = %s", int(id))
            if not entry: raise tornado.web.HTTPError(404)
            slug = entry.slug
            self.db.execute(
                "UPDATE entries SET title = %s, markdown = %s, html = %s "
                "WHERE id = %s", title, text, html, int(id))
        else:
            slug = unicodedata.normalize("NFKD", title).encode(
                "ascii", "ignore")
            slug = re.sub(r"[^\w]+", " ", slug)
            slug = "-".join(slug.lower().strip().split())
            if not slug: slug = "entry"
            while True:
                e = self.db.get("SELECT * FROM entries WHERE slug = %s", slug)
                if not e: break
                slug += "-2"
            self.db.execute(
                "INSERT INTO entries (author_id,title,slug,markdown,html,"
                "published) VALUES (%s,%s,%s,%s,%s,UTC_TIMESTAMP())",
                self.current_user.id, title, slug, text, html)
        self.redirect("/entry/" + slug)

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
        # find a match in the db
        user_db = self.db.get("SELECT * FROM users WHERE email = %s", str(email))
        if not user_db:
            self.render("login.html", login_msg="User not found!")
            return
        if user_db.passcode != passcode:
            login_response = {
                'error': True, 
                'msg': 'Thank You.'
            }
            self.write(login_response)
            ### self.render("login.html", login_msg="Email and password not match. Please try again.")
            return

        self.set_secure_cookie("user", user_db.uname)
        self.set_secure_cookie("passcode", user_db.passcode)
        self.set_secure_cookie("email", user_db.email)
        self.redirect("/")

'''
    #### this method is not used ####
    def _on_auth(self, user):
        if not user:
            raise tornado.web.HTTPError(500, "Google auth failed")
        author = self.db.get("SELECT * FROM authors WHERE email = %s",
                             user["email"])
        if not author:
            # Auto-create first author
            any_author = self.db.get("SELECT * FROM authors LIMIT 1")
            if not any_author:
                author_id = self.db.execute(
                    "INSERT INTO authors (email,name) VALUES (%s,%s)",
                    user["email"], user["name"])
            else:
                self.redirect("/")
                return
        else:
            author_id = author["id"]
        self.set_secure_cookie("blogdemo_user", str(author_id))
        self.redirect(self.get_argument("next", "/"))
'''

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
        # create a new user if email addr not found in db
        self.db.execute(
            "INSERT INTO users (email, uname, passcode) VALUES (%s, %s, %s)",
            str(email), str(username), str(passcode0))
        self.set_secure_cookie("user", username)
        self.set_secure_cookie("passcode", passcode0)
        self.set_secure_cookie("email", email)
        # send confirmation email
        smtp_client.send_mail('welcome.txt', email, username)
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
##    MobileAuthLoginHandler
################################
class MobileAuthLoginHandler(BaseHandler):
    @tornado.web.asynchronous
    def post(self):
        logging.getLogger("tornado.general").info("AuthLoginHandler::post...")
        email = self.get_argument("email")
        passcode = self.get_argument("passcode")
        # find a match in the db
        user_db = self.db.get("SELECT * FROM users WHERE email = %s", str(email))
        if not user_db:
            self.render("login.html", login_msg="User not found!")
            return
        if user_db.passcode != passcode:
            self.render("login.html", login_msg="Email and password not match. Please try again.")
            return

        self.set_secure_cookie("user", user_db.uname)
        self.set_secure_cookie("passcode", user_db.passcode)
        self.set_secure_cookie("email", user_db.email)
        self.redirect("/")

################################
##   MobileRegisterHandler
################################
class MobileRegisterHandler(BaseHandler):
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
        # create a new user if email addr not found in db
        self.db.execute(
            "INSERT INTO users (email, uname, passcode) VALUES (%s, %s, %s)",
            str(email), str(username), str(passcode0))
        self.set_secure_cookie("user", username)
        self.set_secure_cookie("passcode", passcode0)
        self.set_secure_cookie("email", email)
        # send confirmation email
        smtp_client.send_mail('welcome.txt', email, username)
        # redirect to home page
        self.redirect("/")
            
################################
##    EntryModule
################################
class EntryModule(tornado.web.UIModule):
    def render(self, entry):
        return self.render_string("modules/entry.html", entry=entry)

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
