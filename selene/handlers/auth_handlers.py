# -*- coding: utf-8 *-*
import bcrypt
import datetime
import tornado.auth
import tornado.web

from selene import helpers
from selene.handlers import BaseHandler
from tornado.options import options


class AuthBaseHandler(BaseHandler):

    def prepare(self):
        if self.current_user:
            self.redirect("/")


class RegisterHandler(AuthBaseHandler):

    def get(self):
        self.render("register.html", message='')

    def post(self):
        name = self.get_argument("name", "")
        email = self.get_argument("email", "")
        password = self.get_argument("password", "")
        if self.db.users.find_one({'email': email}):
            self.render('register.html', message='E-mail address already '
                'registered')
            return
        user = {
            "name": name,
            "email": email,
            "password": bcrypt.hashpw(password, bcrypt.gensalt()),
            'enabled': False,
            'join': datetime.datetime.now(),
            'join_hash': helpers.generate_md5(),
            "locale": options.default_language
            }
        self.db.users.insert(user)
        self.smtp.send('Confirm your account', 'newuser.html', user['email'],
            {'user': user})
        self.redirect("/login")


class ConfirmAccountHandler(AuthBaseHandler):

    def get(self, join_hash=None):
        self.db.users.find_and_modify({'join_hash': join_hash},
            {'$unset': {'join_hash': 1}, '$set': {'enabled': True}})
        self.render('confirmaccount.html')


class LoginHandler(AuthBaseHandler):

    def get(self):
        self.render("login.html", message='')

    def post(self):
        email = self.get_argument("email", False)
        password = self.get_argument("password", False)
        next_ = self.get_argument('next_', '/')
        if email and password:
            user = self.db.users.find_one({"email": email})
            if user:
                if user['enabled']:
                    pass_check = bcrypt.hashpw(password,
                        user["password"]) == user["password"]
                    if pass_check:
                        self.set_secure_cookie("current_user", user["email"])
                        self.redirect(next_)
                        return
        self.render('login.html',
            message="Incorrect user/password combination or invalid account")


class LoginGoogleHandler(AuthBaseHandler, tornado.auth.GoogleMixin):

    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("openid.mode", None):
            self.next_ = self.get_argument('next', '/')
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authenticate_redirect(ax_attrs=['name', 'email', 'language'])

    def _on_auth(self, data):
        if not data:
            raise tornado.web.HTTPError(500)
        user = {
            'name': data['name'],
            'email': data['email'],
            'enabled': True,
            'join': datetime.datetime.now(),
            'locale': data['locale'],
            'accounts': ['google'],
            'google_claimed_id': data['claimed_id']
        }
        self.db.users.update({'email': data['email']}, {'$set': user},
            upsert=True)
        self.set_secure_cookie("current_user", user["email"])
        self.redirect(self.next_)


class LoginTwitterHandler(AuthBaseHandler, tornado.auth.TwitterMixin):

    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("oauth_token", None):
            self.next_ = self.get_argument('next', '/')
            self.get_authenticated_user(self.async_callback(self._on_auth))
            return
        self.authorize_redirect()

    def _on_auth(self, data):
        if not data:
            raise tornado.web.HTTPError(500)
        user = {
            'username': data['username'],
            'name': data['name'],
            'enabled': True,
            'join': datetime.datetime.now(),
            'locale': data['lang'],
            'accounts': ['twitter'],
            'twitter_access_token': data['access_token']
        }
        self.db.users.insert(user)
        self.set_secure_cookie("current_user", user["username"])
        self.redirect(self.next_)


class LoginFacebookHandler(AuthBaseHandler, tornado.auth.FacebookGraphMixin):

    @tornado.web.asynchronous
    def get(self):
        if self.get_argument("code", False):
            self.next_ = self.get_argument('next', '/')
            self.get_authenticated_user(
                redirect_uri=options.base_url + '/login/facebook/',
                client_id=self.settings["facebook_app_id"],
                client_secret=self.settings["facebook_app_secret"],
                code=self.get_argument("code"),
                params={"scope": "email"},
                callback=self.async_callback(self._on_login))
            return
        self.authorize_redirect(
            redirect_uri=options.base_url + '/login/facebook/',
            client_id=self.settings["facebook_app_id"],
            extra_params={"scope": "email"})

    def _on_login(self, data):
        if not data:
            raise tornado.web.HTTPError(500)
        self.write(data)
        self.finish()
        return
        user = {
            'name': data['name'],
            'email': data['email'],
            'enabled': True,
            'join': datetime.datetime.now(),
            'locale': data['locale'],
            'accounts': ['google'],
            'google_claimed_id': data['claimed_id']
        }
        self.db.users.update({'email': data['email']}, {'$set': user},
            upsert=True)
        self.set_secure_cookie("current_user", user["email"])
        self.redirect(self.next_)


class RequestNewPasswordHandler(AuthBaseHandler):

    def get(self):
        self.render('newpassword.html', message='')

    def post(self):
        email = self.get_argument('email', False)
        if not email:
            self.render('newpassword.html',
                message="E-mail address is required.")
            return
        user = self.db.users.find_one({'email': email})
        if user:
            reset_hash = helpers.generate_md5()
            user = self.db.users.find_and_modify({'email': email},
                {'$set': {'reset_hash': reset_hash, 'enabled': True},
                '$unset': {'join_hash': 1}}, new=True)
            self.smtp.send('Reset password', 'newpassword.html',
                user["email"], {'user': user})
            self.redirect('/')
            return
        self.render('newpassword.html', message='User does not exist')


class ResetPasswordHandler(AuthBaseHandler):

    def get(self, reset_hash=''):
        self.render('resetpassword.html', message='', reset_hash=reset_hash)

    def post(self, reset_hash=None):
        reset_hash = self.get_argument('hash', False)
        password = self.get_argument('password', False)
        if reset_hash and password:
            password = bcrypt.hashpw(password, bcrypt.gensalt())
            user = self.db.users.find_and_modify({'reset_hash': reset_hash},
                {'$set': {'password': password}}, new=True)
            if user:
                self.smtp.send('Updated password', 'resetpassword.html',
                    user['email'], {'user': user})
                self.redirect('/login')
                return
        self.render('resetpassword.html', message='Invalid arguments',
            reset_hash='')


class LogoutHandler(BaseHandler):

    def post(self):
        if not self.current_user:
            self.redirect('/')
            return
        self.clear_cookie("current_user")
        self.redirect("/")
