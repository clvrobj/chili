#-*- coding:utf-8 -*-
import os
from os.path import isfile, join
import urllib
from markdown import markdown
from flask import Flask, request, redirect, url_for, send_from_directory
from flask import session as flask_session
from flaskext.mako import init_mako, render_template
from dropbox import client, rest, session

DROPBOX_APP_KEY = ''
DROPBOX_APP_SECRET = ''
DROPBOX_ACCESS_TYPE = ''
APP_SECRET_KEY = '' # for use flask session

try:
    from local_config import *
except ImportError:
    pass


DROPBOX_REQUEST_TOKEN_KEY = 'dropbox_request_token'
DROPBOX_REQUEST_TOKEN_SECRET_KEY = 'dropbox_request_token_secret'
DROPBOX_ACCESS_TOKEN_KEY = 'dropbox_access_token'
RAWS_DIR = 'raw_entries'
ENTRIES_DIR = 'public/entries'
MAKO_DIR = 'templates'
ENTRY_LINK_PATTERN = '/entry/%s'

app = Flask(__name__)

# class Dropbox(object):

def is_authenticated():
    return DROPBOX_ACCESS_TOKEN_KEY in flask_session

def dropbox_session():
    return session.DropboxSession(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_ACCESS_TYPE)

def request_token():
    sess = dropbox_session()
    token = sess.obtain_request_token()
    flask_session[DROPBOX_REQUEST_TOKEN_KEY] = {'key':token.key, 'secret':token.secret}
    return token

def login_url():
    sess = dropbox_session()
    return sess.build_authorize_url(request_token(), oauth_callback='%slogin_success' % request.host_url)

def dropbox_login(request_token):
    sess = dropbox_session()
    sess.set_request_token(request_token['key'], request_token['secret'])
    access_token = sess.obtain_access_token(sess.request_token)
    flask_session[DROPBOX_ACCESS_TOKEN_KEY] = {'key':access_token.key, 'secret':access_token.secret}

    c = client.DropboxClient(sess)
    print "linked account:", c.account_info()
    
    # Remove available request token
    del flask_session[DROPBOX_REQUEST_TOKEN_KEY]

def dropbox_logout():
    if DROPBOX_ACCESS_TOKEN_KEY in flask_session:
        del flask_session[DROPBOX_ACCESS_TOKEN_KEY]


def auth_dropbox():
    # Include the Dropbox SDK libraries

    sess = session.DropboxSession(DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_ACCESS_TYPE)
    request_token = sess.obtain_request_token()
    url = sess.build_authorize_url(request_token, oauth_callback='/')
    # Make the user sign in and authorize this token
    print "url:", url
    print "Please visit this website and press the 'Allow' button, then hit 'Enter' here."
    raw_input()

    # This will fail if the user didn't visit the above URL and hit 'Allow'
    access_token = sess.obtain_access_token(request_token)
    
    client = client.DropboxClient(sess)
    print "linked account:", client.account_info()
    return client

def sync_folder(client):
    """
    download all files in the app folder into raws folder
    """
    folder_meta = client.metadata('/')
    for f in folder_meta['contents']:
        p = f['path']
        print 'Downloading %s' % p
        f, meta = client.get_file_and_metadata(p)
        name = p.lstrip('/')
        raw = open(join(RAWS_DIR, name), 'w')
        raw.write(f.read())
    print 'Sync folder done.'

def gen_entry(file_name):
    raw = open(join(RAWS_DIR, file_name), 'r')
    title = file_name.rstrip('.md')
    path = urllib.quote_plus(title) + '.html'
    gen = open(join(ENTRIES_DIR, path), 'wb')
    content = markdown(raw.read().decode('utf8'))
    html_content = render_template('entry.html', c={'file_content':content})
    gen.write(html_content)
    gen.close()
    raw.close()
    return dict(title=title, path=path, content=content)

def gen_home(files):
    entries = []
    for f in files:
        entries.append(dict(link=ENTRY_LINK_PATTERN % f['path'], title=f['title'], content=f['content']))
    gen = open(join(ENTRIES_DIR, 'home.html'), 'wb')
    gen.write(render_template('home.html', c={'entries':entries}))
    gen.close()

@app.route('/sync')
def sync():
    if not is_authenticated():
        return redirect('/login')

    sess = dropbox_session()
    access_token = flask_session[DROPBOX_ACCESS_TOKEN_KEY]
    sess.set_token(access_token['key'], access_token['secret'])

    c = client.DropboxClient(sess)
    if c:
        sync_folder(c)
        print 'Sync folder OK.'
        print 'Gen html now...'
        try:
            files = []
            for f in os.listdir(RAWS_DIR):
                if isfile(join(RAWS_DIR, f)):
                    files.append(gen_entry(f))
                    print 'Gen %s OK.' % f
            # gen home
            gen_home(files)
            print 'Gen home page OK.'
            return 'Done!'
        except OSError:
            return 'Woops! File operations error ...'
    else:
        print 'Can not auth to dropbox'

@app.route('/')
def home():
    return send_from_directory(ENTRIES_DIR, 'home.html')

@app.route(ENTRY_LINK_PATTERN % '<path:filename>')
def entry(filename):
    return send_from_directory(ENTRIES_DIR, filename)

@app.route('/login')
def login():
    url = login_url()
    return 'Click <a href="%s">here</a> to login with Dropbox.' % url

@app.route('/login_success')
def login_success():
    oauth_token = request.args.get('oauth_token')
    uid = request.args.get('uid')
    if not oauth_token:
        return 'oauth token error'

    # oAuth token **should** be equal to stored request token
    request_token = flask_session.get(DROPBOX_REQUEST_TOKEN_KEY)

    if not request_token or oauth_token != request_token['key']:
        return 'token not equal'

    from dropbox.rest import ErrorResponse
    try:
        dropbox_login(request_token)
    except ErrorResponse, e:
        print '=====', e
        return 'login error'
    return redirect('/')

@app.route('/logout')
def logout():
    dropbox_logout()
    return redirect('/')

@app.route('/test')
def test():
    if not is_authenticated():
        return redirect('/login')

    sess = dropbox_session()
    access_token = flask_session[DROPBOX_ACCESS_TOKEN_KEY]
    sess.set_token(access_token['key'], access_token['secret'])

    c = client.DropboxClient(sess)
    print "linked account:", c.account_info()

    return 'already logged in'


if __name__ == '__main__':
    app.config['MAKO_DIR'] = MAKO_DIR
    init_mako(app)
    app.secret_key = APP_SECRET_KEY
    app.debug = True
    app.run()
