# -*- coding: utf-8 -*-

import os
import sys
from os.path import join
import unittest

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(TEST_DIR)
sys.path.insert(0, ROOT_DIR)

from flask import Flask
from flask.ext.mako import MakoTemplates
from config import MAKO_DIR
from utils import DropboxSync


class DummyDropboxClient(object):

    def revisions(self, path):
        return [{'modified':'Wed, 20 Jul 2011 22:04:50 +0000'}]

    def metadata(self, path):
        if path == '/':
            return {'is_dir':True,
                    'contents':[{'path':'/test-1.md', 'is_dir':False},
                                {'path':'/test-2.md', 'is_dir':False},
                                {'path':'/test-3.md', 'is_dir':False}]}
        return {'is_dir':False}

class ChiliTest(unittest.TestCase):

    def setUp(self):
        app = Flask(__name__)
        app.debug = True
        app.config['MAKO_DIR'] = MAKO_DIR
        mako = MakoTemplates(app)
        self.app = app
        self.mako = mako
        cur_dir = os.path.dirname(os.path.realpath(__file__))
        self.content_path = join(cur_dir, 'content')
        self.output_path = join(cur_dir, 'output')
        self.output_tags_path = join(self.output_path, 'tags')

        @app.before_request
        def setup_context():
            pass

        @app.route('/regen')
        def regen():
            client = DummyDropboxClient()
            DropboxSync(client, self.content_path,
                        self.output_path, self.output_tags_path).gen_pages()
            return 'OK'

    def test_gen_posts(self):
        c = self.app.test_client()
        c.get('/regen')
        content_files = os.listdir(self.content_path)
        output_files = [f for f in os.listdir(self.output_path)
                        if os.path.isfile(os.path.join(self.output_path,
                                                       f))]
        assert len(content_files) == len(output_files)

    def tearDown(self):
        for f in os.listdir(self.output_tags_path):
            os.remove(os.path.join(self.output_tags_path, f))
        os.rmdir(self.output_tags_path)
        for f in os.listdir(self.output_path):
            os.remove(os.path.join(self.output_path, f))

if __name__ == '__main__':
    unittest.main()
