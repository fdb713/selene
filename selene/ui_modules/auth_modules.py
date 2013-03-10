# -*- coding: utf-8 *-*
import tornado.web


class LoginModule(tornado.web.UIModule):

    def render(self, _next):
        return self.render_string('modules/login.html', _next=_next)


class GoogleLoginModule(tornado.web.UIModule):

    def render(self):
        return self.render_string('modules/googlelogin.html')


class TwitterLoginModule(tornado.web.UIModule):

    def render(self):
        return self.render_string('modules/twitterlogin.html')


class FacebookLoginModule(tornado.web.UIModule):

    def render(self):
        return self.render_string('modules/facebooklogin.html')


class RegisterModule(tornado.web.UIModule):

    def render(self):
        return self.render_string('modules/register.html')


class ResetPasswordModule(tornado.web.UIModule):

    def render(self, reset_hash):
        return self.render_string('modules/resetpassword.html',
            reset_hash=reset_hash)


class NewPasswordModule(tornado.web.UIModule):

    def render(self):
        return self.render_string('modules/newpassword.html')
