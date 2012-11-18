#-*- coding:utf-8 -*-

from os import listdir, makedirs
from os.path import isfile, join, exists
import urllib
import re
from datetime import datetime
import pytz
from operator import itemgetter
import markdown
from werkzeug.utils import cached_property
from werkzeug.exceptions import Forbidden
from flask import request, session as flask_session
from flask.ext.mako import render_template
from dropbox import client, rest, session
from global_config import DROPBOX_APP_KEY, DROPBOX_APP_SECRET, DROPBOX_ACCESS_TYPE, \
    DROPBOX_REQUEST_TOKEN_KEY, DROPBOX_ACCESS_TOKEN_KEY, RAW_ENTRY_FILE_SUFFIX, \
    RAWS_DIR, LOCAL_ENTRIES_DIR, LOCAL_TAGS_DIR, ENTRY_LINK_PATTERN, IMAGE_LINK_PATTERN, \
    REMOTE_IMAGE_DIR, LOCAL_IMAGE_DIR, PUBLIC_DIR, TIMEZONE, DOMAIN_URL, DROPBOX_ACCOUNT_EMAIL, \
    BLOG_NAME, PAGE_POSTS_COUNT


class DropboxSync(object):

    def __init__(self, client, content_path=RAWS_DIR,\
                 output_path=LOCAL_ENTRIES_DIR, \
                 output_tags_path=LOCAL_TAGS_DIR):
        self.client = client
        self.content_path = content_path
        self.output_path = output_path
        self.output_tags_path = output_tags_path

    def process_remote_file(self, path):
        print 'Downloading %s' % path
        suffix = path.split('.')[-1]
        if path.endswith(RAW_ENTRY_FILE_SUFFIX):
            dir_path = self.content_path
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
        if not meta['is_dir'] and path.endswith(RAW_ENTRY_FILE_SUFFIX):
            first = self.client.revisions(path)[-1]
            # modified date format: 'Thu, 25 Aug 2011 00:03:15 +0000'
            modified = datetime.strptime(first['modified'][:-6], '%a, %d %b %Y %H:%M:%S')
            return format_time_str(modified.replace(tzinfo=pytz.UTC).astimezone(pytz.timezone(TIMEZONE)))

    def get_file_info(self, file_name):
        name = file_name.rstrip('.md')
        raw = open(join(self.content_path, file_name), 'r')
        md = markdown.Markdown(extensions=['meta'])
        content = md.convert(raw.read().decode('utf8'))
        meta = md.Meta
        raw.close()
        is_public = meta.get('public')
        if is_public and is_public[0].lower() == 'no':
            return False
        is_comment = meta.get('comment')
        is_comment = is_comment and is_comment[0].lower() == 'yes'
        tags = meta.get('keywords', [])
        title = meta.get('title', [''])[0] or name
        created_at = meta.get('date', [''])[0] or self.get_file_created_at('/%s' % file_name)
        path = urllib.quote_plus(name) + '.html'
        return dict(orig_file=file_name, title=title, created_at=created_at,
                    is_comment=is_comment, tags=tags, file_name=name,
                    path=path, link=ENTRY_LINK_PATTERN % path, content=content)

    def gen_entry_page(self, file_info, prev_file=None, next_file=None):
        is_public = file_info.get('public')
        if is_public and is_public[0].lower() == 'no':
            return False
        name = file_info.get('file_name')
        title = file_info.get('title')
        content = file_info.get('content')
        tags = file_info.get('tags')
        created_at = file_info.get('created_at')
        is_comment = file_info.get('is_comment')
        if prev_file:
            prev_title = prev_file.get('title')
            prev_link = prev_file.get('link')
        if next_file:
            next_title = next_file.get('title')
            next_link = next_file.get('link')
        l = locals()
        l.pop('self')
        html_content = render_template('entry.html', **l)
        path = urllib.quote_plus(name) + '.html'
        if not exists(self.output_path):
            makedirs(self.output_path)
        gen = open(join(self.output_path, path), 'wb')
        gen.write(html_content)
        gen.close()
        print 'Gen %s OK.' % name

    def gen_home_page(self, files_info):

        def chunks(l, n):
            for i in xrange(0, len(l), n):
                yield (i+1)/n + 1, l[i:i+n]

        pages = list(chunks(files_info, PAGE_POSTS_COUNT))
        prev_page_id = 0
        next_page_id = 0
        for i, entries in pages:
            next_page_id = i - 1 if i - 1 >= 0 else 0
            prev_page_id = i + 1 if i + 1 <= len(pages) else 0
            gen = open(join(PUBLIC_DIR, 'home-%s.html' % i), 'wb')
            l = locals()
            l.pop('self')
            gen.write(render_template('home.html', **l))
            gen.close()
        print 'Gen home page OK.'

    def gen_tag_page(self, files_info):
        tags = {}
        for entry in files_info:
            for tag in entry['tags']:
                tags.setdefault(tag, [])
                tags[tag].append(entry)
        if not exists(self.output_tags_path):
            makedirs(self.output_tags_path)
        for tag in tags:
            entries = tags[tag]
            gen = open(join(self.output_tags_path, '%s.html' % tag), 'wb')
            l = locals()
            l.pop('self')
            gen.write(render_template('tag.html', **l))
            gen.close()

    def gen_pages(self):
        print 'Gen html file now...'
        try:
            dropbox_files = [f['path'].split('/')[-1] for f in self.client.metadata('/')['contents'] if f['is_dir'] == False]
            fs = [f for f in listdir(self.content_path) if isfile(join(self.content_path, f))\
                  and f.endswith(RAW_ENTRY_FILE_SUFFIX) and f in dropbox_files]
            files_info = []
            for f in fs:
                info = self.get_file_info(f)
                if info:
                    files_info.append(info)
            files_info = sorted(files_info, key=itemgetter('created_at'), reverse=True)
            for i, file_info in enumerate(files_info):
                prev = files_info[i+1] if i < len(files_info) - 1 else None
                next = files_info[i-1] if i > 0 else None
                self.gen_entry_page(file_info, prev_file=prev, next_file=next)
            self.gen_home_page(files_info)
            self.gen_tag_page(files_info)
            self.gen_rss(files_info)
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
            # Dropbox account is incorrect, can not login
            self.logout()
            raise Forbidden

    def logout(self):
        if DROPBOX_ACCESS_TOKEN_KEY in flask_session:
            del flask_session[DROPBOX_ACCESS_TOKEN_KEY]

    @property
    def client(self):
        access_token = flask_session[DROPBOX_ACCESS_TOKEN_KEY]
        self.session.set_token(access_token['key'], access_token['secret'])
        return client.DropboxClient(self.session)
