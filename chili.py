#-*- coding:utf-8 -*-
from flask import Flask, request, redirect, url_for, send_from_directory, session as flask_session
# from flaskext.mako import init_mako, render_template
from flask.ext.mako import MakoTemplates, render_template
from dropbox.rest import ErrorResponse
from utils import Dropbox, DropboxSync
from config import APP_SECRET_KEY, MAKO_DIR, DROPBOX_REQUEST_TOKEN_KEY, \
    ENTRY_LINK_PATTERN, IMAGE_LINK_PATTERN, LOCAL_ENTRIES_DIR, LOCAL_IMAGE_DIR, PUBLIC_DIR

app = Flask(__name__)
app.config['MAKO_DIR'] = MAKO_DIR
# init_mako(app)
mako = MakoTemplates(app)
mako.init_app(app)
app.secret_key = APP_SECRET_KEY
app.debug = True
dropbox = Dropbox()


@app.route('/sync')
def sync():
    if not dropbox.is_authenticated:
        return redirect('/login')

    client = dropbox.client
    if client:
        sync = DropboxSync(client)
        sync.sync_folder()
        return sync.gen_files()
    else:
        print 'Can not auth to dropbox'

@app.route('/regen')
def regen_files():
    if not dropbox.is_authenticated:
        return redirect('/login')

    client = dropbox.client
    if client:
        DropboxSync(client).gen_files()
        return redirect('/')
    else:
        print 'Can not auth to dropbox'

@app.route('/ops')
def operations():
    return render_template('operations.html')

@app.route('/')
def home():
    return send_from_directory(PUBLIC_DIR, 'home.html')

@app.route(ENTRY_LINK_PATTERN % '<path:filename>')
def entry(filename):
    return send_from_directory(LOCAL_ENTRIES_DIR, filename)

@app.route(IMAGE_LINK_PATTERN % '<path:filename>')
def image(filename):
    return send_from_directory(LOCAL_IMAGE_DIR, filename)

@app.route('/<path:filename>')
def public(filename):
    return send_from_directory('public', filename)

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


if __name__ == '__main__':
    app.run()
