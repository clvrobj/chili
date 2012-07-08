#-*- coding:utf-8 -*-
from werkzeug.utils import cached_property
from flask import request, session as flask_session
from dropbox import client, rest, session
from config import DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_ACCESS_TYPE, \
    DROPBOX_REQUEST_TOKEN_KEY, DROPBOX_ACCESS_TOKEN_KEY

class Dropbox(object):

    @property
    def is_authenticated(self):
        return DROPBOX_ACCESS_TOKEN_KEY in flask_session

    @cached_property
    def session(self):
        return session.DropboxSession(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_ACCESS_TYPE)

    @property
    def request_token(self):
        token = self.session.obtain_request_token()
        flask_session[DROPBOX_REQUEST_TOKEN_KEY] = {'key':token.key, 'secret':token.secret}
        return token

    @property
    def login_url(self):
        return self.session.build_authorize_url(self.request_token, oauth_callback='%slogin_success' % request.host_url)

    def login(self, request_token):
        self.session.set_request_token(request_token['key'], request_token['secret'])
        access_token = self.session.obtain_access_token(self.session.request_token)
        flask_session[DROPBOX_ACCESS_TOKEN_KEY] = {'key':access_token.key, 'secret':access_token.secret}

        c = client.DropboxClient(self.session)
        print "linked account:", c.account_info()
    
        # Remove available request token
        del flask_session[DROPBOX_REQUEST_TOKEN_KEY]

    def logout(self):
        if DROPBOX_ACCESS_TOKEN_KEY in flask_session:
            del flask_session[DROPBOX_ACCESS_TOKEN_KEY]

    @property
    def client(self):
        access_token = flask_session[DROPBOX_ACCESS_TOKEN_KEY]
        self.session.set_token(access_token['key'], access_token['secret'])
        return client.DropboxClient(self.session)
