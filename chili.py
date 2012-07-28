#-*- coding:utf-8 -*-
import os
from os.path import isfile, join
import urllib
from datetime import datetime
from dateutil import parser
from pytz import timezone
import markdown
from flask import Flask, request, redirect, url_for, send_from_directory, session as flask_session
from flaskext.mako import init_mako, render_template
from dropbox.rest import ErrorResponse
from utils import Dropbox
from config import APP_SECRET_KEY, RAW_ENTRY_FILE_FORMAT, RAWS_DIR, LOCAL_ENTRIES_DIR, MAKO_DIR, ENTRY_LINK_PATTERN, IMAGE_LINK_PATTERN, DROPBOX_REQUEST_TOKEN_KEY, REMOTE_IMAGE_DIR, LOCAL_IMAGE_DIR,  TIMEZONE

app = Flask(__name__)
app.config['MAKO_DIR'] = MAKO_DIR
init_mako(app)
app.secret_key = APP_SECRET_KEY
app.debug = True
dropbox = Dropbox()


def process_remote_file(client, path):
    print 'Downloading %s' % path
    suffix = path.split('.')[-1]
    if suffix == RAW_ENTRY_FILE_FORMAT:
        dir_path = RAWS_DIR
    elif suffix == 'png' or suffix == 'jpg' or suffix == 'jpeg' or suffix == 'gif':
        dir_path = LOCAL_IMAGE_DIR
    else:
        return
    name = path.split('/')[-1]
    target = join(dir_path, name)
    if not isfile(target) or len(client.revisions(path)) > 1:
        f = client.get_file(path)
        raw = open(target, 'w')
        raw.write(f.read())
        return
    # exists and no history
    print 'Already downloaded'
    return

def process_remote_dir(client, path):
    print 'Processing remote dir', path
    if path != REMOTE_IMAGE_DIR:
        return
    folder_meta = client.metadata(path)
    for f in folder_meta['contents']:
        process_remote_file(client, f['path'])

def sync_folder(client):
    """
    download all files in the app folder into raws folder
    """
    folder_meta = client.metadata('/')
    for f in folder_meta['contents']:
        path = f['path']
        if f['is_dir']:
            process_remote_dir(client, path)
        else:
            process_remote_file(client, path)
    print 'Sync folder done.'

def get_files_created_at(client):
    folder_meta = client.metadata('/')
    files_created_at = {}
    for f in folder_meta['contents']:
        p = f['path']
        if f['is_dir'] == False and p.split('.')[-1] == RAW_ENTRY_FILE_FORMAT:
            name = p.split('/')[-1]
            first = client.revisions(p)[-1]
            files_created_at.setdefault(name, parser.parse(first['modified']).astimezone(timezone(TIMEZONE)))
    return files_created_at

def format_time_str(time):
    time = time or datetime.now()
    time = time.strftime('%Y-%m-%d %H:%M:%S')
    return time

def gen_entry(file_name, created_at):
    name = file_name.rstrip('.md')
    raw = open(join(RAWS_DIR, file_name), 'r')
    path = urllib.quote_plus(name) + '.html'
    gen = open(join(LOCAL_ENTRIES_DIR, path), 'wb')
    md = markdown.Markdown(extensions=['meta'])
    content = md.convert(raw.read().decode('utf8'))
    meta = md.Meta
    title = meta.get('title', [''])[0] or name
    created_at = meta.get('date', [''])[0] or format_time_str(created_at)
    html_content = render_template('entry.html', c=locals())
    gen.write(html_content)
    gen.close()
    raw.close()
    return dict(orig_file=file_name, title=title, created_at=created_at, path=path, content=content)

def gen_home_page(files_info):
    entries = []
    for f in files_info:
        entries.append(dict(link=ENTRY_LINK_PATTERN % f['path'], title=f['title'],
                            content=f['content'], created_at=f['created_at']))
    gen = open(join(LOCAL_ENTRIES_DIR, 'home.html'), 'wb')
    gen.write(render_template('home.html', c=locals()))
    gen.close()

def gen_files(files_created_at):
    print 'Gen html file now...'
    try:
        files_info = []
        for f in os.listdir(RAWS_DIR):
            if isfile(join(RAWS_DIR, f)) and f.endswith('.md'):
                if f in files_created_at:
                    created_at = files_created_at[f]
                    files_info.append(gen_entry(f, created_at))
                    print 'Gen %s OK.' % f
        # gen home
        gen_home_page(files_info)
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
        files_created_at = get_files_created_at(client)
        return gen_files(files_created_at)
    else:
        print 'Can not auth to dropbox'


@app.route('/regen')
def regen_files():
    if not dropbox.is_authenticated:
        return redirect('/login')

    client = dropbox.client
    if client:
        files_created_at = get_files_created_at(client)
        gen_files(files_created_at)
        return redirect('/')
    else:
        print 'Can not auth to dropbox'

@app.route('/ops')
def operations():
    return render_template('operations.html')

@app.route('/')
def home():
    return send_from_directory(LOCAL_ENTRIES_DIR, 'home.html')

@app.route(ENTRY_LINK_PATTERN % '<path:filename>')
def entry(filename):
    return send_from_directory(LOCAL_ENTRIES_DIR, filename)

@app.route(IMAGE_LINK_PATTERN % '<path:filename>')
def image(filename):
    return send_from_directory(LOCAL_IMAGE_DIR, filename)

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
