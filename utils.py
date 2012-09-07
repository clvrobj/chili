#-*- coding:utf-8 -*-
from os import listdir, makedirs
from os.path import isfile, join, exists
import urllib
import re
from datetime import datetime
from dateutil import parser
from pytz import timezone
from operator import itemgetter
import markdown
from werkzeug.utils import cached_property
from flask import request, session as flask_session
# from flaskext.mako import render_template
from flask.ext.mako import render_template
from dropbox import client, rest, session
from config import DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_ACCESS_TYPE, \
    DROPBOX_REQUEST_TOKEN_KEY, DROPBOX_ACCESS_TOKEN_KEY, RAW_ENTRY_FILE_FORMAT, \
    RAWS_DIR, LOCAL_ENTRIES_DIR, LOCAL_TAGS_DIR, ENTRY_LINK_PATTERN, IMAGE_LINK_PATTERN, \
    REMOTE_IMAGE_DIR, LOCAL_IMAGE_DIR, PUBLIC_DIR, TIMEZONE, DOMAIN_URL, DROPBOX_ACCOUNT_EMAIL, \
    BLOG_NAME


class DropboxSync(object):
    
    def __init__(self, client):
        self.client = client

    def process_remote_file(self, path):
        print 'Downloading %s' % path
        suffix = path.split('.')[-1]
        if suffix == RAW_ENTRY_FILE_FORMAT:
            dir_path = RAWS_DIR
        elif suffix == 'png' or suffix == 'jpg' or suffix == 'jpeg' or suffix == 'gif':
            dir_path = LOCAL_IMAGE_DIR
        else:
            return
        name = path.split('/')[-1]
        if not exists(dir_path):
            makedirs(dir_path)
        target = join(dir_path, name)
        if not isfile(target) or len(self.client.revisions(path)) > 1:
            f = self.client.get_file(path)
            raw = open(target, 'w').write(f.read())
            return
        # exists and no history
        print 'Already downloaded'
        return

    def process_remote_dir(self, path):
        print 'Processing remote dir', path
        if path != REMOTE_IMAGE_DIR:
            return
        folder_meta = self.client.metadata(path)
        for f in folder_meta['contents']:
            self.process_remote_file(f['path'])

    def sync_folder(self):
        """
        download all files in the app folder into raws folder
        """
        folder_meta = self.client.metadata('/')
        for f in folder_meta['contents']:
            path = f['path']
            if f['is_dir']:
                self.process_remote_dir(path)
            else:
                self.process_remote_file(path)
        print 'Sync folder done.'

    def get_file_created_at(self, path):

        def format_time_str(time):
            time = time or datetime.now()
            return time.strftime('%Y-%m-%d %H:%M:%S')

        meta = self.client.metadata(path)
        if not meta['is_dir'] and path.split('.')[-1] == RAW_ENTRY_FILE_FORMAT:
            first = self.client.revisions(path)[-1]
            return format_time_str(parser.parse(first['modified']).astimezone(timezone(TIMEZONE)))

    def gen_entry_page(self, file_name):
        name = file_name.rstrip('.md')
        raw = open(join(RAWS_DIR, file_name), 'r')
        md = markdown.Markdown(extensions=['meta'])
        content = md.convert(raw.read().decode('utf8'))
        meta = md.Meta
        is_public = meta.get('public')
        if is_public and is_public[0].lower() == 'no':
            return False
        is_comment = meta.get('comment')
        is_comment = is_comment and is_comment[0].lower() == 'yes'
        tags = meta.get('keywords', [])
        title = meta.get('title', [''])[0] or name
        created_at = meta.get('date', [''])[0] or self.get_file_created_at('/%s' % file_name)
        l = locals()
        l.pop('self')
        html_content = render_template('entry.html', **l)
        path = urllib.quote_plus(name) + '.html'
        if not exists(LOCAL_ENTRIES_DIR):
            makedirs(LOCAL_ENTRIES_DIR)
        gen = open(join(LOCAL_ENTRIES_DIR, path), 'wb')
        gen.write(html_content)
        gen.close()
        raw.close()
        return dict(orig_file=file_name, title=title, created_at=created_at,
                    is_comment=is_comment, tags=tags,
                    path=path, link=ENTRY_LINK_PATTERN % path, content=content)

    def gen_home_page(self, files_info):
        entries = []
        entries = sorted(files_info, key=itemgetter('created_at'), reverse=True)
        gen = open(join(PUBLIC_DIR, 'home.html'), 'wb')
        l = locals()
        l.pop('self')
        gen.write(render_template('home.html', **l))
        gen.close()

    def gen_tag_page(self, files_info):
        tags = {}
        for entry in files_info:
            for tag in entry['tags']:
                tags.setdefault(tag, [])
                tags[tag].append(entry)
        if not exists(LOCAL_TAGS_DIR):
            makedirs(LOCAL_TAGS_DIR)
        for tag in tags:
            entries = tags[tag]
            gen = open(join(LOCAL_TAGS_DIR, '%s.html' % tag), 'wb')
            l = locals()
            l.pop('self')
            gen.write(render_template('tag.html', **l))
            gen.close()

    def gen_files(self):
        print 'Gen html file now...'
        try:
            dropbox_files = [f['path'].split('/')[-1] for f in self.client.metadata('/')['contents'] if f['is_dir'] == False]
            files_info = []
            for f in listdir(RAWS_DIR):
                if isfile(join(RAWS_DIR, f)) and f.endswith('.md') and f in dropbox_files:
                    info = self.gen_entry_page(f)
                    if info:
                        files_info.append(info)
                        print 'Gen %s OK.' % f
            # gen home
            self.gen_home_page(files_info)
            self.gen_tag_page(files_info)
            self.gen_rss(files_info)
            print 'Gen home page OK.'
            return 'Done!'
        except OSError:
            return 'Woops! File operations error ...'

    def gen_rss(self, files_info):
        import PyRSS2Gen
        items = []
        entries = sorted(files_info, key=itemgetter('created_at'), reverse=True)
        for f in entries:
            link = DOMAIN_URL + f['link']
            # replace relative url to absolute url
            desc = re.sub(r'src="/', 'src="%s/' % DOMAIN_URL, f['content'])
            items.append(PyRSS2Gen.RSSItem(link=link, title=f['title'],
                                           description=desc,
                                           pubDate=f['created_at'],
                                           guid = PyRSS2Gen.Guid(link)))

        rss = PyRSS2Gen.RSS2(title=BLOG_NAME, link=DOMAIN_URL,
                             description='', lastBuildDate = datetime.now(),
                             items=items)
        rss.write_xml(open(join(PUBLIC_DIR, 'rss.xml'), 'w'))


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

        if DROPBOX_ACCOUNT_EMAIL != c.account_info().get('email'):
            # owner account is wrong should not login
            self.logout()

    def logout(self):
        if DROPBOX_ACCESS_TOKEN_KEY in flask_session:
            del flask_session[DROPBOX_ACCESS_TOKEN_KEY]

    @property
    def client(self):
        access_token = flask_session[DROPBOX_ACCESS_TOKEN_KEY]
        self.session.set_token(access_token['key'], access_token['secret'])
        return client.DropboxClient(self.session)
