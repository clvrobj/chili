#-*- coding:utf-8 -*-
import os
from os.path import isfile, join
import urllib
from markdown import markdown
from flask import Flask, request, redirect, url_for, send_from_directory
from flask import session as flask_session
from flaskext.mako import init_mako, render_template
from dropbox.rest import ErrorResponse
from utils import Dropbox
from config import APP_SECRET_KEY, RAWS_DIR, ENTRIES_DIR, MAKO_DIR, ENTRY_LINK_PATTERN

app = Flask(__name__)
app.config['MAKO_DIR'] = MAKO_DIR
init_mako(app)
app.secret_key = APP_SECRET_KEY
app.debug = True
dropbox = Dropbox()


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
    html_content = render_template('entry.html', c=locals())
    gen.write(html_content)
    gen.close()
    raw.close()
    return dict(title=title, path=path, content=content)

def gen_home(files_info):
    entries = []
    for f in files_info:
        entries.append(dict(link=ENTRY_LINK_PATTERN % f['path'], title=f['title'], content=f['content']))
    gen = open(join(ENTRIES_DIR, 'home.html'), 'wb')
    gen.write(render_template('home.html', c={'entries':entries}))
    gen.close()

def gen_files():
    print 'Gen html file now...'
    try:
        files_info = []
        for f in os.listdir(RAWS_DIR):
            if isfile(join(RAWS_DIR, f)) and f.endswith('.md'):
                files_info.append(gen_entry(f))
                print 'Gen %s OK.' % f
        # gen home
        gen_home(files_info)
        print 'Gen home page OK.'
        return 'Done!'
    except OSError:
        return 'Woops! File operations error ...'

@app.route('/sync')
def sync():
    if not dropbox.is_authenticated:
        return redirect('/login')

    client = dropbox.client
    if client:
        sync_folder(client)
        print 'Sync folder OK.'
        return gen_files()
    else:
        print 'Can not auth to dropbox'


@app.route('/regen')
def regen_files():
    return gen_files()

@app.route('/ops')
def operations():
    return render_template('operations.html')

@app.route('/')
def home():
    return send_from_directory(ENTRIES_DIR, 'home.html')

@app.route(ENTRY_LINK_PATTERN % '<path:filename>')
def entry(filename):
    return send_from_directory(ENTRIES_DIR, filename)

@app.route('/login')
def login():
    url = dropbox.login_url
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

    try:
        dropbox.login(request_token)
    except ErrorResponse, e:
        print '=====', e
        return 'login error'
    return redirect('/')

@app.route('/logout')
def logout():
    dropbox.logout()
    return redirect('/')

@app.route('/test')
def test():
    if not dropbox.is_authenticated:
        return redirect('/login')

    c = dropbox.client
    print "linked account:", c.account_info()

    return 'already logged in'


if __name__ == '__main__':
    app.run()
