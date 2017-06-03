# -*- coding: utf-8 -*-u

from __future__ import absolute_import
import os
import sys
import unittest
from os.path import join

from flask import Flask
from flask.ext.mako import MakoTemplates

TEST_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(TEST_DIR)
sys.path.insert(0, ROOT_DIR)
from global_config import MAKO_DIR
from utils import DropboxSync


class DummyDropboxClient(object):

    def revisions(self, path):
        return [{'modified':'Wed, 20 Jul 2012 22:04:50 +0000'}]

    def metadata(self, path):
        if path == '/':
            ret = {'is_dir':True}
            content_files = ['test-1.md', 'test-2.md', 'test-3.md']
            ret['contents'] = [{'path':'/' + f, 'is_dir':False} for f in content_files]
            return ret
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
        self.output_entries_path = join(self.output_path, 'entries')
        self.output_tags_path = join(self.output_path, 'tags')

        @app.route('/regen')
        def regen():
            client = DummyDropboxClient()
            DropboxSync(client, self.content_path,
                        self.output_path, self.output_entries_path,
                        self.output_tags_path).gen_pages()
            return 'OK'

    def test_gen_posts(self):
        c = self.app.test_client()
        c.get('/regen')
        content_files = os.listdir(self.content_path)
        output_files = [f for f in os.listdir(self.output_path)
                        if os.path.isfile(os.path.join(self.output_path,
                                                       f))]
        assert len(content_files) == len(output_files)

        for f in content_files:
            output_file = f.replace('.md', '.html')
            assert True == os.path.exists(join(self.output_entries_path, output_file))

    def tearDown(self):
        if os.path.exists(self.output_path):
            for f in os.listdir(self.output_path):
                f = os.path.join(self.output_path, f)
                if os.path.isdir(f):
                    for ff in os.listdir(f):
                        os.remove(os.path.join(f, ff))
                if os.path.isfile(f):
                    os.remove(f)

if __name__ == '__main__':
    unittest.main()
